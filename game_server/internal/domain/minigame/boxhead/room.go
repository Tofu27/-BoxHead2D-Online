package boxhead

import (
	"encoding/json"
	"log"
	"sync"
	"time"
)

// CommandEnvelope 命令信封，封装命令类型和负载
type CommandEnvelope struct {
	Type    string
	Payload interface{}
}

// Room 房间聚合根，采用单goroutine事件循环（Actor模型）
// 所有对玩家状态的修改、广播、定时任务都在此goroutine中串行执行，
// 因此完全不需要锁保护players map。
type Room struct {
	id      string                  // 房间唯一标识
	players map[string]*PlayerState // 所有玩家，key=UUID

	cmdCh  chan CommandEnvelope // 命令通道：接收来自应用层的操作命令
	stopCh chan struct{}        // 停止信号：关闭该channel即可优雅退出主循环
	ticker *time.Ticker         // 高频定时器：驱动游戏逻辑和广播（通常50ms一次）

	// 僵尸玩家清理参数
	cleanInterval time.Duration // 清理间隔（默认30s）
	maxCreateAge  time.Duration // 最长允许未连接时间（默认2min）
}

// 命令类型常量
const (
	CmdJoin       = "join"        // 玩家加入房间
	CmdLeave      = "leave"       // 玩家离开房间
	CmdUpdate     = "update"      // 玩家状态更新（位置、动作等）
	CmdBindSendCh = "bind_sendch" // 绑定玩家的发送通道（WebSocket连接建立后）
)

// ---------- 对象池 ----------
// 用于存储快照切片的sync.Pool，大幅减少高频广播带来的内存分配和GC压力

// 全量快照池：存放 []*PlayerState
var fullSnapshotPool = sync.Pool{
	New: func() interface{} {
		return make([]*PlayerState, 0, 64)
	},
}

// 增量脏玩家池：存放 []*PlayerState
var dirtyPlayerPool = sync.Pool{
	New: func() interface{} {
		return make([]*PlayerState, 0, 64)
	},
}

// NewRoom 创建一个新的房间实例
func NewRoom(id string) *Room {
	return &Room{
		id:            id,
		players:       make(map[string]*PlayerState),
		cmdCh:         make(chan CommandEnvelope, 1024), // 带缓冲，避免阻塞发送者
		stopCh:        make(chan struct{}),
		cleanInterval: 30 * time.Second,
		maxCreateAge:  2 * time.Minute,
	}
}

// SendCommand 向房间发送命令（线程安全，供外部goroutine调用）
func (r *Room) SendCommand(cmd CommandEnvelope) {
	r.cmdCh <- cmd
}

// Run 启动房间主循环（必须在独立的goroutine中运行）
// 这是一个经典的Actor事件循环，处理所有命令、定时广播和清理任务。
func (r *Room) Run() {
	// 初始化主逻辑定时器（20Hz = 50ms一次）
	r.ticker = time.NewTicker(50 * time.Millisecond)
	defer r.ticker.Stop()

	// 僵尸清理定时器
	cleanTicker := time.NewTicker(r.cleanInterval)
	defer cleanTicker.Stop()

	for {
		select {
		case cmd := <-r.cmdCh:
			// 1. 处理外部命令（玩家创建、离开、状态更新、绑定通道）
			r.handleCommand(cmd)

		case <-r.ticker.C:
			// 2. 每帧广播所有玩家的完整状态（game_state）
			r.broadcastStateDiff() // 每帧只发送脏数据（增量）

		case <-cleanTicker.C:
			// 3. 定期清理长时间未连接的僵尸玩家
			r.cleanZombies()

		case <-r.stopCh:
			// 4. 收到停止信号，退出循环
			log.Printf("[房间:%s] 主循环已退出", r.id)
			return
		}
	}
}

// Stop 安全地停止房间（会等到当前帧处理完才退出）
func (r *Room) Stop() {
	close(r.stopCh)
}

// handleCommand 命令分发处理（所有玩家状态修改都在此方法内完成，保证线程安全）
func (r *Room) handleCommand(cmd CommandEnvelope) {
	switch cmd.Type {
	case CmdJoin:
		// 玩家加入：从Payload取PlayerState，存入players map
		player := cmd.Payload.(*PlayerState)
		log.Printf("[Room:%s] 📥 玩家加入: UUID=%s, Name=%s", r.id, player.UUID, player.Name)
		r.players[player.UUID] = player
	case CmdLeave:
		// 玩家离开：从map删除
		uuid := cmd.Payload.(string)
		if p, ok := r.players[uuid]; ok {
			delete(r.players, uuid)
			log.Printf("[Room:%s] 玩家离开: %s", r.id, p.Name)
			r.broadcastPlayerLeave(uuid) // 广播离开消息
		}
	case CmdUpdate:
		// 玩家状态更新（移动、行走、攻击等）
		data := cmd.Payload.(map[string]interface{})
		uuid := data["uuid"].(string)
		p, ok := r.players[uuid]
		if !ok {
			return
		}

		// 只更新有变化的字段，并设置脏标记
		changed := false
		if x, ok := data["x"].(float64); ok && p.PlayerPos.X != x {
			p.PlayerPos.X = x
			changed = true
		}
		if y, ok := data["y"].(float64); ok && p.PlayerPos.Y != y {
			p.PlayerPos.Y = y
			changed = true
		}
		if walking, ok := data["is_walking"].(bool); ok && p.IsWalking != walking {
			p.IsWalking = walking
			changed = true
		}
		if attack, ok := data["is_attack"].(bool); ok && p.IsAttack != attack {
			p.IsAttack = attack
			changed = true
		}
		if mp, ok := data["mouse_pos"].(map[string]interface{}); ok {
			var pos Position
			if mx, ok := mp["x"].(float64); ok {
				pos.X = mx
			}
			if my, ok := mp["y"].(float64); ok {
				pos.Y = my
			}
			if p.MousePos != pos {
				p.MousePos = pos
				changed = true
			}
		}

		if changed {
			p.SetDirty()
		}

	case CmdBindSendCh:
		// 将WebSocket的连接发送通道绑定给玩家
		payload := cmd.Payload.(map[string]interface{})
		uuid := payload["uuid"].(string)
		ch := payload["send_ch"].(chan<- []byte)
		if p, ok := r.players[uuid]; ok {
			p.SetSendCh(ch)
			p.Connected = true
			log.Printf("[Room:%s] ✅ 玩家 %s 已绑定发送通道", r.id, uuid)
			r.sendFullSnapshotToPlayer(p)
		} else {
			log.Printf("[Room:%s] ❌ 绑定失败：玩家 %s 不存在", r.id, uuid)
		}
	}

}

// 广播完整的游戏状态（原版boxhead的game_state消息格式）
// 每50ms执行一次，将所有已连接玩家的数据打包发送给每个客户端，
// 客户端依靠这个数组来渲染所有其他玩家。

// ========== 全量快照：只发给单个新玩家 ==========
func (r *Room) sendFullSnapshotToPlayer(target *PlayerState) {
	if target.sendCh == nil {
		return
	}
	snapshots := fullSnapshotPool.Get().([]*PlayerState)
	snapshots = snapshots[:0]
	defer fullSnapshotPool.Put(snapshots)

	// 收集所有已连接玩家（可选：排除目标自己，取决于客户端逻辑）
	for _, p := range r.players {
		if p.Connected {
			snapshots = append(snapshots, p)
		}
	}

	msg := map[string]interface{}{
		"type": "game_state",
		"snapshots": map[string]interface{}{
			"Players": snapshots,
		},
	}

	sent := 0
	data, _ := json.Marshal(msg)
	select {
	case target.sendCh <- data:
		sent++
	default:
	}
	log.Printf("[Room:%s] 📡 全量广播 %d 个实体，发送给 %d 人, ==> %v", r.id, len(snapshots), sent, data)

}

// ========== 增量广播：每 tick 发出 ==========
func (r *Room) broadcastStateDiff() {
	dirtyPlayers := dirtyPlayerPool.Get().([]*PlayerState)
	dirtyPlayers = dirtyPlayers[:0]
	defer dirtyPlayerPool.Put(dirtyPlayers)

	for _, p := range r.players {
		if p.Connected && p.IsDirty() {
			dirtyPlayers = append(dirtyPlayers, p)
		}
	}
	if len(dirtyPlayers) == 0 {
		return
	}

	msg := map[string]interface{}{
		"type": "game_state_diff",
		"snapshots": map[string]interface{}{
			"Players": dirtyPlayers,
		},
	}
	data, _ := json.Marshal(msg)

	// 发给所有已连接玩家
	sent := 0
	for _, p := range r.players {
		if p.Connected && p.sendCh != nil {
			select {
			case p.sendCh <- data:
				sent++
			default:
			}
		}
	}

	log.Printf("[Room:%s] 📡 增量广播 %d 个变化实体，发送给 %d 人", r.id, len(dirtyPlayers), sent)

	// 清除脏标记
	for _, p := range dirtyPlayers {
		p.ClearDirty()
	}
}

func (r *Room) broadcastPlayerLeave(leavingUUID string) {
	msg := map[string]interface{}{
		"type": "player_leave",
		"uuid": leavingUUID,
	}
	data, _ := json.Marshal(msg)

	for _, p := range r.players {
		if p.Connected && p.sendCh != nil {
			// select {
			// case p.sendCh <- data:
			// default:
			// }
			// 阻塞发送，保证必达（房间主循环会短暂停在此处）
			p.sendCh <- data
			log.Printf("[Room:%s] 📦 已发送离开消息给 %s(%s)", r.id, p.Name, p.UUID)
		}
	}
}

// cleanZombies 清理玩家：创建后超过maxCreateAge仍未建立WebSocket连接的视为僵尸，直接删除
func (r *Room) cleanZombies() {
	now := time.Now()
	for uuid, p := range r.players {
		if !p.Connected && now.Sub(p.CreatedAt) > r.maxCreateAge {
			delete(r.players, uuid)
			log.Printf("[Room:%s] 🧟 清理僵尸玩家: %s (%s)", r.id, p.Name, uuid)
		}
	}
}

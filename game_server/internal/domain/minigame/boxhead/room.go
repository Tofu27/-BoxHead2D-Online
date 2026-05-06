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
	width    float64
	height   float64
	id       string                  // 房间唯一标识
	players  map[string]*PlayerState // 所有玩家，key=UUID
	monsters map[string]*Monster     // 所有怪物，key=ID

	cmdCh  chan CommandEnvelope // 命令通道：接收来自应用层的操作命令
	stopCh chan struct{}        // 停止信号：关闭该channel即可优雅退出主循环
	ticker *time.Ticker         // 高频定时器：驱动游戏逻辑和广播（通常50ms一次）

	// 僵尸玩家清理参数
	cleanInterval time.Duration // 清理间隔（默认30s）
	maxCreateAge  time.Duration // 最长允许未连接时间（默认2min）

	lastLogTime time.Time
	logInterval time.Duration
}

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
	r := &Room{
		id:            id,
		players:       make(map[string]*PlayerState),
		monsters:      make(map[string]*Monster),
		cmdCh:         make(chan CommandEnvelope, 1024), // 带缓冲，避免阻塞发送者
		stopCh:        make(chan struct{}),
		cleanInterval: 30 * time.Second,
		maxCreateAge:  2 * time.Minute,
		logInterval:   2 * time.Second,
		lastLogTime:   time.Now(),
	}

	r.initTestMonster() // 初始化测试怪物

	return r
}

func (r *Room) initTestMonster() {
	r.monsters["monster1"] = &Monster{
		ID:            "monster1",
		CharacterType: 0,
		MonsterPos:    Position{X: 1050, Y: 600},
		HP:            100,
		Speed:         4,

		Width:  20,
		Height: 30,
		Dirty:  true,
	}
}

func (r *Room) updateMonsters() {
	var targetPlayer *PlayerState
	for _, p := range r.players {
		if p.Connected {
			targetPlayer = p
			break
		}
	}
	if targetPlayer == nil {
		return
	}

	for _, m := range r.monsters {
		m.Update(targetPlayer.PlayerPos.X, targetPlayer.PlayerPos.Y, r.width, r.height)
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
		// case cmd := <-r.cmdCh:
		// 	// 1. 处理外部命令（玩家创建、离开、状态更新、绑定通道）
		// 	r.handleCommand(cmd)

		// case <-r.ticker.C:
		// 	// 2. 每帧广播所有玩家的完整状态（game_state）
		// 	r.updateMonsters()
		// 	r.broadcastStateDiff() // 每帧只发送脏数据（增量）, 重置脏位

		case <-r.ticker.C:
			// 先排空所有已在 cmdCh 中等待的命令，保证状态最新
			for {
				select {
				case cmd := <-r.cmdCh:
					r.handleCommand(cmd)
				default:
					goto doneDrain
				}
			}
		doneDrain:
			r.updateMonsters()
			r.broadcastStateDiff()

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
	case CmdCreatePlayer:
		player := cmd.Payload.(*PlayerState)
		r.players[player.UUID] = player
		log.Printf("[Room:%s] 📥 创建玩家: UUID=%s, Name=%s", r.id, player.UUID, player.Name)

	case CmdJoin:
		data := cmd.Payload.(map[string]interface{})

		// 1. 从 player 对象中取出 uuid，并更新已有玩家信息
		if playerData, ok := data["player"].(map[string]interface{}); ok {
			uuid, _ := playerData["uuid"].(string)
			if p, ok := r.players[uuid]; ok {
				if name, ok := playerData["name"].(string); ok && p.Name != name {
					p.Name = name
					p.SetDirty()
				}
				if ct, ok := playerData["char_type"].(string); ok && p.CharacterType != ct {
					p.CharacterType = ct
					p.SetDirty()
				}
			}
		}

		// 2. 设置房间尺寸
		if roomData, ok := data["room"].(map[string]interface{}); ok {
			if w, ok := roomData["width"].(float64); ok {
				r.width = w
			}
			if h, ok := roomData["height"].(float64); ok {
				r.height = h
			}
		}

		log.Printf("[Room:%s] 💬 玩家 WebSocket 加入，房间尺寸=%.0f x %.0f", r.id, r.width, r.height)

	case CmdLeave:
		// 玩家离开：从map删除
		uuid := cmd.Payload.(string)
		if p, ok := r.players[uuid]; ok {
			delete(r.players, uuid)
			r.broadcastPlayerLeave(uuid) // 广播离开消息
			log.Printf("[Room:%s] 玩家离开: %s", r.id, p.Name)
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

		if char_type, ok := data["char_type"].(string); ok {
			p.CharacterType = char_type
			changed = true
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
	PlayerSnapshots := fullSnapshotPool.Get().([]*PlayerState)
	PlayerSnapshots = PlayerSnapshots[:0]
	defer fullSnapshotPool.Put(PlayerSnapshots)

	// 收集所有已连接玩家（可选：排除目标自己，取决于客户端逻辑）
	for _, p := range r.players {
		if p.Connected {
			PlayerSnapshots = append(PlayerSnapshots, p)
		}
	}

	MonsterSnapshots := make([]map[string]interface{}, 0, len(r.monsters))
	for _, m := range r.monsters {
		MonsterSnapshots = append(MonsterSnapshots, map[string]interface{}{
			"id":         m.ID,
			"char_type":  m.CharacterType,
			"x":          m.MonsterPos.X,
			"y":          m.MonsterPos.Y,
			"hp":         m.HP,
			"width":      m.Width,
			"height":     m.Height,
			"is_walking": m.IsWalking,
		})
	}

	msg := map[string]interface{}{
		"type": "game_state",
		"snapshots": map[string]interface{}{
			"Players":  PlayerSnapshots,
			"Monsters": MonsterSnapshots,
		},
	}

	sent := 0
	data, _ := json.Marshal(msg)
	select {
	case target.sendCh <- data:
		sent++
	default:
	}

	if time.Since(r.lastLogTime) >= r.logInterval {
		log.Printf("[Room:%s] 发送全量快照给 %s (玩家:%d 怪物:%d)", r.id, target.Name, len(PlayerSnapshots), len(MonsterSnapshots))
		r.lastLogTime = time.Now()
	}
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

	// 收集脏怪物（改为 *Monster 切片）
	var dirtyMonsters []*Monster
	for _, m := range r.monsters {
		if m.Dirty {
			dirtyMonsters = append(dirtyMonsters, m)
		}
	}

	if len(dirtyPlayers) == 0 && len(dirtyMonsters) == 0 {
		return
	}

	// 构建消息用的怪物列表
	monstersForMsg := make([]map[string]interface{}, len(dirtyMonsters))
	for i, m := range dirtyMonsters {
		monstersForMsg[i] = map[string]interface{}{
			"id":         m.ID,
			"char_type":  m.CharacterType,
			"x":          m.MonsterPos.X,
			"y":          m.MonsterPos.Y,
			"hp":         m.HP,
			"is_walking": m.IsWalking,
		}
	}

	msg := map[string]interface{}{
		"type": "game_state_diff",
		"snapshots": map[string]interface{}{
			"Players":  dirtyPlayers,
			"Monsters": monstersForMsg,
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

	if time.Since(r.lastLogTime) >= r.logInterval {
		log.Printf("[Room:%s] 发送增量快照给 %s ==> %s", r.id, string(data))
		r.lastLogTime = time.Now()
	}

	// 清除脏标记
	for _, p := range dirtyPlayers {
		p.ClearDirty()
	}

	// 清除怪物脏标记
	for _, m := range dirtyMonsters {
		m.Dirty = false
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
			select {
			case p.sendCh <- data:
			default:
			}
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

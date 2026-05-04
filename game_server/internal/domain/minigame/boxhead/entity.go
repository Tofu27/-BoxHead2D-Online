package boxhead

import "time"

// Position 坐标值对象
type Position struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// PlayerState 玩家在游戏中的完整状态（纯数据，不包含网络连接）
// 所有字段只能由 Room 主循环修改，外部只能通过命令间接修改
type PlayerState struct {
	UUID          string    `json:"uuid"`
	Name          string    `json:"name"`
	CharacterType string    `json:"character_type"`
	PlayerPos     Position  `json:"player_pos"`
	IsWalking     bool      `json:"is_walking"`
	IsAttack      bool      `json:"is_attack"`
	MousePos      Position  `json:"mouse_pos"`
	CreatedAt     time.Time `json:"created_at"`
	Connected     bool      `json:"connected"`

	// 以下字段仅供内部使用，不序列化到客户端
	dirty  bool          // 脏标记：当状态发生变化时设为true，广播后清除（用于优化广播）
	sendCh chan<- []byte // 发送通道：指向对应Session的发送channel，用于推送消息给该玩家
}

// ---------- 内部工具方法（只能在Room主循环中使用） ----------

// SetDirty 标记状态已变化，需要广播
func (p *PlayerState) SetDirty() { p.dirty = true }

// ClearDirty 清除脏标记（广播完成后调用）
func (p *PlayerState) ClearDirty() { p.dirty = false }

// IsDirty 检查是否有未同步的变化
func (p *PlayerState) IsDirty() bool { return p.dirty }

// SetSendCh 设置发送通道（由Room在绑定Session时调用）
func (p *PlayerState) SetSendCh(ch chan<- []byte) { p.sendCh = ch }

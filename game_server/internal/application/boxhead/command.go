package boxhead

// 本文件仅定义命令中携带的数据结构（载荷），方便应用层使用

// CreatePlayerPayload 加入房间时传递的数据（暂未直接使用，直接传 *PlayerState 亦可）
type CreatePlayerPayload struct {
	Player interface{}
}

type JoinPayload struct {
	Player interface{}
	Room   interface{}
}

// LeavePayload 离开房间
type LeavePayload struct {
	UUID string
}

// UpdatePayload 玩家状态更新
type UpdatePayload struct {
	UUID string
	Data map[string]interface{}
}

// BindSendChPayload 绑定发送通道
type BindSendChPayload struct {
	UUID   string
	SendCh chan<- []byte
}

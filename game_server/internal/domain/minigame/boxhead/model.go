package boxhead

// Position 坐标值对象
type Position struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// 命令类型常量
const (
	CmdCreatePlayer = "create_player"
	CmdJoin         = "join"        // 玩家加入房间
	CmdLeave        = "leave"       // 玩家离开房间
	CmdUpdate       = "update"      // 玩家状态更新（位置、动作等）
	CmdBindSendCh   = "bind_sendch" // 绑定玩家的发送通道（WebSocket连接建立后）
)

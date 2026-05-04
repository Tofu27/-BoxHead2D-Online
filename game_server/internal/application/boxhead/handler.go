package boxhead

import (
	domain "game_server/internal/domain/minigame/boxhead"
)

// CommandHandler 应用层命令处理器
// 它将用户的意图转换为对Room的命令，使外部（HTTP/WS处理器）不直接操作Room内部。
type CommandHandler struct {
	room *domain.Room // 指向被操作的房间
}

// NewCommandHandler 创建命令处理器
func NewCommandHandler(room *domain.Room) *CommandHandler {
	return &CommandHandler{room: room}
}

// JoinRoom 玩家加入房间：直接传递完整的PlayerState对象
func (h *CommandHandler) JoinRoom(player *domain.PlayerState) {
	h.room.SendCommand(domain.CommandEnvelope{
		Type:    domain.CmdJoin,
		Payload: player,
	})
}

// LeaveRoom 玩家离开房间
func (h *CommandHandler) LeaveRoom(uuid string) {
	h.room.SendCommand(domain.CommandEnvelope{
		Type:    domain.CmdLeave,
		Payload: uuid,
	})
}

// UpdatePlayer 玩家状态更新（由WebSocket消息触发）
func (h *CommandHandler) UpdatePlayer(uuid string, data map[string]interface{}) {
	// 在数据里补上uuid，便于Room统一处理
	data["uuid"] = uuid
	h.room.SendCommand(domain.CommandEnvelope{
		Type:    domain.CmdUpdate,
		Payload: data,
	})
}

// BindSendCh 将Session的发送通道绑定到房间内的玩家
func (h *CommandHandler) BindSendCh(uuid string, ch chan<- []byte) {
	h.room.SendCommand(domain.CommandEnvelope{
		Type: domain.CmdBindSendCh,
		Payload: map[string]interface{}{
			"uuid":    uuid,
			"send_ch": ch,
		},
	})
}

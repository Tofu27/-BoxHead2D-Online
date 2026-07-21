package states

import (
	"fmt"
	"log"
	"server/internal/server/interfaces"
	"server/internal/server/objects"
	"server/pkg/packets"
)

type InRoom struct {
	client interfaces.ClientInterfacer
	user   *objects.User
	logger *log.Logger
}

func (c *InRoom) Name() string {
	return "InRoom"
}

func (c *InRoom) SetClient(client interfaces.ClientInterfacer) {
	c.client = client
	loggingPrefix := fmt.Sprintf("客户端 %d [%s]:", client.Id(), c.Name())
	c.logger = log.New(log.Writer(), loggingPrefix, log.LstdFlags)
}

func (c *InRoom) OnEnter() {
	c.logger.Printf("玩家 %s 进入房间", c.user.Username)

	roomManager := c.client.GetRoomManager()
	room, err := roomManager.CreateRoom(4, c.user)

	if err != nil {
		c.logger.Printf("房间已经存在")
		return
	}

}

func (c *InRoom) HandleMessage(senderId uint64, message packets.Msg) {
	c.logger.Printf("接收到来自客户端 %d 的消息：%+v", senderId, message)
}

func (c *InRoom) OnExit() {
	c.logger.Printf("玩家 %s 离开房间", c.user.Username)

}

func (c *InRoom) handleLeaveRoomRequest(_ uint64, _ *packets.Packet_LeaveRoomRequest) {

}

package states

import (
	"log"
	"server/internal/server/interfaces"
	"server/pkg/packets"
)

type Connected struct {
	client interfaces.ClientInterfacer
	logger *log.Logger
}

func (c *Connected) Name() string {
	return "Connected"
}

func (c *Connected) SetClient(client interfaces.ClientInterfacer) {
	c.client = client
}

func (c *Connected) OnEnter() {
	c.client.SendToSelf(packets.NewId(c.client.Id()))
}

func (c *Connected) HandleMessage(senderId uint64, message packets.Msg) {
	c.logger.Printf("接收到来自客户端 %d 的消息，类型：%T", senderId, message)
}

func (c *Connected) OnExit() {

}

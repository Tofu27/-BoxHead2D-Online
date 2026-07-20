package states

import (
	"fmt"
	"log"
	"server/internal/server/interfaces"
	"server/internal/server/objects"
	"server/pkg/packets"
)

type InHall struct {
	client interfaces.ClientInterfacer
	player *objects.Player
	logger *log.Logger
}

func (c *InHall) Name() string {
	return "InHall"
}

func (c *InHall) SetClient(client interfaces.ClientInterfacer) {
	c.client = client
	loggingPrefix := fmt.Sprintf("客户端 %d [%s]:", client.Id(), c.Name())
	c.logger = log.New(log.Writer(), loggingPrefix, log.LstdFlags)
}

func (c *InHall) OnEnter() {

	c.client.SendToSelf(packets.NewPlayer(c.client.Id(), c.player))
}

func (c *InHall) HandleMessage(senderId uint64, message packets.Msg) {
	c.logger.Printf("接收到来自客户端 %d 的消息：%+v", senderId, message)

}

func (c *InHall) OnExit() {

}

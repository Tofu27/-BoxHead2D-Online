package states

import (
	"fmt"
	"log"
	"server/internal/server/interfaces"
	"server/internal/server/objects"
	"server/pkg/packets"
)

type InGame struct {
	client interfaces.ClientInterfacer
	user   *objects.User
	logger *log.Logger
}

func (c *InGame) Name() string {
	return "InGame"
}

func (c *InGame) SetClient(client interfaces.ClientInterfacer) {
	c.client = client
	loggingPrefix := fmt.Sprintf("客户端 %d [%s]:", client.Id(), c.Name())
	c.logger = log.New(log.Writer(), loggingPrefix, log.LstdFlags)
}

func (c *InGame) OnEnter() {
	c.logger.Printf("玩家 %s 进入游戏", c.user.Username)
	// TODO: 初始化游戏逻辑（地图、物理、同步等）

}

func (c *InGame) HandleMessage(senderId uint64, message packets.Msg) {
	c.logger.Printf("收到消息: %T", message)
	// TODO: 处理游戏内消息（移动、攻击等）

}

func (c *InGame) OnExit() {

}

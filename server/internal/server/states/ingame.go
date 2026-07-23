package states

import (
	"context"
	"fmt"
	"log"
	"math"
	"math/rand"
	"server/internal/server/game"
	"server/internal/server/interfaces"
	"server/internal/server/objects"
	"server/pkg/packets"
	"time"
)

type InGame struct {
	client interfaces.ClientInterfacer
	user   *objects.User
	logger *log.Logger

	gameMap *game.GameMap

	cancelPlayerUpdateLoop context.CancelFunc
}

func (c *InGame) Name() string {
	return "InGame"
}

func (c *InGame) SetClient(client interfaces.ClientInterfacer) {
	c.client = client
	c.gameMap = client.GetGameMap()

	loggingPrefix := fmt.Sprintf("客户端 %d [%s]:", client.Id(), c.Name())
	c.logger = log.New(log.Writer(), loggingPrefix, log.LstdFlags)
}

func (c *InGame) OnEnter() {
	c.logger.Printf("玩家 %s 进入游戏", c.user.Username)
	// TODO: 初始化游戏逻辑（地图、物理、同步等）

	// 1. 发送地图数据给客户端
	// go c.sendMapData()

	playerX := rand.Float64() * float64(c.gameMap.Width)
	playerY := rand.Float64() * float64(c.gameMap.Height)
	playerEntity := objects.NewPlayerEntity(playerX, playerY)
	c.user.PlayerEntity = playerEntity
	c.client.GetGameObject().Users.Add(c.user, c.client.Id())

	c.client.SendToSelf(packets.NewPlayerSpawn(c.user.ID, c.user.Username, float32(playerEntity.X), float32(playerEntity.Y), float32(playerEntity.Health), float32(playerEntity.MaxHealth), float32(playerEntity.Speed)))

	if c.cancelPlayerUpdateLoop == nil {
		ctx, cancel := context.WithCancel(context.Background())
		c.cancelPlayerUpdateLoop = cancel
		go c.playerUpdateLoop(ctx)
	}
}

func (c *InGame) HandleMessage(senderId uint64, message packets.Msg) {
	c.logger.Printf("收到消息: %T", message)
	// TODO: 处理游戏内消息（移动、攻击等）

	switch message := message.(type) {
	case *packets.Packet_MoveInput:
		c.handleMoveInput(senderId, message)

	}
}

func (c *InGame) OnExit() {
	if c.cancelPlayerUpdateLoop != nil {
		c.cancelPlayerUpdateLoop()
	}
	c.client.GetGameObject().Users.Remove(c.client.Id())
}

func (c *InGame) playerUpdateLoop(ctx context.Context) {
	const delta float64 = 0.05
	ticker := time.NewTicker(time.Duration(delta*1000) * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.syncPlayer(delta)
		case <-ctx.Done():
			return
		}
	}
}

func (c *InGame) syncPlayer(delta float64) {
	player := c.user.PlayerEntity

	newX := player.X + player.Speed*math.Cos(player.Direction)*delta
	newY := player.Y + player.Speed*math.Sin(player.Direction)*delta

	player.X = newX
	player.Y = newY
}

func (c *InGame) handleMoveInput(senderId uint64, moveInput *packets.Packet_MoveInput) {
	if senderId != c.client.Id() { // 不是当前玩家信息
		return
	}

	// 防作弊：方向向量长度校验
	dirX := float64(moveInput.MoveInput.DirX)
	dirY := float64(moveInput.MoveInput.DirY)
	length := math.Sqrt(dirX*dirX + dirY*dirY)
	if length > 1.0 {
		// 非法，归一化或直接忽略
		dirX /= length
		dirY /= length
	}
	if length == 0 {
		// 静止
		c.user.PlayerEntity.IsMoving = false
	} else {
		c.user.PlayerEntity.IsMoving = true
		// 角度转为弧度（如果你的 syncPlayer 用 Cos/Sin）
		c.user.PlayerEntity.Direction = math.Atan2(dirY, dirX)
	}

	// 读取客户端上报的位置
	reportedX := float64(playerSpawn.PlayerSpawn.X)
	reportedY := float64(playerSpawn.PlayerSpawn.Y)

	// 暂时赋值
	c.user.PlayerEntity.X = reportedX
	c.user.PlayerEntity.Y = reportedY

	// 执行位置校验与修正
	correctedX, correctedY, corrected := c.gameMap.CorrectPosition(c.user.PlayerEntity)

	if corrected {
		c.logger.Printf("玩家 %s 位置被修正: (%.2f, %.2f) -> (%.2f, %.2f)",
			c.user.Username, reportedX, reportedY, correctedX, correctedY)
		c.user.PlayerEntity.X = correctedX
		c.user.PlayerEntity.Y = correctedY
	} else {
		c.user.PlayerEntity.X = reportedX
		c.user.PlayerEntity.Y = reportedY
	}
}

func (c *InGame) sendMapData() {
	// 将二维碰撞数组转为一维
	gridData := make([]uint32, 0, c.gameMap.GridWidth*c.gameMap.GridHeight)
	for y := 0; y < c.gameMap.GridHeight; y++ {
		for x := 0; x < c.gameMap.GridWidth; x++ {
			if c.gameMap.CollisionGrid[y][x] {
				gridData = append(gridData, 1)
			} else {
				gridData = append(gridData, 0)
			}
		}
	}

	spawnPoints := make([]*packets.SpawnPoint, 0)
	for _, sp := range c.gameMap.SpawnPoints {
		spawnPoints = append(spawnPoints, &packets.SpawnPoint{
			X: float32(sp.X),
			Y: float32(sp.Y),
		})
	}

	c.client.SendToSelf(packets.NewMapData(uint32(c.gameMap.Width), uint32(c.gameMap.Height), uint32(c.gameMap.TileWidth), uint32(c.gameMap.TileHeight), uint32(c.gameMap.GridWidth), uint32(c.gameMap.GridHeight), gridData, spawnPoints))
}

package states

import (
	"context"
	"errors"
	"fmt"
	"log"
	"server/internal/server/db"
	"server/internal/server/interfaces"
	"server/internal/server/objects"
	"server/pkg/packets"
	"strings"

	"golang.org/x/crypto/bcrypt"
)

type Connected struct {
	client interfaces.ClientInterfacer
	logger *log.Logger

	queries *db.Queries
	dbCtx   context.Context
}

func (c *Connected) Name() string {
	return "Connected"
}

func (c *Connected) SetClient(client interfaces.ClientInterfacer) {
	c.client = client
	c.dbCtx = client.DbTx().Ctx
	c.queries = client.DbTx().Queries

	loggingPrefix := fmt.Sprintf("客户端 %d [%s]:", client.Id(), c.Name())
	c.logger = log.New(log.Writer(), loggingPrefix, log.LstdFlags)
}

func (c *Connected) OnEnter() {
	c.client.SendToSelf(packets.NewId(c.client.Id()))
}

func (c *Connected) HandleMessage(senderId uint64, message packets.Msg) {
	c.logger.Printf("接收到来自客户端 %d 的消息：%+v", senderId, message)

	switch message := message.(type) {
	case *packets.Packet_LoginRequest:
		c.handleLoginRequest(senderId, message)
	case *packets.Packet_RegisterRequest:
		c.handleRegisterRequest(senderId, message)
	}

}

func (c *Connected) OnExit() {

}

func (c *Connected) handleLoginRequest(senderId uint64, message *packets.Packet_LoginRequest) {
	if senderId != c.client.Id() {
		return
	}

	username := message.LoginRequest.Username
	genericFailMessage := packets.NewDenyResponse("用户名或密码不正确")

	user, err := c.queries.GetUserByUsername(c.dbCtx, strings.ToLower(username))
	if err != nil {
		c.logger.Printf("获取用户 %s 报错: %v", username, err)
		c.client.SendToSelf(genericFailMessage)
		return
	}

	err = bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(message.LoginRequest.Password))
	if err != nil {
		c.logger.Printf("用户输入了错误的密码: %s", username)
		c.client.SendToSelf(genericFailMessage)
		return
	}

	c.client.SendToSelf(packets.NewOkResponse())
	c.logger.Printf("用户 %s 登录成功", username)

	player, err := c.queries.GetPlayerByUserID(c.dbCtx, user.ID)
	if err != nil {
		c.logger.Printf("获取用户 %s 的玩家信息失败: %v", username, err)
		c.client.SendToSelf(genericFailMessage)
		return
	}

	c.client.SetState(&InHall{
		player: &objects.Player{
			Name: username,
			DbId: player.ID,
		},
	})
}

func (c *Connected) handleRegisterRequest(senderId uint64, message *packets.Packet_RegisterRequest) {
	if senderId != c.client.Id() {
		return
	}

	username := strings.ToLower(message.RegisterRequest.Username)

	err := validateUsername(message.RegisterRequest.Username)
	if err != nil {
		reason := fmt.Sprintf("无效用户名: %v", err)
		c.logger.Println(reason)
		c.client.SendToSelf(packets.NewDenyResponse(reason))
		return
	}

	_, err = c.queries.GetUserByUsername(c.dbCtx, username)
	if err == nil {
		c.logger.Printf("用户已经存在: %s", username)
		c.client.SendToSelf(packets.NewDenyResponse("User already exists"))
		return
	}

	genericFailMessage := packets.NewDenyResponse("注册用户时出错（内部服务器错误）-请稍后重试")

	passwordHash, err := bcrypt.GenerateFromPassword([]byte(message.RegisterRequest.Password), bcrypt.DefaultCost)
	if err != nil {
		c.logger.Printf("哈希密码报错: %s", username)
		c.client.SendToSelf(genericFailMessage)
		return
	}

	var user db.User
	user, err = c.queries.CreateUser(c.dbCtx, db.CreateUserParams{
		Username:     username,
		PasswordHash: string(passwordHash),
	})

	if err != nil {
		c.logger.Printf("创建用户 %s 报错: %v", username, err)
		c.client.SendToSelf(genericFailMessage)
		return
	}

	_, err = c.queries.CreatePlayer(c.dbCtx, db.CreatePlayerParams{
		UserID: user.ID,
		Name:   message.RegisterRequest.Username,
	})

	if err != nil {
		c.logger.Printf("为用户 %s 创建玩家报错: %v", username, err)
		c.client.SendToSelf(genericFailMessage)
		return
	}

	c.client.SendToSelf(packets.NewOkResponse())
	c.logger.Printf("用户 %s 注册成功", username)
}

func validateUsername(username string) error {
	if len(username) <= 0 {
		return errors.New("empty")
	}

	if len(username) > 20 {
		return errors.New("too long")
	}

	if username != strings.TrimSpace(username) {
		return errors.New("leading or trailing whitespace")
	}

	return nil
}

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
	user   *objects.User
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

}

func (c *InHall) HandleMessage(senderId uint64, message packets.Msg) {
	c.logger.Printf("接收到来自客户端 %d 的消息：%+v", senderId, message)

	switch message := message.(type) {
	case *packets.Packet_RoomListRequest:
		c.handleRoomListRequest(senderId, message)
	case *packets.Packet_CreateRoomRequest:
		c.handleCreateRoomRequest(senderId, message)
	case *packets.Packet_JoinRoomRequest:
		c.handleJoinRoomRequest(senderId, message)
	}
}

func (c *InHall) OnExit() {

}

func (c *InHall) handleRoomListRequest(_ uint64, _ *packets.Packet_RoomListRequest) {
	rooms := c.getPacketsRoomList()
	c.client.SendToSelf(packets.NewRoomListResponse(rooms))
	c.logger.Printf("已发送房间列表，共 %d 个房间", len(rooms))
}

func (c *InHall) handleCreateRoomRequest(_ uint64, req *packets.Packet_CreateRoomRequest) {

	roomManager := c.client.GetRoomManager()
	roomName := req.CreateRoomRequest.Name
	maxPlayers := req.CreateRoomRequest.MaxPlayers

	room, err := roomManager.CreateRoom(
		roomName,
		maxPlayers,
		c.user,
	)

	if err != nil {
		c.logger.Printf("创建房间失败：%v", err)
		c.client.SendToSelf(packets.NewDenyResponse(fmt.Sprintf("创建房间失败：%v", err)))
		return
	}

	c.client.SendToSelf(packets.NewCreateRoomResponse(true, "", getPacketsRoomInfo(room)))
	c.logger.Printf("房间 %s（ID:%d）创建成功", room.Name, room.ID)
}

// 处理加入房间请求
func (c *InHall) handleJoinRoomRequest(senderId uint64, req *packets.Packet_JoinRoomRequest) {
	roomManager := c.client.GetRoomManager()
	roomID := req.JoinRoomRequest.RoomId

	room, err := roomManager.JoinRoom(
		c.user,
		roomID,
	)

	if err != nil {
		c.logger.Printf("加入房间失败：%v", err)
		c.client.SendToSelf(packets.NewDenyResponse(fmt.Sprintf("加入房间失败：%v", err)))
		return
	}

	packetRoomsInfo := getPacketsRoomInfo(room)

	// 发送加入成功响应
	c.client.SendToSelf(packets.NewJoinRoomResponse(true, "", packetRoomsInfo))
	c.logger.Printf("玩家 %s 加入房间 %s（ID:%d）", c.user.Username, room.Name, room.ID)

	// 发送房间加入通知（包含房间详情和当前玩家列表）
	c.client.SendToSelf(packets.NewRoomJoined(
		packetRoomsInfo,
		,
	))

}

// 获取房间列表（全量）
func (c *InHall) getPacketsRoomList() []*packets.RoomInfo {
	roomManager := c.client.GetRoomManager()
	var infos []*packets.RoomInfo

	roomManager.Rooms.ForEach(func(roomId uint64, room *objects.Room) {
		// 注意：Room 内部 GetPlayerCount 使用了读锁
		infos = append(infos, getPacketsRoomInfo(room))
	})
	return infos
}

func getPacketsRoomInfo(room *objects.Room) *packets.RoomInfo {
	return &packets.RoomInfo{
		RoomId:      room.ID,
		Name:        room.Name,
		PlayerCount: uint32(room.GetPlayerCount()),
		MaxPlayers:  room.MaxPlayers,
		RoomOwner: &packets.User{
			Id:       uint64(room.RoomOwner.ID),
			Username: room.RoomOwner.Username,
		},
	}
}

func getPacketsUsers(room *objects.Room) []*packets.User {
	users := make([]packets.User)
	room.ForEachPlayers(func(id uint64, player *User){
		apend
	})
}

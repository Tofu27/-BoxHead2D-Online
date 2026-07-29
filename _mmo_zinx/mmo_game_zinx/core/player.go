package core

import (
	"fmt"
	"game/pb"
	"math/rand"
	"sync"
	"zinx/ziface"

	"google.golang.org/protobuf/proto"
)

// 玩家对象
type Player struct {
	Pid  int32              // 玩家ID
	Conn ziface.IConnection // 当前玩家的连接（用于和客户端的连接）

	X float32 // 平面的X坐标
	Y float32 // 高度
	Z float32 // 平面y坐标
	V float32 // 旋转的0-360角度
}

/*
Player ID 生成器
*/
var PidGen int32 = 1  //用来生产玩家ID的计数器
var IdLock sync.Mutex //保护pidGen

// 创建一个玩家的方法
func NewPlayer(conn ziface.IConnection) *Player {
	IdLock.Lock()
	id := PidGen
	PidGen++
	defer IdLock.Unlock()

	p := &Player{
		Pid:  id,
		Conn: conn,
		X:    float32(160 + rand.Intn(10)),
		Y:    0,
		Z:    float32(140 + rand.Intn(20)),
		V:    0,
	}

	return p
}

/*
提供一个发送给客户端消息的方法
主要是将PB的protobuf数据序列化之后，再调用zinx的SendMsg方法
*/
func (p *Player) SendMsg(msgId uint32, data proto.Message) {
	// 将proto Message结构体序列化转换成二进制
	msg, err := proto.Marshal(data)
	if err != nil {
		fmt.Println("marshal msg err: ", err)
		return
	}

	// 将二进制文件 通过 zinx 框架的sendmsg 将数据发送给客户端
	if p.Conn == nil {
		fmt.Println("connection in player is nil")
		return
	}

	if err := p.Conn.SendMsg(msgId, msg); err != nil {
		fmt.Println("Player SendMsg error: ", err)
		return
	}

}

// 告知客户端玩家Pid，同步已经生成的玩家ID客户端
func (p *Player) SyncPid() {
	// 组建MsgID: 0的proto数据
	proto_msg := &pb.SyncPid{
		Pid: p.Pid,
	}

	// 将消息发送给客户端
	p.SendMsg(1, proto_msg)
}

// 广播玩家自己的出生地点
func (p *Player) BroadCastStartPosition() {
	// 组建MsgID: 200的proto数据
	proto_msg := &pb.BroadCast{
		Pid: p.Pid,
		Tp:  2, //Tp2 广播的位置坐标
		Data: &pb.BroadCast_P{
			P: &pb.Position{
				X: p.X,
				Y: p.Y,
				Z: p.Z,
				V: p.V,
			},
		},
	}

	// 将消息发送给客户端
	p.SendMsg(200, proto_msg)
}

// 玩家广播世界聊天消息
func (p *Player) Talk(content string) {

	// 组建MsgId: 200 proto 数据
	proto_msg := &pb.BroadCast{
		Pid: p.Pid,
		Tp:  1,
		Data: &pb.BroadCast_Content{
			Content: content,
		},
	}

	// 得到当前世界所有玩家
	players := WorldMgrObj.GetAllPlayers()

	// 遍历所有玩家(包括自己)发送数据
	for _, player := range players {
		// player 分别给对应的客户端发送消息
		player.SendMsg(200, proto_msg)
	}
}

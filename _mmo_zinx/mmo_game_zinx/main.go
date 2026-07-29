package main

import (
	"fmt"
	"game/apis"
	"game/core"
	"zinx/ziface"
	"zinx/znet"
)

// 当前客户端建立连接之后的hook函数
func OnConnectionAdd(conn ziface.IConnection) {
	// 创建一个Player对象
	player := core.NewPlayer(conn)

	// 给客户端发送MsgID:1的消息 同步当前Player的ID
	player.SyncPid()

	// 给客户端发送MsgID:200的消息 同步当前Player的初始位置
	player.BroadCastStartPosition()

	// 将当前新上线的玩家添加到WorldManager中
	core.WorldMgrObj.AddPlayer(player)

	// 将该连接绑定一个Pid
	conn.SetProperty("pid", player.Pid)

	fmt.Println("==> player pid = ", player.Pid, " is arrived <==")
}

func main() {
	// 创建zinx server 句柄
	s := znet.NewServer("MMO Game Zinx")

	// 连接创建和销毁的HOOK钩子函数
	s.SetOnConnStart(OnConnectionAdd)

	// 注册一些路由业务
	s.AddRouter(2, &apis.WorldChatApi{})

	// 启动服务
	s.Serve()
}

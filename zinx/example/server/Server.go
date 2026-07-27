package main

import (
	"fmt"
	"zinx/ziface"
	"zinx/znet"
)

type PingRouter struct {
	znet.BaseRouter
}

func (this *PingRouter) Handle(request ziface.IRequest) {
	fmt.Println("路由Handle")

	// 先读取客户端数据，再回写ping
	fmt.Println("接收来自客户端：msgID = ", request.GetMsgID(),
		", data = ", string(request.GetMsgData()))

	err := request.GetConnection().SendMsg(1, []byte("ping...ping..."))
	if err != nil {
		fmt.Println(err)
	}
}

type HelloRouter struct {
	znet.BaseRouter
}

func (this *HelloRouter) Handle(request ziface.IRequest) {
	// 先读取客户端数据，再回写ping
	fmt.Println("接收来自客户端：msgID = ", request.GetMsgID(),
		", data = ", string(request.GetMsgData()))

	err := request.GetConnection().SendMsg(201, []byte("hello"))
	if err != nil {
		fmt.Println(err)
	}
}

func main() {
	s := znet.NewServer("zinx")

	s.AddRouter(0, &PingRouter{})
	s.AddRouter(1, &HelloRouter{})

	s.Serve()

}

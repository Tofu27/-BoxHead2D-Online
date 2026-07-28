package ziface

import (
	"context"
	"net"
)

// 定义连接模块的抽象层
type IConnection interface {
	// 启动连接  让当前连接准备开始工作
	Start()

	// 停止连接  结束当前连接的工作
	Stop()

	// (返回ctx，用于用户自定义的go程获取连接退出状态)
	Context() context.Context

	// 获取当前连接绑定的 socket coon
	GetTCPConnection() net.Conn

	// 获取当前连接模块的连接ID
	GetConnID() uint32

	// 获取远程客户端的 TCP状态 IP port
	RemoteAddr() net.Addr

	GetMsgHandler() IMsgHandle // (获取消息处理器)

	// 发送数据，将数据发送给远程的客户端
	SendMsg(msgId uint32, data []byte) error

	// 设置连接属性
	SetProperty(key string, value interface{})
	// 获取连接属性
	GetProperty(key string) (interface{}, error)
	// 移除连接属性
	RemoveProperty(key string)
}

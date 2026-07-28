package ziface

type IServer interface {
	// 启动服务器
	Start()
	// 停止服务器
	Stop()
	// 运行服务器
	Serve()

	// 路由功能，给当前的服务注册一个路由方法，供客户端的连接处理使用
	AddRouter(msgId uint32, router IRouter)

	// (获取Server绑定的消息处理模块)
	GetMsgHandler() IMsgHandle

	// 获取当前Server的连接管理器
	GetConnMgr() IConnManager

	// (设置该Server的连接创建时Hook函数)
	SetOnConnStart(func(IConnection))
	// (设置该Server的连接断开时的Hook函数)
	SetOnConnStop(func(IConnection))
	// (得到该Server的连接创建时Hook函数)
	GetOnConnStart() func(IConnection)
	// (得到该Server的连接断开时的Hook函数)
	GetOnConnStop() func(IConnection)
}

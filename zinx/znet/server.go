package znet

import (
	"fmt"
	"net"
	"zinx/zconf"
	"zinx/ziface"
)

// IServer 接口的实现，定义一个 Server 的服务模块
type Server struct {
	// 服务器名称
	Name string
	// 服务器绑定的 ip 版本
	IpVersion string
	// 服务器监听的 ip
	IP string
	//服务器监听的端口
	Port int

	// 当前Server的消息管理模块,用来绑定MsgId和对应的处理业务API关系
	msgHandler ziface.IMsgHandle

	// 该Server的连接管理器
	ConnMgr ziface.IConnManager

	// 该server 创建连接之后自动调用Hook函数
	onConnStart func(conn ziface.IConnection)

	// 该server 销毁连接之后自动调用Hook函数
	onConnStop func(conn ziface.IConnection)
}

func NewServer(name string) ziface.IServer {

	s := &Server{
		Name:       zconf.GlobalObject.Name,
		IpVersion:  "tcp4",
		IP:         zconf.GlobalObject.Host,
		Port:       zconf.GlobalObject.TcpPort,
		msgHandler: NewMsgHandler(),
		ConnMgr:    NewConnManager(),
	}

	return s
}

func (s *Server) Start() {
	fmt.Printf("[Start] 服务名 %s, 监听 IP: %s, 端口:%d 中\n", zconf.GlobalObject.Name, zconf.GlobalObject.Host, zconf.GlobalObject.TcpPort)
	fmt.Printf("[Start] 版本号 %s, 最大连接数: %d, 数据包最大值: %d\n", zconf.GlobalObject.Version, zconf.GlobalObject.MaxConn, zconf.GlobalObject.MaxPackageSize)

	go func() {
		// 开启消息队列及Worker工作池
		s.msgHandler.StartWorkerPool()

		// 获取一个TCP的Addr
		addr, err := net.ResolveTCPAddr(s.IpVersion, fmt.Sprintf("%s:%d", s.IP, s.Port))
		if err != nil {
			fmt.Println("解析tcp地址错误: ", err)
			return
		}

		// 监听服务器地址
		listener, err := net.ListenTCP(s.IpVersion, addr)
		if err != nil {
			fmt.Println("监听 ", s.IpVersion, " 错误: ", err)
			return
		}

		fmt.Println("服务启动成功: ", s.Name, " 监听中...")

		var cid uint32
		cid = 0

		// 阻塞等待客户端连接，处理客户端连接服务
		for {
			conn, err := listener.AcceptTCP()
			if err != nil {
				fmt.Println("接收错误：", err)
				continue
			}

			// 设置最大连接个数的判断，如果超过最大连接的数量，那么则关闭此新的连接
			if s.ConnMgr.Len() >= zconf.GlobalObject.MaxConn {
				fmt.Println("超出连接最大限制，连接容量已满, MaxConn = ", zconf.GlobalObject.MaxConn)
				conn.Close()
				continue
			}

			dealConn := NewConnection(s, conn, cid)
			cid++

			go dealConn.Start()
		}
	}()
}

func (s *Server) Stop() {
	// 将一些服务器资源、状态、或者已经开辟的连接信息 进行停止或回收
	fmt.Printf("[Stop] 服务名 %s\n", zconf.GlobalObject.Name)

	s.ConnMgr.ClearConn()
}

func (s *Server) Serve() {
	s.Start()

	select {}
}

func (s *Server) AddRouter(msgId uint32, router ziface.IRouter) {
	s.msgHandler.AddRouter(msgId, router)
	fmt.Println("添加路由成功")
}

func (s *Server) GetConnMgr() ziface.IConnManager {
	return s.ConnMgr
}

func (s *Server) GetMsgHandler() ziface.IMsgHandle {
	return s.msgHandler
}

func (s *Server) SetOnConnStart(hookFunc func(ziface.IConnection)) {
	s.onConnStart = hookFunc
}

func (s *Server) SetOnConnStop(hookFunc func(ziface.IConnection)) {
	s.onConnStop = hookFunc
}

func (s *Server) GetOnConnStart() func(ziface.IConnection) {
	return s.onConnStart
}

func (s *Server) GetOnConnStop() func(ziface.IConnection) {
	return s.onConnStop
}

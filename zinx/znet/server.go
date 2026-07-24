package znet

import (
	"errors"
	"fmt"
	"net"
	"zinx/utils"
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

	// 当前的Server添加一个Router, Server注册的连接对应的处理业务
	Router ziface.IRouter
}

func CallBackToClient(conn *net.TCPConn, data []byte, cnt int) error {
	fmt.Println("[Conn Handle] 回调")
	if _, err := conn.Write(data[:cnt]); err != nil {
		fmt.Println(err)
		return errors.New("CallBackToClient error")
	}
	return nil
}

func (s *Server) Start() {
	fmt.Printf("[Start] 服务名 %s, 监听 IP: %s, 端口:%d 中\n", utils.GlobalObject.Name, utils.GlobalObject.Host, utils.GlobalObject.TcpPort)
	fmt.Printf("[Start] 版本号 %s, 最大连接数: %d, 数据包最大值: %d\n", utils.GlobalObject.Version, utils.GlobalObject.MaxConn, utils.GlobalObject.MaxPackageSize)

	go func() {
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

			dealConn := NewConnection(conn, cid, s.Router)
			cid++

			go dealConn.Start()
		}
	}()
}

func (s *Server) Stop() {

}

func (s *Server) Serve() {
	s.Start()

	select {}
}

func (s *Server) AddRouter(router ziface.IRouter) {
	s.Router = router
	fmt.Println("添加路由成功")
}

func NewServer(name string) ziface.IServer {

	s := &Server{
		Name:      utils.GlobalObject.Name,
		IpVersion: "tcp4",
		IP:        utils.GlobalObject.Host,
		Port:      utils.GlobalObject.TcpPort,
		Router:    nil,
	}

	return s
}

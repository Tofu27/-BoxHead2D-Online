package znet

import (
	"errors"
	"fmt"
	"io"
	"net"
	"zinx/ziface"
)

/*
连接模块
*/
type Connection struct {
	// 当前连接的socket TCP 套接字
	Conn *net.TCPConn

	// 连接的ID
	ConnID uint32

	// 当前连接的状态
	isClosed bool

	// 告知当前连接已经退出/停止 channel
	ExitChan chan bool

	// 该连接处理的方法Router
	Router ziface.IRouter
}

func NewConnection(conn *net.TCPConn, connID uint32, router ziface.IRouter) *Connection {
	c := &Connection{
		Conn:     conn,
		ConnID:   connID,
		Router:   router,
		isClosed: false,
		ExitChan: make(chan bool, 1),
	}

	return c
}

// 连接的 读业务方法
func (c *Connection) StartReader() {
	fmt.Println("读协程运行中...")
	defer func() {
		fmt.Println("ConnID = ", c.ConnID, "读协程退出, remote addr: ", c.RemoteAddr().String())
		c.Stop()
	}()

	for {
		// 创建一个拆包解包的对象
		dp := NewDataPack()
		// 读取客户端的Msg Head 二进制流 8个字节
		headData := make([]byte, dp.GetHeadLen())
		if _, err := io.ReadFull(c.Conn, headData); err != nil {
			fmt.Println("读取包头信息失败: ", err)
			break
		}

		// 拆包，得到MsgId和MsgDataLen 放在Msg消息中
		msg, err := dp.Unpack(headData)
		if err != nil {
			fmt.Println("解包失败: ", err)
			break
		}

		// 根据 dataLen 再次读取Data，放在msg.Data中
		var data []byte
		if msg.GetMsgLen() > 0 {
			data = make([]byte, msg.GetMsgLen())
			if _, err := io.ReadFull(c.GetTCPConnection(), data); err != nil {
				fmt.Println("读取包数据失败: ", err)
				break
			}
		}
		msg.SetData(data)

		// 得到当前Conn数据的request请求数据
		req := &Request{
			conn: c,
			msg:  msg,
		}

		// 执行注册的路由方法
		go func(request ziface.IRequest) {
			// 从路由中，找到注册绑定的Conn对应的Router调用
			c.Router.PreHandle(request)
			c.Router.Handle(request)
			c.Router.PostHandle(request)
		}(req)

	}
}

// 启动连接  让当前连接准备开始工作
func (c *Connection) Start() {
	fmt.Println("连接启动... ConnID = ", c.ConnID)

	// 启动从当前连接读取数据的业务
	go c.StartReader()
	// 启动从当前连接写数据的业务

}

// 停止连接  结束当前连接的工作
func (c *Connection) Stop() {
	fmt.Println("连接停止... ConnID = ", c.ConnID)

	// 如果连接已经关闭
	if c.isClosed == true {
		return
	}

	c.isClosed = true

	// 关闭 socket 连接
	c.Conn.Close()

	close(c.ExitChan)
}

// 获取当前连接绑定的 socket coon
func (c *Connection) GetTCPConnection() *net.TCPConn {
	return c.Conn
}

// 获取当前连接模块的连接ID
func (c *Connection) GetConnID() uint32 {
	return c.ConnID
}

// 获取远程客户端的 TCP状态 IP port
func (c *Connection) RemoteAddr() net.Addr {
	return c.Conn.RemoteAddr()
}

// 发送数据，将数据发送给远程的客户端
func (c *Connection) Send(data []byte) error {
	return nil
}

// 提供一个SendMsg方法 将我们要发送给客户端的数据，先进行封包，再发送
func (c *Connection) SendMsg(msgId uint32, data []byte) error {
	if c.isClosed == true {
		return errors.New("连接已经关闭")
	}

	// 将data进行封包 MsgDataLen/MsgID Data
	dp := NewDataPack()

	binaryMsg, err := dp.Pack(NewMsgPackage(msgId, data))
	if err != nil {
		return fmt.Errorf("封包 msdId: %d  失败: %v", msgId, err)
	}

	if _, err := c.Conn.Write(binaryMsg); err != nil {
		return fmt.Errorf("写入 msgId: %d 错误: %v", msgId, err)
	}

	return nil
}

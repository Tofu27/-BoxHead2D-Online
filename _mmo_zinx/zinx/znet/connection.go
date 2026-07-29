package znet

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"sync"
	"zinx/zconf"
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

	// 负责处理该连接的workerid
	workerID uint32

	// (告知该连接已经退出/停止的channel)
	ctx    context.Context
	cancel context.CancelFunc

	// (有缓冲管道，用于读、写两个goroutine之间的消息通信)
	msgBuffChan chan []byte

	// (消息管理MsgID和对应处理方法的消息管理模块)
	msgHandler ziface.IMsgHandle

	// (当前连接是属于哪个Connection Manager的)
	connManager ziface.IConnManager

	// (连接属性)
	property map[string]interface{}

	// (保护当前property的锁)
	propertyLock sync.RWMutex

	// (当前连接创建时Hook函数)
	onConnStart func(conn ziface.IConnection)

	// (当前连接断开时的Hook函数)
	onConnStop func(conn ziface.IConnection)
}

func NewConnection(server ziface.IServer, conn *net.TCPConn, connID uint32) *Connection {
	c := &Connection{
		Conn:        conn,
		ConnID:      connID,
		msgBuffChan: make(chan []byte, 1024),
		property:    make(map[string]interface{}),
	}

	c.msgHandler = server.GetMsgHandler()
	c.connManager = server.GetConnMgr()
	c.onConnStart = server.GetOnConnStart()
	c.onConnStop = server.GetOnConnStop()

	// (将新创建的Conn添加到连接管理中)
	server.GetConnMgr().Add(c)

	return c
}

// 连接的 读业务方法
func (c *Connection) StartReader() {
	fmt.Println("[读协程] 运行中...")
	defer func() {
		fmt.Println("ConnID = ", c.ConnID, "读协程退出, remote addr: ", c.RemoteAddr().String())
		c.Stop()
	}()

	for {
		select {
		case <-c.ctx.Done():
			return
		default:
			// 创建一个拆包解包的对象
			dp := NewDataPack()
			// 读取客户端的Msg Head 二进制流 8个字节
			headData := make([]byte, dp.GetHeadLen())
			if _, err := io.ReadFull(c.Conn, headData); err != nil {
				fmt.Println("读取包头信息失败: ", err)
				return
			}

			// 拆包，得到MsgId和MsgDataLen 放在Msg消息中
			msg, err := dp.Unpack(headData)
			if err != nil {
				fmt.Println("解包失败: ", err)
				return
			}

			// 根据 dataLen 再次读取Data，放在msg.Data中
			var data []byte
			if msg.GetMsgLen() > 0 {
				data = make([]byte, msg.GetMsgLen())
				if _, err := io.ReadFull(c.GetTCPConnection(), data); err != nil {
					fmt.Println("读取包数据失败: ", err)
					return
				}
			}
			msg.SetData(data)

			// 得到当前Conn数据的request请求数据
			req := &Request{
				conn: c,
				msg:  msg,
			}

			if zconf.GlobalObject.WorkerPoolSize > 0 {
				// 已经开启了工作池机制，将消息发送给Worker工作池处理
				c.msgHandler.SendMsgToTaskQueue(req)
			} else {
				// 从路由中 根据绑定好的MsgId 找到对应处理Api业务执行
				go c.msgHandler.DoMsgHandler(req)
			}

		}
	}
}

// 写消息的协程，专门发送给客户端消息的模块
func (c *Connection) StartWriter() {
	fmt.Println("[写协程] 运行中...")
	defer func() {
		fmt.Println("ConnID = ", c.ConnID, "写协程退出, remote addr: ", c.RemoteAddr().String())
	}()

	// 阻塞等待channel的消息, 读到消息并写给客户端
	for {
		select {
		case <-c.ctx.Done():
			return

		case data := <-c.msgBuffChan:
			// 有数据要写给客户端
			if _, err := c.Conn.Write(data); err != nil {
				fmt.Println("发送消息失败: ", err)
				return
			}
		}
	}
}

// 启动连接  让当前连接准备开始工作
func (c *Connection) Start() {
	fmt.Println("连接启动... ConnID = ", c.ConnID)

	c.ctx, c.cancel = context.WithCancel(context.Background())

	// (按照用户传递进来的创建连接时需要处理的业务，执行钩子方法)
	c.callOnConnStart()

	// 占用workerid
	c.workerID = useWorker(c)

	// 启动从当前连接读取数据的业务
	go c.StartReader()
	go c.StartWriter()

}

// 停止连接  结束当前连接的工作
func (c *Connection) Stop() {
	fmt.Println("连接停止... ConnID = ", c.ConnID)

	if c.cancel != nil {
		c.cancel()
	}

	// 调用开发者注册的 销毁链接之前 需要执行的业务Hook函数
	c.callOnConnStop()

	// 关闭 socket 连接
	if c.Conn != nil {
		_ = c.Conn.Close()
	}

	// 将当前连接从ConnMgr中移除
	if c.connManager != nil {
		c.connManager.Remove(c)
	}

	close(c.msgBuffChan)
}

// 获取当前连接绑定的 socket coon
func (c *Connection) GetTCPConnection() net.Conn {
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

	// 将data进行封包 MsgDataLen/MsgID Data
	dp := NewDataPack()

	binaryMsg, err := dp.Pack(NewMsgPackage(msgId, data))
	if err != nil {
		return fmt.Errorf("封包 msdId: %d  失败: %v", msgId, err)
	}

	// 将数据写入管道
	c.msgBuffChan <- binaryMsg

	return nil
}

// 设置连接属性
func (c *Connection) SetProperty(key string, value interface{}) {
	c.propertyLock.Lock()
	defer c.propertyLock.Unlock()

	c.property[key] = value
}

// 获取连接属性
func (c *Connection) GetProperty(key string) (interface{}, error) {
	c.propertyLock.RLock()
	defer c.propertyLock.RUnlock()

	if value, ok := c.property[key]; ok {
		return value, nil
	}

	return nil, errors.New("连接属性不存在")
}

// 移除连接属性
func (c *Connection) RemoveProperty(key string) {
	c.propertyLock.Lock()
	defer c.propertyLock.Unlock()

	delete(c.property, key)
}

func (c *Connection) callOnConnStart() {
	if c.onConnStart != nil {
		fmt.Println("CallOnConnStart 执行")
		c.onConnStart(c)
	}
}

func (c *Connection) callOnConnStop() {
	if c.onConnStop != nil {
		fmt.Println("CallOnConnStop 执行")
		c.onConnStop(c)
	}
}

func (c *Connection) Context() context.Context {
	return c.ctx
}

func (c *Connection) GetMsgHandler() ziface.IMsgHandle {
	return c.msgHandler
}

func (c *Connection) isClosed() bool {
	return c.ctx == nil || c.ctx.Err() != nil
}

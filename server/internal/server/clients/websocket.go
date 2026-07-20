package clients

import (
	"fmt"
	"log"
	"net/http"
	"server/internal/server"
	"server/internal/server/interfaces"
	"server/internal/server/managers"
	"server/internal/server/objects"
	"server/internal/server/states"
	"server/pkg/packets"
	"sync"

	"github.com/gorilla/websocket"
	"google.golang.org/protobuf/proto"
)

type WebSocketClient struct {
	id        uint64
	hub       *server.Hub
	conn      *websocket.Conn
	state     interfaces.ClientStateHandler
	sendChan  chan *packets.Packet
	closeOnce sync.Once
	logger    *log.Logger
	dbTx      *interfaces.DbTx

	user *objects.User
}

func NewWebSocketClient(hub *server.Hub, writer http.ResponseWriter, request *http.Request) (interfaces.ClientInterfacer, error) {
	upgrader := websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		CheckOrigin:     func(_ *http.Request) bool { return true },
	}

	conn, err := upgrader.Upgrade(writer, request, nil)
	if err != nil {
		return nil, err
	}

	c := &WebSocketClient{
		hub:      hub,
		conn:     conn,
		sendChan: make(chan *packets.Packet, 256),
		logger:   log.New(log.Writer(), "客户端：", log.LstdFlags),
		dbTx:     hub.NewDbTx(),
	}

	return c, nil
}

func (c *WebSocketClient) Id() uint64 {
	return c.id
}

func (c *WebSocketClient) Initialize(id uint64) {
	c.id = id
	c.logger.SetPrefix(fmt.Sprintf("客户端 %d: ", c.id))
	c.SetState(&states.Connected{})
}

func (c *WebSocketClient) DbTx() *interfaces.DbTx {
	return c.dbTx
}

func (c *WebSocketClient) SetState(state interfaces.ClientStateHandler) {
	prevStateName := "None"

	if c.state != nil {
		prevStateName = c.state.Name()
		c.state.OnExit()
	}

	newStateName := "None"
	if state != nil {
		newStateName = state.Name()
	}

	c.logger.Printf("客户端 %d 的状态从 %s 切换到 %s", c.id, prevStateName, newStateName)

	c.state = state
	if c.state != nil {
		c.state.SetClient(c)
		c.state.OnEnter()
	}
}

func (c *WebSocketClient) HandleIncomingMessage(senderId uint64, message packets.Msg) {
	c.state.HandleMessage(senderId, message)
}

func (c *WebSocketClient) SendToSelf(message packets.Msg) {
	c.SendMessageFrom(message, c.id)
}

func (c *WebSocketClient) SendMessageFrom(message packets.Msg, senderId uint64) {
	select {
	case c.sendChan <- &packets.Packet{SenderId: senderId, Msg: message}:
	default:
		c.logger.Printf("发送队列已满，丢弃消息类型：%T", message)
	}
}

func (c *WebSocketClient) ForwardToPeer(message packets.Msg, peerId uint64) {
	if peer, exists := c.hub.Clients.Get(peerId); exists {
		peer.HandleIncomingMessage(c.id, message)
	}
}

func (c *WebSocketClient) BroadcastToOthers(message packets.Msg) {
	c.hub.BroadcastChan <- &packets.Packet{SenderId: c.id, Msg: message}
}

func (c *WebSocketClient) RunReadLoop() {
	defer func() {
		c.logger.Printf("读协程关闭")
		c.Shutdown("读协程关闭")
	}()

	for {
		_, data, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				c.logger.Printf("读取消息错误：%v", err)
			}
			break
		}

		packet := &packets.Packet{}
		err = proto.Unmarshal(data, packet)
		if err != nil {
			c.logger.Printf("数据反序列化失败：%v", err)
			continue
		}

		if packet.SenderId == 0 {
			packet.SenderId = c.id
		}

		c.HandleIncomingMessage(packet.SenderId, packet.Msg)
	}
}

func (c *WebSocketClient) RunWriteLoop() {
	defer func() {
		c.logger.Printf("写协程关闭")
		c.Shutdown("写协程关闭")
	}()

	for packet := range c.sendChan {
		writer, err := c.conn.NextWriter(websocket.BinaryMessage)
		if err != nil {
			c.logger.Printf("获取写入器失败，关闭客户端：%v", err)
			return
		}

		data, err := proto.Marshal(packet)
		if err != nil {
			c.logger.Printf("序列化消息失败，丢弃消息类型：%T", packet.Msg)
			continue
		}

		_, writeErr := writer.Write(data)
		if writeErr != nil {
			c.logger.Printf("写入消息失败：%v", writeErr)
			continue
		}

		// writer.Write([]byte{'\n'})

		if closeErr := writer.Close(); closeErr != nil {
			c.logger.Printf("关闭写入器失败：%v", closeErr)
			continue
		}
	}
}

func (c *WebSocketClient) Shutdown(reason string) {
	c.logger.Printf("关闭客户端连接，原因：%s", reason)

	c.hub.UnRegisterChan <- c

	c.closeOnce.Do(func() {
		c.conn.Close()
		close(c.sendChan)
	})
}

func (c *WebSocketClient) GetRoomManager() *managers.RoomManager {
	return c.hub.RoomManager
}

func (c *WebSocketClient) SetUserInfo(user *objects.User) {
	c.user = user
}

package clients

import (
	"net/http"
	"server/internal/server"
	"server/internal/server/interfaces"

	"github.com/gorilla/websocket"
)

type WebSocketClient struct {
	id   uint64
	hub  *server.Hub
	conn *websocket.Conn
}

func NewWebSocketClient(hub *server.Hub, writer http.ResponseWriter, request *http.Request) (interfaces.ClientInterfacer, error) {

	upgrader := websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		CheckOrigin:     func(_ *http.Request) bool { return true },
	}

	conn, err := websocket.Upgrade(upgrader)
	if err != nil {
		return nil, err
	}

	c := &WebSocketClient{
		hub:  hub,
		conn: conn,
	}

	return c, nil
}

func (c *WebSocketClient) Id() uint64 {
	return c.id
}

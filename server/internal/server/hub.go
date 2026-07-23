package server

import (
	"context"
	"database/sql"
	"log"
	"net/http"
	"server/internal/server/db"
	"server/internal/server/game"
	"server/internal/server/interfaces"
	"server/internal/server/objects"
	"server/pkg/packets"

	_ "embed"
)

//go:embed db/config/table.sql
var schemaGenSql string

type Hub struct {
	Clients *objects.SyncIDMap[interfaces.ClientInterfacer]

	BroadcastChan  chan *packets.Packet
	RegisterChan   chan interfaces.ClientInterfacer
	UnRegisterChan chan interfaces.ClientInterfacer
	dbPool         *sql.DB

	GameMap *game.GameMap // ✅ 新增地图模块
}

func (h *Hub) NewDbTx() *interfaces.DbTx {
	return &interfaces.DbTx{
		Ctx:     context.Background(),
		Queries: db.New(h.dbPool),
	}
}

func NewHub(dbPool *sql.DB) *Hub {

	hub := &Hub{
		Clients: objects.NewSyncIDMap[interfaces.ClientInterfacer](),

		BroadcastChan:  make(chan *packets.Packet),
		RegisterChan:   make(chan interfaces.ClientInterfacer),
		UnRegisterChan: make(chan interfaces.ClientInterfacer),
		dbPool:         dbPool,
	}

	hub.GameMap = game.NewGameMap("resources/map1.json")
	if err := hub.GameMap.Load(); err != nil {
		log.Printf("加载地图失败: %v", err)
	} else {
		log.Printf("地图加载成功: %dx%d", hub.GameMap.Grid.Width, hub.GameMap.Grid.Height)
	}

	return hub
}

func (h *Hub) Run() {
	log.Println("等待客户端注册...")

	log.Println("数据库初始化中...")
	if _, err := h.dbPool.ExecContext(context.Background(), schemaGenSql); err != nil {
		log.Fatalf("数据库初始化失败: %v", err)
	}

	log.Println("等待客户端链接...")
	for {
		select {
		case client := <-h.RegisterChan:
			client.Initialize(uint64(h.Clients.Add(client)))

		case client := <-h.UnRegisterChan:
			h.Clients.Remove(client.Id())

		case packet := <-h.BroadcastChan:
			h.Clients.ForEach(func(clientId uint64, client interfaces.ClientInterfacer) {
				if clientId != packet.SenderId {
					client.HandleIncomingMessage(packet.SenderId, packet.Msg)
				}
			})
		}
	}
}

func (h *Hub) Serve(getNewClient func(*Hub, http.ResponseWriter, *http.Request) (interfaces.ClientInterfacer, error), writer http.ResponseWriter, request *http.Request) {
	log.Println("新客户端已连接，地址：", request.RemoteAddr)

	client, err := getNewClient(h, writer, request)

	if err != nil {
		log.Printf("新连接获取客户端时出错：%v", err)
		return
	}

	h.RegisterChan <- client
	go client.RunWriteLoop()
	go client.RunReadLoop()
}

package main

import (
	boxhead "game_server/internal/application/boxhead"
	domain "game_server/internal/domain/minigame/boxhead"
	httphandler "game_server/internal/interfaces/http"
	"log"
	"net/http"
)

func main() {
	// 1. 创建一个房间（整个游戏只有一个房间，所有玩家都进入这个房间）
	room := domain.NewRoom("boxhead_main")

	// 2. 在单独的goroutine中启动房间的主循环（Actor事件循环）
	//    这个循环会一直运行，直到调用 room.Stop()
	go room.Run()

	// 3. 创建应用层命令处理器，它封装了对房间的操作
	//    外部（如HTTP处理器）通过它来向房间发送命令，而不直接操作房间内部数据
	cmdHandler := boxhead.NewCommandHandler(room)

	// 4. 创建HTTP/WebSocket处理器，负责处理客户端创建玩家和WebSocket连接
	httpHandler := httphandler.NewHandler(room, cmdHandler)

	// 5. 注册路由
	//   /create  -> 创建玩家（HTTP GET）
	//   /ws      -> WebSocket连接（用于实时通信）
	http.HandleFunc("/create", httpHandler.HandleCreatePlayer)
	http.HandleFunc("/ws", httpHandler.HandleWebSocket)

	log.Println("服务器启动于 :8888")
	// 6. 启动HTTP服务器，默认监听8888端口
	log.Fatal(http.ListenAndServe(":8888", nil))
}

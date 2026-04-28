package main

import (
	boxhead "game_server/BoxHead"
	"log"
	"net/http"
)

func main() {
	game := boxhead.InitGame()

	http.HandleFunc("/createPlayer", game.HandleCreatePlayer)
	http.HandleFunc("/ws", game.HandleWebSocket)

	log.Println("服务启动：8888")
	err := http.ListenAndServe(":8888", nil)
	if err != nil {
		log.Fatal("服务器启动失败:", err)
	}
}

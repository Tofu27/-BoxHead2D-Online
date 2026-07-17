package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"server/internal/server"
	"server/internal/server/clients"
	"server/internal/server/database"

	_ "github.com/mattn/go-sqlite3"
)

var (
	port = flag.Int("port", 8080, "监听端口")
)

func main() {
	flag.Parse()

	// 1. 初始化数据库
	db, err := database.New("./data/game.db")
	if err != nil {
		log.Fatalf("数据库初始化失败: %v", err)
	}
	defer db.Close()

	hub := server.NewHub(db.Queries)

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		hub.Serve(clients.NewWebSocketClient, w, r)
	})

	go hub.Run()
	addr := fmt.Sprintf(":%d", *port)

	log.Printf("服务启动中%s", addr)
	err := http.ListenAndServe(addr, nil)

	if err != nil {
		log.Fatalf("服务启动失败: %v", err)
	}
}

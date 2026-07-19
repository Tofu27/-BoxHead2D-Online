package main

import (
	"database/sql"
	"flag"
	"fmt"
	"log"
	"net/http"
	"server/internal/server"
	"server/internal/server/clients"

	_ "modernc.org/sqlite"
)

var (
	port = flag.Int("port", 8080, "监听端口")
)

func main() {
	flag.Parse()

	// 1. 初始化数据库
	dbPool, err := sql.Open("sqlite", "cmd/db.sqlite")
	if err != nil {
		log.Fatalf("数据库打开失败: %v", err)
	}
	defer dbPool.Close()

	hub := server.NewHub(dbPool)

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		hub.Serve(clients.NewWebSocketClient, w, r)
	})

	go hub.Run()
	addr := fmt.Sprintf(":%d", *port)

	log.Printf("服务启动中%s", addr)
	err = http.ListenAndServe(addr, nil)

	if err != nil {
		log.Fatalf("服务启动失败: %v", err)
	}
}

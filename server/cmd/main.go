package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"server/internal/server"
	"server/internal/server/clients"
)

var (
	port = flag.Int("port", 8080, "监听端口")
)

func main() {
	hub := server.NewHub()

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

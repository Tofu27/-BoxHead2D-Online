package main

import (
	"net/http"
	"server/internal/server"
)

func main() {
	hub := server.NewHub()

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {

	})

}

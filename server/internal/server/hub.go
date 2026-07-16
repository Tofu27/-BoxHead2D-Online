package server

import (
	"server/internal/server/interfaces"
	"server/internal/server/objects"
)

type Hub struct {
	Clients *objects.SharedCollection[interfaces.ClientInterfacer]
}

func NewHub() *Hub {

	return &Hub{}
}

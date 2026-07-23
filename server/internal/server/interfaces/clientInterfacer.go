package interfaces

import (
	"context"
	"server/internal/server/db"
	"server/internal/server/game"
	"server/internal/server/objects"
	"server/pkg/packets"
)

type DbTx struct {
	Ctx     context.Context
	Queries *db.Queries
}

type ClientStateHandler interface {
	Name() string
	SetClient(client ClientInterfacer)
	OnEnter()
	HandleMessage(senderId uint64, message packets.Msg)
	OnExit()
}

type ClientInterfacer interface {
	Id() uint64
	Initialize(id uint64)

	HandleIncomingMessage(senderId uint64, message packets.Msg)
	SendToSelf(message packets.Msg)
	SendMessageFrom(message packets.Msg, senderId uint64)
	ForwardToPeer(message packets.Msg, peerId uint64)
	BroadcastToOthers(message packets.Msg)
	RunReadLoop()
	RunWriteLoop()
	Shutdown(reason string)

	SetState(newState ClientStateHandler)

	DbTx() *DbTx

	GetGameMap() *game.GameMap
	GetGameObject() *objects.GameObject
}

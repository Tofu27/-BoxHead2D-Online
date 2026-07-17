package interfaces

import "server/pkg/packets"

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
}

package packets

// Msg 是 Packet 中 oneof 消息的接口类型
type Msg = isPacket_Msg

// ===== Common =====

func NewIdMessage(clientID uint64) Msg {
	return &Packet_Id{
		Id: &IdMessage{
			ClientId: clientID,
		},
	}
}

func NewOkResponse() Msg {
	return &Packet_OkResponse{
		OkResponse: &OkResponse{},
	}
}

func NewDenyResponse(reason string) Msg {
	return &Packet_DenyResponse{
		DenyResponse: &DenyResponse{
			Reason: reason,
		},
	}
}

func NewDisconnect(reason string) Msg {
	return &Packet_Disconnect{
		Disconnect: &DisconnectMessage{
			Reason: reason,
		},
	}
}

func NewChat(msg string) Msg {
	return &Packet_Chat{
		Chat: &ChatMessage{
			Msg: msg,
		},
	}
}

// ===== Auth =====

func NewLoginResponse(success bool, reason string, user *User) Msg {
	return &Packet_LoginResponse{
		LoginResponse: &LoginResponse{
			Success: success,
			Reason:  reason,
			User:    user,
		},
	}
}

// ===== Game =====

func NewPlayerList(players []*User, roomOwner *User, maxPlayers uint32) Msg {
	return &Packet_PlayerList{
		PlayerList: &PlayerList{
			Players:    players,
			RoomOwner:  roomOwner,
			MaxPlayers: maxPlayers,
		},
	}
}

func NewPlayerJoined(player *User) Msg {
	return &Packet_PlayerJoined{
		PlayerJoined: &PlayerJoined{
			Player: player,
		},
	}
}

func NewPlayerLeft(playerID uint64, username string) Msg {
	return &Packet_PlayerLeft{
		PlayerLeft: &PlayerLeft{
			PlayerId: playerID,
			Username: username,
		},
	}
}

func NewStartGameResponse(success bool, reason string) Msg {
	return &Packet_StartGameResponse{
		StartGameResponse: &StartGameResponse{
			Success: success,
			Reason:  reason,
		},
	}
}

func NewGameStarting(roomID uint64) Msg {
	return &Packet_GameStarting{
		GameStarting: &GameStarting{
			RoomId: roomID,
		},
	}
}

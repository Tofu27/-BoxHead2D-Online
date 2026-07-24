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

// NewMapData 创建地图数据消息
func NewMapData(width, height, tileWidth, tileHeight, gridWidth, gridHeight uint32,
	collisionGrid []uint32, spawnPoints []*SpawnPoint) Msg {
	return &Packet_MapData{
		MapData: &MapData{
			Width:         width,
			Height:        height,
			TileWidth:     tileWidth,
			TileHeight:    tileHeight,
			GridWidth:     gridWidth,
			GridHeight:    gridHeight,
			CollisionGrid: collisionGrid,
			SpawnPoints:   spawnPoints,
		},
	}
}

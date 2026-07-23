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

// NewPlayerSpawn 创建玩家生成消息
func NewPlayerSpawn(playerID uint64, username string, x, y, health, maxHealth, speed float32) Msg {
	return &Packet_PlayerSpawn{
		PlayerSpawn: &PlayerSpawn{
			PlayerId:  playerID,
			Username:  username,
			X:         x,
			Y:         y,
			Health:    health,
			MaxHealth: maxHealth,
			Speed:     speed,
		},
	}
}

// NewPlayerState 创建单个玩家状态消息
func NewPlayerState(playerID uint64, x, y, health float32, isMoving bool) Msg {
	return &Packet_PlayerState{
		PlayerState: &PlayerState{
			PlayerId: playerID,
			X:        x,
			Y:        y,
			Health:   health,
			IsMoving: isMoving,
		},
	}
}

// NewPlayerLeave 创建玩家离开消息
func NewPlayerLeave(playerID uint64) Msg {
	return &Packet_PlayerLeave{
		PlayerLeave: &PlayerLeave{
			PlayerId: playerID,
		},
	}
}

// NewWorldState 创建世界状态消息
func NewWorldState(players []*PlayerState) Msg {
	return &Packet_WorldState{
		WorldState: &WorldState{
			Players: players,
		},
	}
}

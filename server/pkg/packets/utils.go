package packets

type Msg = isPacket_Msg

// ===== 基础消息 =====
func NewChat(msg string) Msg {
	return &Packet_Chat{
		Chat: &ChatMessage{
			Msg: msg,
		},
	}
}

func NewId(id uint64) Msg {
	return &Packet_Id{
		Id: &IdMessage{
			ClientId: id,
		},
	}
}

// ===== 登录/注册 =====
func NewDenyResponse(reason string) Msg {
	return &Packet_DenyResponse{
		DenyResponse: &DenyResponse{
			Reason: reason,
		},
	}
}

func NewOkResponse() Msg {
	return &Packet_OkResponse{
		OkResponse: &OkResponse{},
	}
}

func NewLoginRequest(username, password string) Msg {
	return &Packet_LoginRequest{
		LoginRequest: &LoginRequest{
			Username: username,
			Password: password,
		},
	}
}

func NewLoginResponse(userId uint64, username string) Msg {
	return &Packet_LoginResponse{
		LoginResponse: &LoginResponse{
			User: &User{
				Id:       userId,
				Username: username,
			},
		},
	}
}

func NewRegisterRequest(username, password string) Msg {
	return &Packet_RegisterRequest{
		RegisterRequest: &RegisterRequest{
			Username: username,
			Password: password,
		},
	}
}

// ===== 大厅/房间 =====
// 房间信息（通常由服务端构造，客户端也可使用）
func NewRoomInfo(roomId uint64, name string, playerCount, maxPlayers uint32, user *User) Msg {
	return &Packet_RoomInfo{
		RoomInfo: &RoomInfo{
			RoomId:      roomId,
			Name:        name,
			PlayerCount: playerCount,
			MaxPlayers:  maxPlayers,
			RoomOwner:   user,
		},
	}
}

// 请求房间列表（客户端发送）
func NewRoomListRequest() Msg {
	return &Packet_RoomListRequest{
		RoomListRequest: &RoomListRequest{},
	}
}

// 房间列表响应（服务端发送）
func NewRoomListResponse(rooms []*RoomInfo) Msg {
	return &Packet_RoomListResponse{
		RoomListResponse: &RoomListResponse{
			Rooms: rooms,
		},
	}
}

// 创建房间请求（客户端发送）
func NewCreateRoomRequest(name string, maxPlayers uint32) Msg {
	return &Packet_CreateRoomRequest{
		CreateRoomRequest: &CreateRoomRequest{
			Name:       name,
			MaxPlayers: maxPlayers,
		},
	}
}

// 创建房间响应（服务端发送）
func NewCreateRoomResponse(success bool, reason string, room *RoomInfo) Msg {
	return &Packet_CreateRoomResponse{
		CreateRoomResponse: &CreateRoomResponse{
			Success: success,
			Reason:  reason,
			Room:    room,
		},
	}
}

// 加入房间请求（客户端发送）
func NewJoinRoomRequest(roomId uint64) Msg {
	return &Packet_JoinRoomRequest{
		JoinRoomRequest: &JoinRoomRequest{
			RoomId: roomId,
		},
	}
}

// 加入房间响应（服务端发送）
func NewJoinRoomResponse(success bool, reason string, room *RoomInfo) Msg {
	return &Packet_JoinRoomResponse{
		JoinRoomResponse: &JoinRoomResponse{
			Success: success,
			Reason:  reason,
			Room:    room,
		},
	}
}

// 房间列表更新（服务端广播）
func NewRoomListUpdate(added []*RoomInfo, removed []uint64) Msg {
	return &Packet_RoomListUpdate{
		RoomListUpdate: &RoomListUpdate{
			Added:   added,
			Removed: removed,
		},
	}
}

// 玩家进入房间通知（服务端发送给加入者）
func NewRoomJoined(room *RoomInfo, users []*User) Msg {
	return &Packet_RoomJoined{
		RoomJoined: &RoomJoined{
			Room:  room,
			Users: users,
		},
	}
}

// 玩家简要信息（可单独发送，但通常包含在 RoomJoined 中）
func NewUser(id uint64, username string) Msg {
	return &Packet_User{
		User: &User{
			Id:       id,
			Username: username,
		},
	}
}

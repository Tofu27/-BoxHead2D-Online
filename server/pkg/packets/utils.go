package packets

// Msg 是 Packet 中 oneof 消息的接口类型
type Msg = isPacket_Msg

// ===== Common =====

// NewIdMessage 创建 ID 消息（服务器分配客户端 ID）
func NewIdMessage(clientID uint64) Msg {
	return &Packet_Id{
		Id: &IdMessage{
			ClientId: clientID,
		},
	}
}

// NewOkResponse 创建通用成功响应
func NewOkResponse() Msg {
	return &Packet_OkResponse{
		OkResponse: &OkResponse{},
	}
}

// NewDenyResponse 创建通用错误响应
func NewDenyResponse(reason string) Msg {
	return &Packet_DenyResponse{
		DenyResponse: &DenyResponse{
			Reason: reason,
		},
	}
}

// NewDisconnect 创建断开连接消息
func NewDisconnect(reason string) Msg {
	return &Packet_Disconnect{
		Disconnect: &DisconnectMessage{
			Reason: reason,
		},
	}
}

// NewChat 创建聊天消息
func NewChat(msg string) Msg {
	return &Packet_Chat{
		Chat: &ChatMessage{
			Msg: msg,
		},
	}
}

// ===== Auth =====

// NewLoginResponse 创建登录响应
func NewLoginResponse(success bool, reason string, user *User) Msg {
	return &Packet_LoginResponse{
		LoginResponse: &LoginResponse{
			Success: success,
			Reason:  reason,
			User:    user,
		},
	}
}

// ===== Hall =====

// NewCreateRoomResponse 创建房间响应
func NewCreateRoomResponse(success bool, reason string, room *RoomInfo) Msg {
	return &Packet_CreateRoomResponse{
		CreateRoomResponse: &CreateRoomResponse{
			Success: success,
			Reason:  reason,
			Room:    room,
		},
	}
}

// NewJoinRoomResponse 加入房间响应
func NewJoinRoomResponse(success bool, reason string, room *RoomInfo) Msg {
	return &Packet_JoinRoomResponse{
		JoinRoomResponse: &JoinRoomResponse{
			Success: success,
			Reason:  reason,
			Room:    room,
		},
	}
}

// NewRoomJoined 房间加入/更新通知（服务端推送）
func NewRoomJoined(room *RoomInfo, users []*User) Msg {
	return &Packet_RoomJoined{
		RoomJoined: &RoomJoined{
			Room:  room,
			Users: users,
		},
	}
}

package managers

import (
	"errors"
	"server/internal/server/objects"
	"sync"
)

type RoomManager struct {
	Rooms *objects.SyncIDMap[*objects.Room]

	mu     sync.Mutex
	nextId uint64
}

func NewManager() *RoomManager {
	return &RoomManager{
		Rooms:  objects.NewSyncIDMap[*objects.Room](),
		nextId: 1,
	}
}

func (m *RoomManager) CreateRoom(roomName string, maxPlayers uint32, roomOwner *objects.User) (*objects.Room, error) {
	m.mu.Lock()
	id := m.nextId
	m.nextId++
	m.mu.Unlock()

	room := objects.NewRoom(id, roomName, maxPlayers, roomOwner)
	m.Rooms.Add(room, id) // SyncIDMap.Add 是线程安全的

	return room, nil
}

// 加入房间
func (m *RoomManager) JoinRoom(user *objects.User, roomID uint64) (*objects.Room, error) {
	room, ok := m.Rooms.Get(roomID)

	if !ok {
		return nil, errors.New("房间不存在")
	}

	if !room.AddPlayer(user) {
		return nil, errors.New("房间已满")
	}

	return room, nil
}

// 离开房间
func (m *RoomManager) LeaveRoom(userID uint64, roomID uint64) {
	room, ok := m.Rooms.Get(roomID)
	if !ok {
		return
	}
	room.RemovePlayer(userID)
	// 如果房间为空，销毁
	if room.IsEmpty() {
		m.DestroyRoom(roomID)
	} else {
		// 广播更新
	}
}

// 销毁房间
func (m *RoomManager) DestroyRoom(roomID uint64) {
	m.Rooms.Remove(roomID)
}

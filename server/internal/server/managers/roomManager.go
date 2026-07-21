package managers

import (
	"errors"
	"server/internal/server/objects"
	"sync"
)

// RoomManager 管理单个房间实例
type RoomManager struct {
	room *objects.Room
	mu   sync.RWMutex // 保护 room 字段
}

// NewRoomManager 创建 RoomManager 实例
func NewRoomManager() *RoomManager {
	return &RoomManager{}
}

// CreateRoom 创建房间，如果已存在则返回错误
func (m *RoomManager) CreateRoom(maxPlayers uint32, owner *objects.User) (*objects.Room, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.room != nil {
		return m.room, errors.New("房间已存在")
	}

	// 使用 objects.NewRoom 创建房间（房主会自动加入 Players）
	room := objects.NewRoom(1, maxPlayers, owner) // ID 固定为 1，因为只有一个房间
	m.room = room
	return room, nil
}

// GetRoom 获取当前房间（只读）
func (m *RoomManager) GetRoom() *objects.Room {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.room
}

// IsRoomExist 检查房间是否存在
func (m *RoomManager) IsRoomExist() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.room != nil
}

// JoinRoom 加入当前房间
func (m *RoomManager) JoinRoom(user *objects.User) error {
	m.mu.RLock()
	room := m.room
	m.mu.RUnlock()

	if room == nil {
		return errors.New("房间不存在")
	}

	if !room.AddPlayer(user) {
		return errors.New("房间已满")
	}
	return nil
}

// LeaveRoom 离开当前房间
func (m *RoomManager) LeaveRoom(userID uint64) error {
	m.mu.RLock()
	room := m.room
	m.mu.RUnlock()

	if room == nil {
		return errors.New("房间不存在")
	}

	room.RemovePlayer(userID)

	// 如果房间为空，自动销毁
	if room.IsEmpty() {
		m.DestroyRoom()
	}
	return nil
}

// DestroyRoom 销毁房间（清空引用）
func (m *RoomManager) DestroyRoom() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.room = nil
}

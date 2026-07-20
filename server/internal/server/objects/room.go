package objects

import (
	"sync"
)

type Room struct {
	ID           uint64
	Name         string
	MaxPlayers   uint32
	RoomOwner    *User            // 房主
	Players      map[uint64]*User // key = 玩家
	nextPlayerId uint64
	mu           sync.RWMutex // 保护 Players 和内部状态
}

func NewRoom(id uint64, name string, maxPlayers uint32, owner *User) *Room {
	r := &Room{
		ID:         id,
		Name:       name,
		MaxPlayers: maxPlayers,
		RoomOwner:  owner,
		Players:    make(map[uint64]*User),
	}

	if owner != nil {
		r.Players[owner.ID] = owner
	}
	return r
}

func (r *Room) AddPlayer(player *User) bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	if len(r.Players) >= int(r.MaxPlayers) {
		return false
	}
	r.Players[player.ID] = player
	return true
}

func (r *Room) RemovePlayer(playerID uint64) {
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.Players, playerID)
}

func (r *Room) GetPlayers() []*User {
	r.mu.RLock()
	defer r.mu.RUnlock()
	players := make([]*User, 0, len(r.Players))
	for _, p := range r.Players {
		players = append(players, p)
	}
	return players
}

func (r *Room) ForEachPlayers(callback func(id uint64, player *User)) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	for id, player := range r.Players {
		callback(id, player)
	}
}

func (r *Room) GetPlayerCount() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.Players)
}

func (r *Room) IsEmpty() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.Players) == 0
}

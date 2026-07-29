package core

import (
	"fmt"
	"sync"
)

/*
一个AOI地图中的格子类型
*/
type Grid struct {
	// 格子ID
	GID int
	// 格子的左边边界坐标
	MinX int
	// 格子的右边边界坐标
	MaxX int
	// 格子的上边边界坐标
	MinY int
	// 格子的下边边界坐标
	MaxY int
	// 当前格子内玩家或物体成员的ID集合
	playerIDs map[int]bool
	// 保护当前集合的锁
	pIDLock sync.RWMutex
}

// 初始化当前格子的方法
func NewGrid(gID, minX, maxX, minY, maxY int) *Grid {
	grid := &Grid{
		GID:  gID,
		MinX: minX,
		MaxX: maxX,
		MinY: minY,
		MaxY: maxY,
	}

	grid.playerIDs = make(map[int]bool)

	return grid
}

// 给格子添加一个玩家
func (g *Grid) Add(playerID int) {
	g.pIDLock.Lock()
	defer g.pIDLock.Unlock()

	g.playerIDs[playerID] = true
}

// 删除一个玩家
func (g *Grid) Remove(playerID int) {
	g.pIDLock.Lock()
	defer g.pIDLock.Unlock()

	delete(g.playerIDs, playerID)
}

// 得到当前格子中所有的玩家
func (g *Grid) GetPlayerIds() (playerIds []int) {
	g.pIDLock.RLock()
	defer g.pIDLock.RUnlock()

	for k, _ := range g.playerIDs {
		playerIds = append(playerIds, k)
	}

	return
}

// 调试用 打印出格子的基本信息
func (g *Grid) String() string {
	return fmt.Sprintf("Grid id: %d, minX: %d, maxX: %d, minY: %d, maxY: %d, playerIDs: %v\n", g.GID, g.MinX, g.MaxX, g.MinY, g.MaxY, g.playerIDs)
}

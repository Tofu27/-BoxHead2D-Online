package core

import "sync"

/*
当前游戏的世界管理模块
*/
type WorldManager struct {
	// AOIManager 当前世界地图AOI的管理模块
	AoiMgr *AOIManager
	// 当前全部在线的Players集合
	Players map[int32]*Player
	// 保护Player集合的锁
	pLock sync.RWMutex
}

// 提供一个对外的世界管理模块句柄（全局）
var WorldMgrObj *WorldManager

// 初始化方法
func init() {
	if WorldMgrObj == nil {
		WorldMgrObj = &WorldManager{}

		// 创建世界AOI地图规划
		WorldMgrObj.AoiMgr = NewAOIManager(AOI_MIN_X, AOI_MAX_X, AOI_CNTS_X, AOI_MIN_Y, AOI_MAX_Y, AOI_CNTS_Y)

		// 初始化Player集合
		WorldMgrObj.Players = make(map[int32]*Player)
	}
}

// 添加一个玩家
func (wm *WorldManager) AddPlayer(player *Player) {
	wm.pLock.Lock()
	wm.Players[player.Pid] = player
	wm.pLock.Unlock()

	// 将player添加到地图格子中
	wm.AoiMgr.AddToGridByPos(int(player.Pid), player.X, player.Y)
}

// 删除一个玩家
func (wm *WorldManager) RemovePlayerByPid(pid int32) {
	player := wm.Players[pid]
	wm.AoiMgr.RemoveFromGridByPos(int(player.Pid), player.X, player.Y)

	wm.pLock.Lock()
	delete(wm.Players, pid)
	wm.pLock.Unlock()
}

// 通过玩家ID查询Player对象
func (wm *WorldManager) GetPlayerByPid(pid int32) *Player {
	wm.pLock.RLock()
	defer wm.pLock.RUnlock()

	return wm.Players[pid]
}

// 获取全部的玩家
func (wm *WorldManager) GetAllPlayers() []*Player {
	wm.pLock.RLock()
	defer wm.pLock.RUnlock()

	players := make([]*Player, 0)
	for _, player := range wm.Players {
		players = append(players, player)
	}

	return players
}

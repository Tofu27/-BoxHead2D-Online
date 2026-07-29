package core

import (
	"fmt"
	"testing"
)

func TestNewAOIManager(t *testing.T) {
	aoiMgr := NewAOIManager(100, 300, 4, 200, 450, 5)

	fmt.Println(aoiMgr.String())
}

func TestAOIManagerSuroundGridsByGid(t *testing.T) {
	// 初始化AOIManager
	aoiMgr := NewAOIManager(0, 250, 5, 0, 250, 5)

	for gid, _ := range aoiMgr.grids {
		// 得到当前gid的周边九宫格信息
		grids := aoiMgr.GetSurroundGridsByGid(gid)
		fmt.Println("gid: ", gid, "grids len = ", len(grids))
		gids := make([]int, 0, len(grids))
		for _, grid := range grids {
			gids = append(gids, grid.GID)
		}

		fmt.Printf("suround grid Ids: %v\n", gids)
	}
}

// 通过横纵坐标得到当前GID格子编号
func (m *AOIManager) GetGidByPos(x, y float32) int {
	idx := (int(x) - m.MinX) / m.gridWidth()
	idy := (int(y) - m.MinY) / m.gridHeight()

	return idy*m.CntsX + idx
}

// 通过横纵坐标得到周边九宫格内全部的playerIds
func (m *AOIManager) GetPidsByPos(x, y float32) (playerIds []int) {
	// 得到当前玩家的Gid格子id
	gid := m.GetGidByPos(x, y)

	// 通过GID得到周边九宫格信息
	grids := m.GetSurroundGridsByGid(gid)

	// 再将九宫格的信息里的全部playerd的id放在playerIds
	for _, v := range grids {
		playerIds = append(playerIds, v.GetPlayerIds()...)
	}

	return
}

// 添加一个PlayerId到一个格子中
func (m *AOIManager) AddPidToGrid(pid, gid int) {
	m.grids[gid].Add(pid)
}

// 移除一个格子中的playerId
func (m *AOIManager) RemovePidFromGrid(pid, gid int) {
	m.grids[gid].Remove(pid)
}

// 通过Gid获取全部的playerID
func (m *AOIManager) GetPidsByGid(gid int) (playerIds []int) {
	playerIds = m.grids[gid].GetPlayerIds()
	return
}

// 通过坐标将Player添加到一个格子中
func (m *AOIManager) AddToGridByPos(pid int, x, y float32) {
	gid := m.GetGidByPos(x, y)
	m.grids[gid].Add(pid)
}

// 通过坐标把一个Player从一个格子中删除
func (m *AOIManager) RemoveFromGridByPos(pid int, x, y float32) {
	gid := m.GetGidByPos(x, y)
	m.grids[gid].Remove(pid)
}

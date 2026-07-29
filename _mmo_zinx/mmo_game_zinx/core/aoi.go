package core

import "fmt"

// 定义一些AOI的边界值
const (
	AOI_MIN_X  int = 85
	AOI_MAX_X  int = 410
	AOI_CNTS_X int = 10
	AOI_MIN_Y  int = 75
	AOI_MAX_Y  int = 400
	AOI_CNTS_Y int = 20
)

/*
	AOI区域管理模块
*/

type AOIManager struct {
	// 区域的左边界坐标
	MinX int
	// 区域的右边界坐标
	MaxX int
	// X方向格子的数量
	CntsX int
	// 区域的上边界坐标
	MinY int
	// 区域的下边界坐标
	MaxY int
	// Y方向格子的数量
	CntsY int
	// 当前区域中有哪些格子map-key=格子的ID, value=格子对象
	grids map[int]*Grid
}

/*
	初始化一个AOI区域管理模块
*/

func NewAOIManager(minX, maxX, cntsX, minY, maxY, cntsY int) *AOIManager {
	AOIMgr := &AOIManager{
		MinX:  minX,
		MaxX:  maxX,
		MinY:  minY,
		MaxY:  maxY,
		CntsX: cntsX,
		CntsY: cntsY,
	}

	AOIMgr.grids = make(map[int]*Grid)

	gridWidth := AOIMgr.gridWidth()
	gridHeight := AOIMgr.gridHeight()

	// 初始化 AOI 格子
	for y := 0; y < cntsY; y++ {
		for x := 0; x < cntsX; x++ {
			// 计算格子ID 根据x,y编号
			// 格子编号：id = idy * CntsX + idx
			gid := y*cntsX + x

			// 初始化gid格子
			AOIMgr.grids[gid] = NewGrid(
				gid,
				AOIMgr.MinX+x*gridWidth,
				AOIMgr.MinX+(x+1)*gridWidth,
				AOIMgr.MinY+y*gridHeight,
				AOIMgr.MinY+(y+1)*gridHeight,
			)
		}
	}

	return AOIMgr
}

// 得到每个格子在X轴方向的宽度
func (m *AOIManager) gridWidth() int {
	return (m.MaxX - m.MinX) / m.CntsX
}

// 得到每个格子在Y轴方向的高度
func (m *AOIManager) gridHeight() int {
	return (m.MaxY - m.MinY) / m.CntsY
}

// 打印格子信息
func (m *AOIManager) String() string {
	// 打印AOIManager信息
	s := fmt.Sprintf("AOIManager: \n MinX: %d, MaxX: %d, MinY: %d, MaxY: %d, CntsX: %d, cntsY: %d\n", m.MinX, m.MaxX, m.MinY, m.MaxY, m.CntsX, m.CntsY)

	// 打印格子信息
	for _, grid := range m.grids {
		s += fmt.Sprintln(grid.String())
	}

	return s
}

// 根据格子GID得到周边九宫格格子集合
func (m *AOIManager) GetSurroundGridsByGid(gid int) (grids []*Grid) {
	// 判断GID是否在AOIManager中
	if _, ok := m.grids[gid]; !ok {
		return
	}

	// 初始化grids返回值切片, 将当前gid本身加入九宫格切片中
	grids = append(grids, m.grids[gid])

	// 判断gid附近是否有格子
	// 需要通过gid得到当前格子x轴的编号 idx = id * nx
	idx := gid % m.CntsX

	// 判断 idx 编号左边是否有格子
	if idx > 0 {
		grids = append(grids, m.grids[gid-1])
	}

	// 判断 dix 编号右边是否有格子
	if idx < m.CntsX-1 {
		grids = append(grids, m.grids[gid+1])
	}

	// 将 x 轴当前的格子都取出, 进行遍历, 再分别得到每个格子上下是否有格子
	// 得到当前 x 轴格子的ID集合
	gidsX := make([]int, 0, len(grids))
	for _, v := range grids {
		gidsX = append(gidsX, v.GID)
	}

	// 遍历gidsX集合中每个格子的gid
	for _, v := range gidsX {
		// 得到当前格子id的y轴编号 idy = id / ny
		idy := v / m.CntsX

		// gid 上边是否有格子
		if idy > 0 {
			grids = append(grids, m.grids[v-m.CntsX])
		}

		if idy < m.CntsY-1 {
			grids = append(grids, m.grids[v+m.CntsX])
		}
	}

	return
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
	if grid, ok := m.grids[gid]; ok {
		grid.Add(pid)
	} else {
		fmt.Printf("Warning: gid %d not found in grids\n", gid)
	}
}

// 通过坐标把一个Player从一个格子中删除
func (m *AOIManager) RemoveFromGridByPos(pid int, x, y float32) {
	gid := m.GetGidByPos(x, y)
	m.grids[gid].Remove(pid)
}

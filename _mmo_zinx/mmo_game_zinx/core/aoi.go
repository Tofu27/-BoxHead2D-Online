package core

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

func NewAOIManager(minX, maxX, CntsX, minY, maxY, cntsY int) *AOIManager {

}

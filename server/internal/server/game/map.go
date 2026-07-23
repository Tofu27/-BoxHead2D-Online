package game

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"server/internal/server/objects"
)

// TileLayer 地图图层
type TileLayer struct {
	Name   string `json:"name"`
	Width  int    `json:"width"`
	Height int    `json:"height"`
	Data   []int  `json:"data"`
}

// TiledMap 原始地图结构
type TiledMap struct {
	Width      int         `json:"width"`
	Height     int         `json:"height"`
	TileWidth  int         `json:"tilewidth"`
	TileHeight int         `json:"tileheight"`
	Layers     []TileLayer `json:"layers"`
}

// GameMap 游戏地图（服务端用）
type GameMap struct {
	Width         int // 像素宽度
	Height        int // 像素高度
	TileWidth     int
	TileHeight    int
	GridWidth     int      // 网格列数
	GridHeight    int      // 网格行数
	CollisionGrid [][]bool // true=阻挡
	SpawnPoints   []SpawnPoint
}

type SpawnPoint struct {
	X float64
	Y float64
}

// LoadMap 加载地图 JSON 文件
func LoadMap(path string) (*GameMap, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取地图文件失败: %w", err)
	}

	var tiledMap TiledMap
	if err := json.Unmarshal(data, &tiledMap); err != nil {
		return nil, fmt.Errorf("解析地图JSON失败: %w", err)
	}

	// 查找 wall 图层
	var wallLayer *TileLayer
	for i := range tiledMap.Layers {
		if tiledMap.Layers[i].Name == "wall" {
			wallLayer = &tiledMap.Layers[i]
			break
		}
	}

	if wallLayer == nil {
		return nil, fmt.Errorf("未找到 'wall' 图层")
	}

	// 构建碰撞矩阵
	grid := make([][]bool, wallLayer.Height)
	for y := 0; y < wallLayer.Height; y++ {
		grid[y] = make([]bool, wallLayer.Width)
		for x := 0; x < wallLayer.Width; x++ {
			idx := y*wallLayer.Width + x
			grid[y][x] = wallLayer.Data[idx] != 0
		}
	}

	mapWidth := tiledMap.Width * tiledMap.TileWidth
	mapHeight := tiledMap.Height * tiledMap.TileHeight

	// 怪物生成出生点（取地图中间上下两个门口附近）
	spawnPoints := []SpawnPoint{
		{X: float64(mapWidth / 2), Y: 0},
		{X: float64(mapWidth / 2), Y: float64(mapHeight)},
	}

	return &GameMap{
		Width:         mapWidth,
		Height:        mapHeight,
		TileWidth:     tiledMap.TileWidth,
		TileHeight:    tiledMap.TileHeight,
		GridWidth:     wallLayer.Width,
		GridHeight:    wallLayer.Height,
		CollisionGrid: grid,
		SpawnPoints:   spawnPoints,
	}, nil
}

// IsWalkable 判断某个瓦片坐标是否可通行
func (m *GameMap) IsWalkable(tileX, tileY int) bool {
	if tileY < 0 || tileY >= m.GridHeight {
		return false
	}
	if tileX < 0 || tileX >= m.GridWidth {
		return false
	}
	return !m.CollisionGrid[tileY][tileX]
}

// IsWalkableWorld 判断世界坐标是否可通行
func (m *GameMap) IsWalkableWorld(worldX, worldY float64) bool {
	tileX := int(worldX / float64(m.TileWidth))
	tileY := int(worldY / float64(m.TileHeight))
	return m.IsWalkable(tileX, tileY)
}

// GetSpawnPoint 获取一个出生点
func (m *GameMap) GetSpawnPoint(index int) SpawnPoint {
	if len(m.SpawnPoints) == 0 {
		return SpawnPoint{X: 100, Y: 100}
	}
	return m.SpawnPoints[index%len(m.SpawnPoints)]
}

// IsRectColliding 检测以(cx,cy)为中心的矩形是否与墙碰撞
func (m *GameMap) IsRectColliding(cx, cy, w, h float64) bool {
	left := cx - w/2
	right := cx + w/2
	top := cy - h/2
	bottom := cy + h/2

	// 计算覆盖的瓦片范围（包含边界）
	startX := int(math.Floor(left / float64(m.TileWidth)))
	endX := int(math.Floor((right - 1e-9) / float64(m.TileWidth)))
	startY := int(math.Floor(top / float64(m.TileHeight)))
	endY := int(math.Floor((bottom - 1e-9) / float64(m.TileHeight)))

	// 裁剪到地图边界
	if startX < 0 {
		startX = 0
	}
	if endX >= m.GridWidth {
		endX = m.GridWidth - 1
	}
	if startY < 0 {
		startY = 0
	}
	if endY >= m.GridHeight {
		endY = m.GridHeight - 1
	}

	for ty := startY; ty <= endY; ty++ {
		for tx := startX; tx <= endX; tx++ {
			if m.CollisionGrid[ty][tx] {
				return true
			}
		}
	}
	return false
}

// CorrectPosition 修正玩家位置，返回新中心坐标和是否修正
func (m *GameMap) CorrectPosition(entity *objects.PlayerEntity) (newX, newY float64, corrected bool) {
	x, y := entity.X, entity.Y
	w, h := float64(entity.Width), float64(entity.Height)

	// 如果当前位置合法，直接返回
	if !m.IsRectColliding(x, y, w, h) {
		return x, y, false
	}

	const step = 0.5    // 每次微调步长（像素）
	const maxSteps = 20 // 最大尝试步数，总修正范围 ±10 像素

	// 尝试沿 X 轴向左微调
	for i := 1; i <= maxSteps; i++ {
		newX := x - float64(i)*step
		// 检查边界和碰撞
		if newX-w/2 >= 0 && newX+w/2 <= float64(m.Width) && !m.IsRectColliding(newX, y, w, h) {
			return newX, y, true
		}
	}
	// 沿 X 轴向右微调
	for i := 1; i <= maxSteps; i++ {
		newX := x + float64(i)*step
		if newX-w/2 >= 0 && newX+w/2 <= float64(m.Width) && !m.IsRectColliding(newX, y, w, h) {
			return newX, y, true
		}
	}

	// 尝试沿 Y 轴向上微调
	for i := 1; i <= maxSteps; i++ {
		newY := y - float64(i)*step
		if newY-h/2 >= 0 && newY+h/2 <= float64(m.Height) && !m.IsRectColliding(x, newY, w, h) {
			return x, newY, true
		}
	}
	// 沿 Y 轴向下微调
	for i := 1; i <= maxSteps; i++ {
		newY := y + float64(i)*step
		if newY-h/2 >= 0 && newY+h/2 <= float64(m.Height) && !m.IsRectColliding(x, newY, w, h) {
			return x, newY, true
		}
	}

	// 若以上均失败，强制传送到第一个出生点（或地图中心）
	spawn := m.GetSpawnPoint(0)
	if m.IsRectColliding(spawn.X, spawn.Y, w, h) {
		// 如果出生点也碰撞，使用地图中心
		centerX, centerY := float64(m.Width)/2, float64(m.Height)/2
		if !m.IsRectColliding(centerX, centerY, w, h) {
			return centerX, centerY, true
		}
		// 保底值（一般不会发生）
		return 0, 0, true
	}
	return spawn.X, spawn.Y, true
}

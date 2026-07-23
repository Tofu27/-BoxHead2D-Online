package game

import (
	"encoding/json"
	"fmt"
	"os"
)

// TileLayer 表示地图的一个图层
type TileLayer struct {
	Name   string `json:"name"`
	Width  int    `json:"width"`
	Height int    `json:"height"`
	Data   []int  `json:"data"`
}

// TiledMap 表示完整的地图
type TiledMap struct {
	Width  int         `json:"width"`
	Height int         `json:"height"`
	Layers []TileLayer `json:"layers"`
}

// CollisionGrid 碰撞矩阵
type CollisionGrid struct {
	Width  int
	Height int
	Grid   [][]bool // true = 阻挡, false = 可通行
}

// GameMap 游戏地图管理器
type GameMap struct {
	filePath string
	TiledMap *TiledMap
	Grid     *CollisionGrid
}

// NewGameMap 创建地图管理器
func NewGameMap(filePath string) *GameMap {
	return &GameMap{
		filePath: filePath,
	}
}

// Load 加载地图文件
func (m *GameMap) Load() error {
	data, err := os.ReadFile(m.filePath)
	if err != nil {
		return fmt.Errorf("读取地图文件失败: %w", err)
	}

	var tiledMap TiledMap
	if err := json.Unmarshal(data, &tiledMap); err != nil {
		return fmt.Errorf("解析地图JSON失败: %w", err)
	}

	m.TiledMap = &tiledMap
	m.buildCollisionGrid()
	return nil
}

// buildCollisionGrid 构建碰撞矩阵
func (m *GameMap) buildCollisionGrid() {
	if m.TiledMap == nil {
		return
	}

	// 找到 wall 图层
	var wallLayer *TileLayer
	for i := range m.TiledMap.Layers {
		if m.TiledMap.Layers[i].Name == "wall" {
			wallLayer = &m.TiledMap.Layers[i]
			break
		}
	}

	if wallLayer == nil {
		fmt.Println("警告: 未找到 'wall' 图层，地图全部可通行")
		m.Grid = &CollisionGrid{
			Width:  m.TiledMap.Width,
			Height: m.TiledMap.Height,
			Grid:   make([][]bool, m.TiledMap.Height),
		}
		return
	}

	grid := make([][]bool, wallLayer.Height)
	for y := 0; y < wallLayer.Height; y++ {
		grid[y] = make([]bool, wallLayer.Width)
		for x := 0; x < wallLayer.Width; x++ {
			idx := y*wallLayer.Width + x
			// 值大于 0 表示有图块，不可通行
			grid[y][x] = wallLayer.Data[idx] != 0
		}
	}

	m.Grid = &CollisionGrid{
		Width:  wallLayer.Width,
		Height: wallLayer.Height,
		Grid:   grid,
	}
}

// IsWalkable 判断某 Tile 是否可通行
func (m *GameMap) IsWalkable(tileX, tileY int) bool {
	if m.Grid == nil {
		return true // 没有碰撞数据，全部可通行
	}
	if tileY < 0 || tileY >= m.Grid.Height {
		return false
	}
	if tileX < 0 || tileX >= m.Grid.Width {
		return false
	}
	return !m.Grid.Grid[tileY][tileX]
}

// WorldToTile 将世界坐标转换为 Tile 坐标
func (m *GameMap) WorldToTile(worldX, worldY float64) (int, int) {
	tileSize := 32.0 // 与 Tiled 设置一致
	return int(worldX / tileSize), int(worldY / tileSize)
}

// IsWalkableWorld 判断世界坐标是否可通行
func (m *GameMap) IsWalkableWorld(worldX, worldY float64) bool {
	tileX, tileY := m.WorldToTile(worldX, worldY)
	return m.IsWalkable(tileX, tileY)
}

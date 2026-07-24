package game

import (
	"encoding/json"
	"fmt"
	"os"
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

// IsBlocked 判断世界坐标 (x, y) 所在的格子是否被阻挡（墙或边界）
func (m *GameMap) IsBlocked(x, y float64) bool {
	// 转换为网格坐标
	gx := int(x / float64(m.TileWidth))
	gy := int(y / float64(m.TileHeight))

	// 边界检查：超出地图范围视为阻挡
	if gx < 0 || gx >= m.GridWidth || gy < 0 || gy >= m.GridHeight {
		return true
	}
	return m.CollisionGrid[gy][gx] // 注意：二维数组索引为 [行][列]，即 [y][x]
}

// IsRectBlocked 检测一个矩形区域是否与任何墙体相交（用于碰撞响应）
// 参数为矩形左上角坐标 (x, y) 和宽高 (w, h)
func (m *GameMap) IsRectBlocked(x, y, w, h float64) bool {
	// 检查矩形覆盖的所有格子，只要有一个阻挡则返回 true
	// 为了简化，只检测四个角点和中心点，或者遍历矩形覆盖的格子
	// 这里采用遍历所有覆盖格子的方式（更精确）
	left := int(x / float64(m.TileWidth))
	right := int((x + w - 1) / float64(m.TileWidth))
	top := int(y / float64(m.TileHeight))
	bottom := int((y + h - 1) / float64(m.TileHeight))

	for gy := top; gy <= bottom; gy++ {
		for gx := left; gx <= right; gx++ {
			if gx < 0 || gx >= m.GridWidth || gy < 0 || gy >= m.GridHeight {
				return true // 超出边界视为阻挡
			}
			if m.CollisionGrid[gy][gx] {
				return true
			}
		}
	}
	return false
}

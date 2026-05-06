package boxhead

import "math"

type Monster struct {
	ID            string   `json:"id"`
	CharacterType int32    `json:"character_type"`
	MonsterPos    Position `json:"monster_pos"`
	HP            int32    `json:"hp"`
	Speed         float64  `json:"speed"`
	IsWalking     bool     `json:"is_walking"`
	Width         float64  `json:"width"`  // 新增
	Height        float64  `json:"height"` // 新增

	// 脏位
	Dirty bool
}

func (m *Monster) Update(targetX, targetY, roomWidth, roomHeight float64) {
	dx := targetX - m.MonsterPos.X
	dy := targetY - m.MonsterPos.Y

	// 假设玩家碰撞体尺寸与怪物相同，如果不同可后续传参
	const playerWidth = 20.0
	const playerHeight = 30.0

	// 计算两个矩形在 X 和 Y 方向上的分离距离
	// 分离距离 = 轴上半宽和 - 轴心距绝对值，正值表示有间隙，负值表示重叠
	sepX := (m.Width+playerWidth)/2 - math.Abs(dx)
	sepY := (m.Height+playerHeight)/2 - math.Abs(dy)

	// 如果两个方向上都已经重叠或刚刚接触（留一点缓冲），停止移动
	if sepX >= -2 && sepY >= -3 {
		if m.IsWalking {
			m.IsWalking = false
			m.Dirty = true
		}
		return
	}

	step := m.Speed
	// 计算剩余距离：到目标矩形边缘的距离，可以用到矩形最近边的向量
	// 简化：直接朝目标点移动，但限制步长不超过 distance（欧氏距离也可）
	distance := math.Sqrt(dx*dx + dy*dy)

	if distance < step {
		step = distance
	}

	newX := m.MonsterPos.X + dx/distance*step
	newY := m.MonsterPos.Y + dy/distance*step

	// ---------- 基于怪物半宽/半高的边界约束 ----------
	halfW := m.Width / 2
	halfH := m.Height / 2
	wallMargin := 30.0 // 墙壁本身的厚度，若有额外墙壁像素可以设置

	// X 轴约束
	minX := halfW + wallMargin
	maxX := roomWidth - halfW - wallMargin
	if newX < minX {
		newX = minX
	}
	if newX > maxX {
		newX = maxX
	}

	// Y 轴约束
	minY := halfH + wallMargin
	maxY := roomHeight - halfH - wallMargin
	if newY < minY {
		newY = minY
	}
	if newY > maxY {
		newY = maxY
	}

	m.MonsterPos.X = newX
	m.MonsterPos.Y = newY
	m.IsWalking = true
	m.Dirty = true
}

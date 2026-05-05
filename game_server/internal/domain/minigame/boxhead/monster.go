package boxhead

import "math"

type Monster struct {
	ID         string
	Type       int32
	MonsterPos Position
	HP         int32
	Speed      float64
	Dirty      bool
}

func (m *Monster) Update(targetX, targetY, roomWidth, roomHeight float64) {
	dx := targetX - m.MonsterPos.X
	dy := targetY - m.MonsterPos.Y
	distance := math.Sqrt(dx*dx + dy*dy)
	if distance < 2 {
		return
	}
	step := m.Speed
	if distance < step {
		step = distance
	}

	newX := m.MonsterPos.X + dx/distance*step
	newY := m.MonsterPos.Y + dy/distance*step

	// 边界限制（墙壁厚度30）
	margin := 30.0
	if newX < margin {
		newX = margin
	}
	if newX > roomWidth-margin {
		newX = roomWidth - margin
	}
	if newY < margin {
		newY = margin
	}
	if newY > roomHeight-margin {
		newY = roomHeight - margin
	}

	m.MonsterPos.X = newX
	m.MonsterPos.Y = newY
	m.Dirty = true
}

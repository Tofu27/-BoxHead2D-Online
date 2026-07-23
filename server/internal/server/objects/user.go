package objects

type User struct {
	ID           uint64
	Username     string
	PlayerEntity *PlayerEntity
}

type PlayerEntity struct {
	Width     uint64 // 角色的宽
	Height    uint64 // 角色的高
	X         float64
	Y         float64
	Direction float64
	Health    float64
	MaxHealth float64
	Speed     float64
	IsMoving  bool
}

func NewPlayerEntity(x, y float64) *PlayerEntity {
	return &PlayerEntity{
		Width:     20,
		Height:    24 + 4, // 身高 + 脚
		X:         x,
		Y:         y,
		Health:    500,
		MaxHealth: 500,
		Speed:     1600,
	}
}

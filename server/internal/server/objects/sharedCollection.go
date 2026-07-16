package objects

import "sync"

type SharedCollection[T any] struct {
	objectsMap map[uint64]T
	nextId     uint64
	mapMux     sync.Mutex
}

func NewSharedCollection[T any](capacity ...int) *SharedCollection[T] {
	var newObjectMap map[uint64]T

	if len(capacity) > 0 {
		newObjectMap = make(map[uint64]T, capacity[0])
	} else {
		newObjectMap = make(map[uint64]T)
	}

	return &SharedCollection[T]{
		objectsMap: newObjectMap,
		nextId:     1,
	}
}

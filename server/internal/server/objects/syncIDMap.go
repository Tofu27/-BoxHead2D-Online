package objects

import (
	"sync"
)

type SyncIDMap[T any] struct {
	objectsMap map[uint64]T
	nextId     uint64
	mapMux     sync.RWMutex
}

func NewSyncIDMap[T any](capacity ...int) *SyncIDMap[T] {
	var newObjectMap map[uint64]T

	if len(capacity) > 0 {
		newObjectMap = make(map[uint64]T, capacity[0])
	} else {
		newObjectMap = make(map[uint64]T)
	}

	return &SyncIDMap[T]{
		objectsMap: newObjectMap,
		nextId:     1,
	}
}

func (s *SyncIDMap[T]) Add(obj T, id ...uint64) uint64 {
	s.mapMux.Lock()
	defer s.mapMux.Unlock()

	thisId := s.nextId
	if len(id) > 0 {
		thisId = id[0]
	}

	s.objectsMap[thisId] = obj
	s.nextId++

	return thisId
}

func (s *SyncIDMap[T]) Remove(id uint64) {
	s.mapMux.Lock()
	defer s.mapMux.Unlock()

	delete(s.objectsMap, id)
}

// ForEach 在锁内直接遍历（适合回调很快的场景）
func (s *SyncIDMap[T]) ForEach(callback func(uint64, T)) {
	s.mapMux.RLock()
	defer s.mapMux.RUnlock()
	for id, obj := range s.objectsMap {
		callback(id, obj)
	}
}

// ForEachSafe 拷贝后再遍历（适合回调耗时或可能修改 map 的场景）
func (s *SyncIDMap[T]) ForEachSafe(callback func(uint64, T)) {
	s.mapMux.RLock()
	localCopy := make(map[uint64]T, len(s.objectsMap))
	for id, obj := range s.objectsMap {
		localCopy[id] = obj
	}
	s.mapMux.RUnlock()

	for id, obj := range localCopy {
		callback(id, obj)
	}
}

func (s *SyncIDMap[T]) Get(id uint64) (T, bool) {
	s.mapMux.RLock()
	defer s.mapMux.RUnlock()
	obj, ok := s.objectsMap[id]
	return obj, ok
}

func (s *SyncIDMap[T]) Len() int {
	return len(s.objectsMap)
}

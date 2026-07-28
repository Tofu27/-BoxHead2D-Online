package znet

import (
	"errors"
	"fmt"
	"sync"
	"zinx/ziface"
)

/*
	连接管理模块
*/

type ConnManager struct {
	// 管理的连接集合
	connections map[uint32]ziface.IConnection
	// 保护连接集合的读写锁
	connLock sync.RWMutex
}

// 创建当前连接的方法
func NewConnManager() *ConnManager {
	cm := &ConnManager{
		connections: make(map[uint32]ziface.IConnection),
	}

	return cm
}

// 添加连接
func (connMgr *ConnManager) Add(conn ziface.IConnection) {
	connMgr.connLock.Lock()
	defer connMgr.connLock.Unlock()

	// 将conn加入到connManager中
	connMgr.connections[conn.GetConnID()] = conn
	fmt.Println("连接 ConnID = ", conn.GetConnID(), " 添加到连接管理模块, connLen = ", connMgr.Len())
}

// 删除连接
func (connMgr *ConnManager) Remove(conn ziface.IConnection) {
	connMgr.connLock.Lock()
	defer connMgr.connLock.Unlock()

	delete(connMgr.connections, conn.GetConnID())
	fmt.Println("连接 ConnID = ", conn.GetConnID(), " 从连接管理模块删除, connLen = ", len(connMgr.connections))
}

// 根据connID获取连接
func (connMgr *ConnManager) Get(connID uint32) (ziface.IConnection, error) {
	connMgr.connLock.RLock()
	defer connMgr.connLock.RUnlock()

	if conn, ok := connMgr.connections[connID]; ok {
		return conn, nil
	}
	return nil, errors.New("连接不存在")
}

// 得到当前连接总数
func (connMgr *ConnManager) Len() int {
	return len(connMgr.connections)
}

// 清楚并终止所有的连接
func (connMgr *ConnManager) ClearConn() {
	connMgr.connLock.Lock()
	defer connMgr.connLock.Unlock()

	// 删除conn并停止conn的工作
	for connID, conn := range connMgr.connections {
		conn.Stop()
		delete(connMgr.connections, connID)
	}

	fmt.Println("清除所有连接成功 connLen = ", len(connMgr.connections))
}

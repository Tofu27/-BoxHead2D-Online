// internal/server/database/database.go
package database

import (
	"context"
	"database/sql"
	_ "embed"
	"os"
	"path/filepath"

	"server/internal/server/db" // 你的 sqlc 生成的包

	_ "github.com/mattn/go-sqlite3"
)

// 使用 embed 将 schema.sql 嵌入二进制文件（推荐，避免运行时文件缺失）
//
//go:embed ../migrations/schema.sql
var schemaSQL string

// DB 封装了数据库连接和查询对象
type DB struct {
	Conn    *sql.DB
	Queries *db.Queries
}

// New 创建并初始化数据库连接，执行迁移，返回封装好的 DB 对象
func New(dbPath string) (*DB, error) {
	// 1. 确保数据库目录存在
	if err := ensureDir(dbPath); err != nil {
		return nil, err
	}

	// 2. 打开数据库连接
	conn, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, err
	}

	// 3. 执行迁移（创建表）
	if err := runMigrations(conn); err != nil {
		conn.Close()
		return nil, err
	}

	// 4. 创建 sqlc 的 Queries 对象
	queries := db.New(conn)

	return &DB{
		Conn:    conn,
		Queries: queries,
	}, nil
}

// ensureDir 确保数据库文件所在的目录存在
func ensureDir(dbPath string) error {
	dir := filepath.Dir(dbPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	return nil
}

// runMigrations 执行 schema.sql 迁移
func runMigrations(conn *sql.DB) error {
	// 如果使用 embed，直接使用嵌入的字符串
	_, err := conn.ExecContext(context.Background(), schemaSQL)
	if err != nil {
		return err
	}
	return nil
}

// Close 关闭数据库连接
func (d *DB) Close() error {
	return d.Conn.Close()
}

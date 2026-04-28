package boxhead

import (
	"encoding/json"
	"log"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

// Player 游戏玩家
type Player struct {
	UUID          string  `json:"uuid"`
	Name          string  `json:"name"`
	CharacterType string  `json:"character_type"`
	X             float64 `json:"x"`
	Y             float64 `json:"y"`
	Conn          *websocket.Conn
}

// BoxHead 游戏核心结构
type BoxHead struct {
	players map[string]*Player // key: UUID
	mu      sync.RWMutex

	// 广播频率
	tickerInterval time.Duration
	stopChan       chan struct{}
}

// 配置常量
const (
	DefaultTickerInterval = 50 * time.Millisecond // 20Hz
	WriteWait             = 10 * time.Second
	PongWait              = 60 * time.Second
	PingPeriod            = (PongWait * 9) / 10
	MaxMessageSize        = 512
)

var upgrader = websocket.Upgrader{
	CheckOrigin:     func(r *http.Request) bool { return true },
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

func InitGame() *BoxHead {
	g := &BoxHead{
		players:        make(map[string]*Player),
		tickerInterval: DefaultTickerInterval,
		stopChan:       make(chan struct{}),
	}

	go g.broadcaster()
	return g
}

// Stop 停止广播
func (g *BoxHead) Stop() {
	close(g.stopChan)
}

func (g *BoxHead) HandleCreatePlayer(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "http://localhost:8000")
	w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS") // Allow GET and preflight OPTIONS
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type") // Allow Content-Type header

	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	log.Println("HandleCreatePlayer: 接受到一条玩家创建请求")

	name := strings.TrimSpace(r.URL.Query().Get("name"))
	if name == "" {
		writeError(w, http.StatusBadRequest, "name 参数缺失")
		return
	}

	if len(name) > 12 {
		writeError(w, http.StatusConflict, "名字长度不得超过12字符")
		return
	}

	g.mu.Lock()
	defer g.mu.Unlock()

	// 检查重名
	for _, p := range g.players {
		if p.Name == name {
			// writeError(w, http.StatusConflict, "该玩家已经存在")
			// return
			resp := map[string]interface{}{
				"code": 200,
				"data": map[string]interface{}{
					"uuid":     p.UUID,
					"username": p.Name,
				},
				"msg": "玩家已经存在",
			}
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(resp)
			return
		}
	}

	player := &Player{
		UUID: uuid.New().String(),
		Name: name,
		X:    0, // 默认出生点
		Y:    0,
	}
	g.players[player.UUID] = player

	resp := map[string]interface{}{
		"code": 200,
		"data": map[string]interface{}{
			"uuid":     player.UUID,
			"username": player.Name,
		},
	}
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
	log.Printf("玩家创建成功: %s (%s)", player.Name, player.UUID)
}

// HandleWebSocket 处理 WebSocket 连接
func (g *BoxHead) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	uuidParam := r.URL.Query().Get("uuid")
	if uuidParam == "" {
		http.Error(w, "missing uuid", http.StatusBadRequest)
		return
	}

	// 验证玩家是否存在并获取指针
	g.mu.RLock()
	player, exists := g.players[uuidParam]
	g.mu.RUnlock()

	if !exists {
		http.Error(w, "player not found", http.StatusForbidden)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}

	// 如果该玩家已有连接，先关闭旧的
	if player.Conn != nil {
		player.Conn.Close()
	}
	player.Conn = conn

	// 配置连接参数
	conn.SetReadLimit(MaxMessageSize)
	conn.SetReadDeadline(time.Now().Add(PongWait))
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(PongWait))
		return nil
	})

	log.Printf("玩家 %s (%s) 已连接", player.Name, player.UUID)

	// 启动 ping 定时器
	go g.pingLoop(player)

	// 读取消息循环（阻塞）
	g.readMessages(player)

	// 清理连接
	g.cleanupPlayer(player)
}

// pingLoop 定期发送 ping 保持连接
func (g *BoxHead) pingLoop(p *Player) {
	ticker := time.NewTicker(PingPeriod)
	defer ticker.Stop()
	for range ticker.C {
		if p.Conn == nil {
			return
		}
		if err := p.Conn.WriteControl(websocket.PingMessage, []byte{}, time.Now().Add(WriteWait)); err != nil {
			log.Printf("ping 失败 for %s: %v", p.UUID, err)
			p.Conn.Close()
			return
		}
	}
}

// readMessages 读取客户端消息并更新位置
func (g *BoxHead) readMessages(p *Player) {
	defer func() {
		if p.Conn != nil {
			p.Conn.Close()
		}
	}()

	for {
		_, message, err := p.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("读取错误 %s: %v", p.UUID, err)
			}
			break
		}
		var raw map[string]interface{}
		if err := json.Unmarshal(message, &raw); err != nil {
			log.Printf("无效JSON from %s: %v", p.UUID, err)
			continue
		}

		msgType, ok := raw["type"].(string)
		if !ok {
			log.Printf("消息缺少type字段 from %s", p.UUID)
			continue
		}
		switch msgType {
		case "join":
			// 处理加入消息（设置玩家名称和角色类型）
			cacheName := p.Name

			p.UUID = raw["uuid"].(string)
			p.Name = raw["name"].(string)
			p.CharacterType = raw["char_type"].(string)

			log.Printf("玩家 %s (%s) 已设置名称: %s, 角色: %s", cacheName, p.UUID, p.Name, p.CharacterType)
		case "move":
			x, xok := raw["x"].(float64)
			y, yok := raw["y"].(float64)
			if xok && yok {
				p.X = x
				p.Y = y
			} else {
				log.Printf("移动消息格式错误 from %s", p.UUID)
			}
		default:
			log.Printf("未知消息类型 %s from %s", msgType, p.UUID)
		}
	}
}

// cleanupPlayer 清理玩家连接并从游戏中移除
func (g *BoxHead) cleanupPlayer(p *Player) {
	g.mu.Lock()
	defer g.mu.Unlock()
	// 如果 map 中的玩家还是当前这个（确保没被重新连接覆盖），则删除
	if cur, ok := g.players[p.UUID]; ok && cur == p {
		delete(g.players, p.UUID)
		log.Printf("玩家 %s (%s) 已退出游戏", p.Name, p.UUID)
	}
	if p.Conn != nil {
		p.Conn.Close()
		p.Conn = nil
	}
}

// broadcaster 定时广播所有玩家状态
func (g *BoxHead) broadcaster() {
	ticker := time.NewTicker(g.tickerInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			g.broadcastGameState()
		case <-g.stopChan:
			return
		}
	}
}

// broadcastGameState 收集并发送游戏状态快照
func (g *BoxHead) broadcastGameState() {
	g.mu.RLock()
	if len(g.players) == 0 {
		g.mu.RUnlock()
		return
	}
	// 复制快照: 每个玩家的必要信息
	type playerSnapshot struct {
		UUID          string  `json:"uuid"`
		Name          string  `json:"name"`
		X             float64 `json:"x"`
		Y             float64 `json:"y"`
		CharacterType string  `json:"char_type"`
		Conn          *websocket.Conn
	}
	PlyaerSnapshots := make([]playerSnapshot, 0, len(g.players))
	for _, p := range g.players {
		PlyaerSnapshots = append(PlyaerSnapshots, playerSnapshot{
			UUID:          p.UUID,
			Name:          p.Name,
			X:             p.X,
			Y:             p.Y,
			CharacterType: p.CharacterType,
			Conn:          p.Conn,
		})
	}
	g.mu.RUnlock()

	// 构造广播消息
	msg := map[string]interface{}{
		"type": "game_state",
		"snapshots": map[string]interface{}{
			"Players": PlyaerSnapshots,
		},
	}
	data, err := json.Marshal(msg)
	if err != nil {
		log.Printf("序列化消息失败: %v", err)
		return
	}
	// 向每个玩家发送
	for _, ps := range PlyaerSnapshots {
		if ps.Conn == nil {
			continue
		}
		// 设置写超时
		ps.Conn.SetWriteDeadline(time.Now().Add(WriteWait))
		if err := ps.Conn.WriteMessage(websocket.TextMessage, data); err != nil {
			log.Printf("发送给 %s 失败: %v", ps.UUID, err)
			// 发送失败时关闭连接，下次广播会因 Conn == nil 而忽略
			ps.Conn.Close()
			return
		}
	}
}

// writeError 辅助函数返回 JSON 错误
func writeError(w http.ResponseWriter, status int, msg string) {
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"error": msg, "code": "400"})
}

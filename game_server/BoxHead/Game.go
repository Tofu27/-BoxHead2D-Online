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

type Pos struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// Player 游戏玩家
type Player struct {
	UUID          string  `json:"uuid"`
	Name          string  `json:"name"`
	CharacterType string  `json:"character_type"`
	X             float64 `json:"x"`
	Y             float64 `json:"y"`
	IsWalking     bool    `json:"is_walking"`
	MousePos      Pos     `json:"mouse_pos"`

	Conn        *websocket.Conn
	Send        chan []byte   // 用于串行化 WebSocket 写操作
	Done        chan struct{} // 通知 writePump 退出
	cleanupOnce sync.Once     // 确保清理逻辑只执行一次

	CreatedAt time.Time // 玩家创建时间
	Connected bool      // 是否已成功建立 WebSocket 连接
}

// BoxHead 游戏核心结构
type BoxHead struct {
	players map[string]*Player
	mu      sync.RWMutex

	tickerInterval time.Duration
	stopChan       chan struct{}
}

const (
	DefaultTickerInterval = 50 * time.Millisecond // 20Hz
	WriteWait             = 10 * time.Second
	PongWait              = 60 * time.Second    // 等待客户端 Pong 的最长时间
	PingPeriod            = (PongWait * 9) / 10 // 发送 Ping 的间隔
	MaxMessageSize        = 512

	// 僵尸玩家清理配置
	CleanZombieInterval = 30 * time.Second // 清理检查间隔
	MaxCreateAge        = 2 * time.Minute  // 创建后超过此时间仍未连接视为僵尸
)

var upgrader = websocket.Upgrader{
	CheckOrigin:     func(r *http.Request) bool { return true },
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

// InitGame 初始化游戏
func InitGame() *BoxHead {
	g := &BoxHead{
		players:        make(map[string]*Player),
		tickerInterval: DefaultTickerInterval,
		stopChan:       make(chan struct{}),
	}
	go g.broadcaster()
	go g.periodicPlayerListPrinter()
	go g.zombieCleaner() // 启动僵尸玩家清理协程
	return g
}

// Stop 停止所有后台协程
func (g *BoxHead) Stop() {
	close(g.stopChan)
}

// periodicPlayerListPrinter 每隔 30 秒打印当前玩家列表
func (g *BoxHead) periodicPlayerListPrinter() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			g.printPlayerList()
		case <-g.stopChan:
			return
		}
	}
}

func (g *BoxHead) printPlayerList() {
	g.mu.RLock()
	defer g.mu.RUnlock()
	if len(g.players) == 0 {
		log.Println("当前在线玩家：无")
		return
	}
	log.Printf("当前在线玩家 (%d)：", len(g.players))
	for _, p := range g.players {
		connStatus := "未连接"
		if p.Connected {
			connStatus = "已连接"
		}
		log.Printf("  - UUID=%s, 名称=%s, 角色=%s, 位置=(%.1f, %.1f), 状态=%s",
			p.UUID, p.Name, p.CharacterType, p.X, p.Y, connStatus)
	}
}

// HandleCreatePlayer 处理创建玩家 HTTP 请求
func (g *BoxHead) HandleCreatePlayer(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "http://localhost:8000")
	w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}
	w.Header().Set("Content-Type", "application/json")

	log.Println("HandleCreatePlayer: 接收到一条玩家创建请求")

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

	// 检查重名
	for _, p := range g.players {
		if p.Name == name {
			existingUUID := p.UUID
			existingName := p.Name
			g.mu.Unlock()

			resp := map[string]interface{}{
				"code": 200,
				"data": map[string]interface{}{
					"uuid":     existingUUID,
					"username": existingName,
				},
				"msg": "玩家已经存在",
			}
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(resp)
			return
		}
	}

	// 创建新玩家
	player := &Player{
		UUID:      uuid.New().String(),
		Name:      name,
		X:         0,
		Y:         0,
		CreatedAt: time.Now(), // 记录创建时间
		Connected: false,
	}
	g.players[player.UUID] = player
	g.mu.Unlock()

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
	g.printPlayerList()
}

// HandleWebSocket 处理 WebSocket 连接
func (g *BoxHead) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	uuidParam := r.URL.Query().Get("uuid")
	if uuidParam == "" {
		http.Error(w, "missing uuid", http.StatusBadRequest)
		return
	}

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

	// 关闭旧连接（如果存在）
	if player.Conn != nil {
		player.Conn.Close()
	}

	player.Conn = conn
	player.Connected = true // 标记已连接，避免被僵尸清理器误删

	// 初始化通道
	player.Send = make(chan []byte, 256)
	player.Done = make(chan struct{})

	conn.SetReadLimit(MaxMessageSize)
	conn.SetReadDeadline(time.Now().Add(PongWait))
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(PongWait))
		return nil
	})

	log.Printf("玩家 %s (%s) 已连接", player.Name, player.UUID)

	// 启动写协程
	go g.writePump(player)

	// 当前协程负责读消息（阻塞）
	g.readMessages(player)

	// 连接退出后清理
	g.cleanupPlayer(player)
}

// writePump 串行化发送数据到 WebSocket
func (g *BoxHead) writePump(p *Player) {
	ticker := time.NewTicker(PingPeriod)
	defer func() {
		ticker.Stop()
		p.Conn.Close()
	}()
	for {
		select {
		case <-ticker.C:
			p.Conn.SetWriteDeadline(time.Now().Add(WriteWait))
			if err := p.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		case message, ok := <-p.Send:
			if !ok {
				return
			}
			p.Conn.SetWriteDeadline(time.Now().Add(WriteWait))
			if err := p.Conn.WriteMessage(websocket.TextMessage, message); err != nil {
				return
			}
		case <-p.Done:
			return
		}
	}
}

// readMessages 读取客户端消息，更新玩家状态
func (g *BoxHead) readMessages(p *Player) {
	defer func() {
		if p.Conn != nil {
			p.Conn.Close()
		}
	}()

	// 应用层空闲超时（可选）：若超过此时间未收到任何有效消息则断开
	const appIdleTimeout = 5 * time.Minute
	idleTimer := time.NewTimer(appIdleTimeout)
	defer idleTimer.Stop()

	// 监听空闲超时
	go func() {
		<-idleTimer.C
		log.Printf("玩家 %s 应用层空闲超时，断开连接", p.UUID)
		p.Conn.Close()
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

		// 收到任何有效业务消息时重置空闲计时器
		if !idleTimer.Stop() {
			select {
			case <-idleTimer.C:
			default:
			}
		}
		idleTimer.Reset(appIdleTimeout)

		switch msgType {
		case "join":
			g.mu.Lock()
			if name, ok := raw["name"].(string); ok {
				p.Name = name
			}
			if charType, ok := raw["char_type"].(string); ok {
				p.CharacterType = charType
			}
			g.mu.Unlock()
			log.Printf("玩家 %s 信息更新: 名称=%s, 角色=%s", p.UUID, p.Name, p.CharacterType)
		case "player_game_status": // 时刻更新玩家状态

			// python客户端发送
			// {
			//     "type": "player_game_status",
			//     "x": self.player.pos.x,
			//     "y": self.player.pos.y,
			//     "is_walking": self.player.is_walking,
			//     "mouse_pos": {
			//         "x": self.mouse_pos.x,
			//         "y": self.mouse_pos.y
			//     },
			// }

			g.mu.Lock()
			x, xok := raw["x"].(float64)
			y, yok := raw["y"].(float64)
			if xok && yok {
				p.X = x
				p.Y = y
			}

			if IsWalking, ok := raw["is_walking"].(bool); ok {
				p.IsWalking = IsWalking
			}

			if MousePos, ok := raw["mouse_pos"].(map[string]interface{}); ok {
				var pos Pos

				if mx, ok := MousePos["x"].(float64); ok {
					pos.X = mx
				}

				if my, ok := MousePos["y"].(float64); ok {
					pos.Y = my
				}

				p.MousePos = pos

			} else {
				println("接受鼠标信息失败", raw)
				panic("失败")
			}

			g.mu.Unlock()
		default:
			log.Printf("未知消息类型 %s from %s", msgType, p.UUID)
		}
	}
}

// cleanupPlayer 从游戏中移除玩家
func (g *BoxHead) cleanupPlayer(p *Player) {
	p.cleanupOnce.Do(func() {
		g.mu.Lock()
		if cur, ok := g.players[p.UUID]; ok && cur == p {
			delete(g.players, p.UUID)
		}
		g.mu.Unlock()

		// 通知写协程停止
		close(p.Done)

		log.Printf("玩家 %s (%s) 已退出游戏", p.Name, p.UUID)
		g.printPlayerList()
	})
}

// zombieCleaner 定期清理创建后长时间未建立连接的玩家
func (g *BoxHead) zombieCleaner() {
	ticker := time.NewTicker(CleanZombieInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			g.cleanZombiePlayers()
		case <-g.stopChan:
			return
		}
	}
}

func (g *BoxHead) cleanZombiePlayers() {
	g.mu.Lock()
	defer g.mu.Unlock()

	now := time.Now()
	for uuid, p := range g.players {
		if !p.Connected && now.Sub(p.CreatedAt) > MaxCreateAge {
			log.Printf("清理未连接僵尸玩家: %s (%s), 已存在 %v", p.Name, uuid, now.Sub(p.CreatedAt))
			delete(g.players, uuid)
		}
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

	type playerSnapshot struct {
		UUID          string
		Name          string
		X             float64
		Y             float64
		IsWalking     bool
		MousePos      Pos
		CharacterType string
		Send          chan []byte
		Done          <-chan struct{}
	}
	snapshots := make([]playerSnapshot, 0, len(g.players))
	for _, p := range g.players {
		if !p.Connected {
			continue
		}

		snapshots = append(snapshots, playerSnapshot{
			UUID:          p.UUID,
			Name:          p.Name,
			X:             p.X,
			Y:             p.Y,
			IsWalking:     p.IsWalking,
			MousePos:      p.MousePos,
			CharacterType: p.CharacterType,
			Send:          p.Send,
			Done:          p.Done,
		})
	}
	g.mu.RUnlock()

	playersForMsg := make([]map[string]interface{}, len(snapshots))
	for i, ps := range snapshots {
		playersForMsg[i] = map[string]interface{}{
			"uuid":       ps.UUID,
			"name":       ps.Name,
			"x":          ps.X,
			"y":          ps.Y,
			"is_walking": ps.IsWalking,
			"mouse_pos":  ps.MousePos,
			"char_type":  ps.CharacterType,
		}
	}
	msg := map[string]interface{}{
		"type":      "game_state",
		"snapshots": map[string]interface{}{"Players": playersForMsg},
	}
	data, err := json.Marshal(msg)
	if err != nil {
		log.Printf("序列化消息失败: %v", err)
		return
	}

	for _, ps := range snapshots {
		select {
		case ps.Send <- data:
		case <-ps.Done:
		default:
		}
	}
}

// writeError 返回 JSON 格式错误
func writeError(w http.ResponseWriter, status int, msg string) {
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"error": msg, "code": "400"})
}

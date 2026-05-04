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
	IsAttack      bool    `json:"is_attack"`
	MousePos      Pos     `json:"mouse_pos"`

	Conn        *websocket.Conn
	Send        chan []byte   // 串行化 WebSocket 写操作
	Done        chan struct{} // 通知 writePump 退出
	cleanupOnce sync.Once     // 确保清理逻辑只执行一次

	CreatedAt time.Time // 创建时间
	Connected bool      // 是否已建立 WebSocket 连接
}

// BoxHead 游戏核心
type BoxHead struct {
	players map[string]*Player
	mu      sync.RWMutex

	tickerInterval time.Duration
	stopChan       chan struct{}
}

const (
	DefaultTickerInterval = 50 * time.Millisecond
	WriteWait             = 10 * time.Second
	PongWait              = 60 * time.Second
	PingPeriod            = (PongWait * 9) / 10
	MaxMessageSize        = 512

	CleanZombieInterval = 30 * time.Second
	MaxCreateAge        = 2 * time.Minute
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
	go g.zombieCleaner()
	return g
}

func (g *BoxHead) Stop() {
	close(g.stopChan)
}

// ---------- 玩家列表打印 ----------
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
		status := "未连接"
		if p.Connected {
			status = "已连接"
		}
		log.Printf("  - UUID=%s, 名称=%s, 角色=%s, 位置=(%.1f, %.1f), 行走=%v, 鼠标=(%.1f, %.1f), %s",
			p.UUID, p.Name, p.CharacterType, p.X, p.Y, p.IsWalking, p.MousePos.X, p.MousePos.Y, status)
	}
}

// ---------- HTTP 创建玩家 ----------
func (g *BoxHead) HandleCreatePlayer(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "http://localhost:8000")
	w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}
	w.Header().Set("Content-Type", "application/json")

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
	// 重名检查
	for _, p := range g.players {
		if p.Name == name {

			if p.Connected {
				writeError(w, http.StatusConflict, "玩家已经在游戏中...")
				return
			}

			existingUUID := p.UUID
			existingName := p.Name
			g.mu.Unlock()
			json.NewEncoder(w).Encode(map[string]interface{}{
				"code": 200,
				"data": map[string]interface{}{
					"uuid":     existingUUID,
					"username": existingName,
				},
				"msg": "玩家已经存在",
			})
			return
		}
	}

	player := &Player{
		UUID:      uuid.New().String(),
		Name:      name,
		X:         0,
		Y:         0,
		CreatedAt: time.Now(),
		Connected: false,
	}
	g.players[player.UUID] = player
	g.mu.Unlock()

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"code": 200,
		"data": map[string]interface{}{
			"uuid":     player.UUID,
			"username": player.Name,
		},
	})
	log.Printf("玩家创建成功: %s (%s)", player.Name, player.UUID)
	g.printPlayerList()
}

// ---------- WebSocket 连接 ----------
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

	// 初始化连接相关字段（加锁保护，防止广播协程读到半初始化状态）
	g.mu.Lock()
	player.Conn = conn
	player.Connected = true
	player.Send = make(chan []byte, 256)
	player.Done = make(chan struct{})
	g.mu.Unlock()

	conn.SetReadLimit(MaxMessageSize)
	conn.SetReadDeadline(time.Now().Add(PongWait))
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(PongWait))
		return nil
	})

	log.Printf("玩家 %s (%s) 已连接", player.Name, player.UUID)

	go g.writePump(player)
	g.readMessages(player)  // 阻塞
	g.cleanupPlayer(player) // 连接退出后清理
}

// ---------- 写协程 ----------
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

// ---------- 读协程 ----------
func (g *BoxHead) readMessages(p *Player) {
	defer func() {
		if p.Conn != nil {
			p.Conn.Close()
		}
	}()

	const appIdleTimeout = 5 * time.Minute
	idleTimer := time.NewTimer(appIdleTimeout)
	defer idleTimer.Stop()

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

		// 重置应用层空闲计时器
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
			if ct, ok := raw["char_type"].(string); ok {
				p.CharacterType = ct
			}
			g.mu.Unlock()
			log.Printf("玩家 %s 信息更新: 名称=%s, 角色=%s", p.UUID, p.Name, p.CharacterType)

		case "player_game_status":
			g.mu.Lock()
			if x, ok := raw["x"].(float64); ok {
				p.X = x
			}
			if y, ok := raw["y"].(float64); ok {
				p.Y = y
			}
			if walking, ok := raw["is_walking"].(bool); ok {
				p.IsWalking = walking
			}

			if attack, ok := raw["is_attack"].(bool); ok {
				p.IsAttack = attack
			}

			if mpRaw, ok := raw["mouse_pos"].(map[string]interface{}); ok {
				var pos Pos
				if mx, ok := mpRaw["x"].(float64); ok {
					pos.X = mx
				}
				if my, ok := mpRaw["y"].(float64); ok {
					pos.Y = my
				}
				p.MousePos = pos
			}

			g.mu.Unlock()

		default:
			log.Printf("未知消息类型 %s from %s", msgType, p.UUID)
		}
	}
}

// ---------- 清理玩家 ----------
func (g *BoxHead) cleanupPlayer(p *Player) {
	p.cleanupOnce.Do(func() {
		g.mu.Lock()
		if cur, ok := g.players[p.UUID]; ok && cur == p {
			delete(g.players, p.UUID)
		}
		g.mu.Unlock()

		close(p.Done) // 通知 writePump 退出

		log.Printf("玩家 %s (%s) 已退出游戏", p.Name, p.UUID)
		g.printPlayerList()
	})
}

// ---------- 僵尸清理 ----------
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

// ---------- 广播 ----------
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
		IsAttack      bool
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
			IsAttack:      p.IsAttack,
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
			"is_attack":  ps.IsAttack,
		}
	}
	msg := map[string]interface{}{
		"type":      "game_state",
		"snapshots": map[string]interface{}{"Players": playersForMsg},
	}

	log.Println("[Game] 广播游戏状态", msg)
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

// ---------- 工具 ----------
func writeError(w http.ResponseWriter, status int, msg string) {
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"error": msg, "code": "400"})
}

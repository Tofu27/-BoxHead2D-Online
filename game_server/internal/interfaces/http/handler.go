package http

import (
	"encoding/json"
	"game_server/internal/application/boxhead"
	"log"
	"net/http"
	"strings"
	"sync"
	"time"

	domain "game_server/internal/domain/minigame/boxhead"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

// ---------- 配置常量 ----------
const (
	writeWait      = 10 * time.Second    // 写超时
	pongWait       = 60 * time.Second    // 等待Pong的最长时间
	pingPeriod     = (pongWait * 9) / 10 // Ping间隔（必须小于pongWait）
	maxMessageSize = 512                 // 最大消息体大小
)

// WebSocket升级器
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin:     func(r *http.Request) bool { return true }, // 允许所有来源（开发环境）
}

// Handler HTTP处理器，持有房间和命令处理器的引用
type Handler struct {
	room       *domain.Room
	cmdHandler *boxhead.CommandHandler
}

// NewHandler 创建HTTP处理器实例
func NewHandler(room *domain.Room, cmdHandler *boxhead.CommandHandler) *Handler {
	return &Handler{room: room, cmdHandler: cmdHandler}
}

// HandleCreatePlayer 处理HTTP GET /create?name=xxx
// 创建一个新玩家，将其加入房间，返回UUID和名称
func (h *Handler) HandleCreatePlayer(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")

	// 获取name参数
	name := strings.TrimSpace(r.URL.Query().Get("name"))
	if name == "" {
		writeError(w, http.StatusBadRequest, "name 参数缺失")
		return
	}
	if len(name) > 12 {
		writeError(w, http.StatusConflict, "名字长度不得超过12字符")
		return
	}

	// 重名校验：需要和房间数据交互，我们暂时使用简单方法：遍历房间玩家（直接读房间的 players map？不行，因为房间在另一个 goroutine 运行）
	// 正确做法是通过命令请求/响应模式，但为简化，这里给一个同步校验接口（要求 Room 提供同步查询方法）
	// 我们给 Room 添加一个 NameCheck 方法，通过 channel 同步返回。
	// 暂且支持同步重名检查，需要修改 Room 增加 requestCh。
	// 但为了快速运行，先不实现重名校验，直接创建。后续可加。
	// 这里我们调用 Room 的同步查询（需要补充），目前暂时跳过重名检查。

	// 创建玩家实体（此时状态为空，位置0,0）
	player := &domain.PlayerState{
		UUID:      uuid.New().String(),
		Name:      name,
		CreatedAt: time.Now(),
	}
	// 通过命令处理器将玩家加入房间（异步，通过channel）
	h.cmdHandler.CreatePlayer(player)

	// 返回成功响应
	resp := map[string]interface{}{
		"code": 200,
		"data": map[string]interface{}{
			"uuid":     player.UUID,
			"username": player.Name,
		},
	}
	json.NewEncoder(w).Encode(resp)
	log.Printf("玩家创建成功: %s (%s)", player.Name, player.UUID)
}

// HandleWebSocket 处理WebSocket升级连接 /ws?uuid=xxx
// 每个连接会创建一个独立的Session，负责该客户的收发。
// 该函数会阻塞在此连接上（因为Session.run()会等待读循环结束），
// 但每个连接由net/http自动分配独立的goroutine，所以不会互相影响。
func (h *Handler) HandleWebSocket(w http.ResponseWriter, r *http.Request) {

	uuidParam := r.URL.Query().Get("uuid")
	if uuidParam == "" {
		http.Error(w, "missing uuid", http.StatusBadRequest)
		return
	}

	// 升级HTTP连接为WebSocket
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}

	// 为这个连接创建Session（封装了读写协程和缓冲通道）
	session := newSession(uuidParam, conn, h.cmdHandler)

	// 启动Session（此调用会阻塞，直到WebSocket连接断开）
	session.run()
}

// session 网络会话，负责WebSocket的收发、心跳和消息解析
type session struct {
	uuid       string                  // 对应玩家UUID
	conn       *websocket.Conn         // 底层WebSocket连接
	sendCh     chan []byte             // 发送缓冲通道（写协程从这里取数据发送）
	doneCh     chan struct{}           // 通知写协程退出的信号
	closeOnce  sync.Once               // 确保清理操作只执行一次
	cmdHandler *boxhead.CommandHandler // 命令处理器，用于将消息转给房间
}

// newSession 创建一个新会话
func newSession(uuid string, conn *websocket.Conn, cmdHandler *boxhead.CommandHandler) *session {
	return &session{
		uuid:       uuid,
		conn:       conn,
		sendCh:     make(chan []byte, 256), // 带缓冲，避免阻塞房间广播
		doneCh:     make(chan struct{}),
		cmdHandler: cmdHandler,
	}
}

// run 启动会话（绑定发送通道，启动读写协程）
func (s *session) run() {
	// 1. 告知房间：这个玩家对应的发送通道是 s.sendCh
	//    这样房间广播时就知道往哪里发消息。
	s.cmdHandler.BindSendCh(s.uuid, s.sendCh)

	// 2. 启动写协程（另一个goroutine，专门负责从sendCh读取并写入WebSocket）
	go s.writePump()

	// 3. 开始读循环（阻塞在当前goroutine，直到连接断开）
	s.readPump()

	// 4. 读循环退出（连接断开或错误），执行清理：关闭写协程、通知房间
	s.closeOnce.Do(func() {
		close(s.doneCh)                // 通知writePump退出
		s.conn.Close()                 // 关闭WebSocket连接
		s.cmdHandler.LeaveRoom(s.uuid) // 通知房间从玩家列表中移除
	})
}

// readPump 从WebSocket连接读取消息，解析后发送命令给房间
func (s *session) readPump() {
	defer s.conn.Close() // 确保退出时关闭连接

	// 设置连接读取限制和Pong处理器（用于WebSocket协议层心跳）
	s.conn.SetReadLimit(maxMessageSize)
	s.conn.SetReadDeadline(time.Now().Add(pongWait))
	s.conn.SetPongHandler(func(string) error {
		s.conn.SetReadDeadline(time.Now().Add(pongWait))
		return nil
	})

	// 应用层空闲超时：5分钟内没有收到任何消息，则认为客户端已死，主动断开
	idleTimer := time.NewTimer(5 * time.Minute)
	defer idleTimer.Stop()
	go func() {
		<-idleTimer.C
		log.Printf("玩家 %s 应用层空闲超时", s.uuid)
		s.conn.Close()
	}()

	for {
		// 读取一条消息
		_, message, err := s.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("读取错误 %s: %v", s.uuid, err)
			}
			break
		}

		// 收到任何消息，重置空闲计时器
		if !idleTimer.Stop() {
			select {
			case <-idleTimer.C:
			default:
			}
		}
		idleTimer.Reset(5 * time.Minute)

		// 解析消息
		var raw map[string]interface{}
		if err := json.Unmarshal(message, &raw); err != nil {
			log.Printf("无效JSON from %s: %v", s.uuid, err)
			continue
		}

		// 提取消息类型
		msgType, ok := raw["type"].(string)
		if !ok {
			log.Printf("消息缺少 type 字段 from %s", s.uuid)
			continue
		}

		// 根据消息类型分派
		switch msgType {
		case "join":
			// 可更新名字和角色，暂时简单忽略
			s.cmdHandler.JoinRoom(raw)
		case "player_game_status":
			// 玩家状态更新（坐标、动作等）
			s.cmdHandler.UpdatePlayer(s.uuid, raw)
		default:
			log.Printf("未知消息类型 %s from %s", msgType, s.uuid)
		}
	}
}

// writePump 从sendCh取出数据，写入WebSocket连接
func (s *session) writePump() {
	// 定时发送Ping帧，保持连接活性
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		s.conn.Close()
	}()
	for {
		select {
		case <-ticker.C:
			// 发送Ping
			s.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := s.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		case data, ok := <-s.sendCh:
			if !ok {
				// sendCh已关闭，退出
				return
			}
			// 写消息到WebSocket
			s.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := s.conn.WriteMessage(websocket.TextMessage, data); err != nil {
				return
			}
		case <-s.doneCh:
			// 收到退出信号（由run中的closeOnce触发）
			return
		}
	}
}

// writeError 工具函数，返回JSON格式的错误响应
func writeError(w http.ResponseWriter, status int, msg string) {
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"error": msg, "code": "400"})
}

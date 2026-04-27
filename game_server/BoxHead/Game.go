package boxhead

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"strings"

	"github.com/google/uuid"
)

type Player struct {
	UUID string `json:"uuid"`
	Name string `json:"name"`
}

type BoxHead struct {
	Players []Player `json:"players"`
}

func InitGame() *BoxHead {
	g := &BoxHead{}

	return g
}

func (boxHead *BoxHead) HandleCreatePlayer(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "http://localhost:8000")
	w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS") // Allow GET and preflight OPTIONS
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type") // Allow Content-Type header

	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	log.Println("HandleCreatePlayer: 接受到一条玩家创建请求")

	name := r.URL.Query().Get("name")
	name = strings.TrimSpace(name)
	if name == "" {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "name 参数不存在",
			"code":  "400",
		})
		log.Println("HandleCreatePlayer: name 参数不存在")
		return
	}

	if len(name) > 12 {
		w.WriteHeader(http.StatusConflict)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "名字长度不得超过12字符",
			"code":  "400",
		})
		log.Printf("HandleCreatePlayer: 名字长度不得超过12字符 - {%v}", name)
		return
	}

	UUID, err := boxHead.CreatePlayer(name)
	if err != nil {
		w.WriteHeader(http.StatusConflict)
		json.NewEncoder(w).Encode(map[string]string{
			"error": err.Error(),
			"code":  "400",
		})
		return
	}

	response := map[string]interface{}{
		"uuid":     UUID,
		"username": name,
		"code":     200,
	}

	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Printf("HandleCreatePlayer: 错误的JSON响应: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}
	log.Printf("HandleCreatePlayer: 玩家创建成功 - {%v}", response)
}

func (boxHead *BoxHead) CreatePlayer(name string) (string, error) {
	var player Player

	for _, p := range boxHead.Players {
		if p.Name == name {
			return "", errors.New("该玩家已经存在")
		}
	}

	player.UUID = uuid.New().String()

	return player.UUID, nil
}

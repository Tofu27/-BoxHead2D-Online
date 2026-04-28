import arcade
from views.base_view import FadingView
from utils.utils import Utils
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from entities.character import Player, Rambo, Redbit
from entities.room import Room
from views.base_view import CAMERA_SPEED
from core.config import get_root_dir

import time
import threading
from network.wsClient import GameWebSocketClient


ROOT_DIR = get_root_dir()

class GameView(FadingView):
    """Main game view."""

    def __init__(self):
        super().__init__()

        self.ws_client = None
        self.other_players = {}   # {player_id: {"sprite":..., "x":..., "y":...}}
        self.last_send_time = 0
        self.send_interval = 0.05  # 20Hz，与服务器 tick 频率接近
        self._pending_players = []
        self._pending_lock = threading.Lock()
        self._last_ws_print_time = 0
        self._ws_print_interval = 2.0  # 每2秒打印一次


        self.mouse_x = None
        self.mouse_y = None
        self.mouse_pos = Vec2(0, 0)
        self.mouse_sprite = arcade.Sprite("public/graphics/ui/Cursor.png")
        self.physics_engine = None
        self.manager = None

        # Sprite lists
        self.wall_list = None
        self.player = None
        
        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        self.camera_sprites = arcade.Camera(self.w, self.h)
        self.camera_gui = arcade.Camera(self.w, self.h)

    def setup(self, player_meta: any, map: Room) -> None:
        """Set up the game and initialize the variables."""

        player:Player = player_meta['player']
        
        print("玩家信息", player_meta['uuid'])
        print("地图信息", map)

        # 启动 WebSocket 客户端
        self.ws_client = GameWebSocketClient(
            server_url="ws://localhost:8888/ws",
            player_uuid = player_meta['uuid'],
            on_game_state=self.on_ws_game_state,
            on_connected=self.on_ws_connected,   # 连接成功后发送 join
            on_error=self.on_ws_error,
            on_close=self.on_ws_close
        )
        self.ws_client.start()


        # Play game BGM
        self.window.play_game_music(1)

        # Create the physics engine
        damping = 0.01
        gravity = (0, 0)
        self.physics_engine = PymunkPhysicsEngine(gravity, damping)

        
        # Game room setup
        self.room = map()
        
        # Set up the player
        self.player = player(
            float(self.room.width / 2), float(self.room.height / 2), self.physics_engine)
        
        self.player.register_mouse_pos(self.mouse_pos)
        self.player.setGameInfo({
            "uuid": player_meta['uuid'],
            "username": player_meta['name']
        })


        # Set up the shop
        # self.shop = item.Shop(self.player)

        self.physics_engine.add_sprite(
            self.player,
            friction=0,
            moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.001,
            collision_type="player",
            elasticity=0.1
        )
        self.physics_engine.add_sprite_list(
            self.room.walls,
            friction=0,
            collision_type="wall",
            body_type=PymunkPhysicsEngine.STATIC,
        )


    def on_ws_game_state(self, players_list):
        """服务器推送所有玩家状态"""
        """子线程回调，只存储数据"""

        now = time.time()
        if now - self._last_ws_print_time >= self._ws_print_interval:
            print("ws消息 (节流后):", players_list)
            self._last_ws_print_time = now
            
        with self._pending_lock:
            self._pending_players = players_list  # 替换为新快照

    def on_ws_connected(self):
        """WebSocket 连接成功后调用（运行在子线程）"""
        join_msg = {
            "type": "join",
            "uuid": self.player.uuid,
            "name": self.player.username,
            "char_type": self.player.char_type
        }
        self.ws_client.send_json(join_msg)

    def on_ws_error(self, err):
        print("WS 报错:", err)

    def on_ws_close(self):
        print("WS 关闭")

    def on_draw(self) -> None:
        self.clear()
        self.camera_sprites.use() # 世界相机，绘制场景、玩家、敌人

        self.room.draw_ground()
        self.room.draw_walls()
        self.player.draw()

        # 绘制其他玩家
        for pid, data in self.other_players.items():
            data["sprite"].draw()
            arcade.draw_text(data["name"],
                data["sprite"].center_x,
                data["sprite"].center_y + 30,
                arcade.color.WHITE, 12, anchor_x="center")

        self.camera_gui.use() # 切换 GUi相机，绘制准许，信息UI

        # Mouse cursor
        if self.mouse_x and self.mouse_y:
            self.mouse_sprite.draw()

    def on_update(self, delta_time) -> None:
        # 先处理待决的网络数据
        with self._pending_lock:
            if self._pending_players:
                self._sync_other_players(self._pending_players)
                self._pending_players = []

        self.physics_engine.step()
        # Update player
        self.player.update()
        self.scroll_to_player()

        
        # 发送本地玩家坐标给服务器
        self._send_move_if_needed()
        # 平滑更新其他玩家的显示位置
        self._update_other_players_positions()

    def _sync_other_players(self, players_list):
        """在主线程中安全地更新其他玩家精灵"""
        current_ids = set(self.other_players.keys())
        received_ids = set()

        for p in players_list:
            pid = p["uuid"]
            if pid == self.player.uuid:   # 跳过自己
                continue
            received_ids.add(pid)

            if pid not in self.other_players:
                # 新玩家：根据 char_type 创建精灵
                sprite = self._create_player_sprite(p.get("char_type", "Player"))
                self.other_players[pid] = {
                    "sprite": sprite,
                    "name": p.get("name", ""),
                    "target_x": p["x"],
                    "target_y": p["y"],
                    "current_x": p["x"],
                    "current_y": p["y"]
                }
            else:
                # 已存在玩家：更新目标位置
                self.other_players[pid]["target_x"] = p["x"]
                self.other_players[pid]["target_y"] = p["y"]
                self.other_players[pid]["name"] = p["name"]

        # 移除离开的玩家
        for pid in current_ids - received_ids:
            if pid in self.other_players:
                self.other_players[pid]["sprite"].remove_from_sprite_lists()
                del self.other_players[pid]


    def _create_player_sprite(self, char_type: str) -> arcade.Sprite:
        """根据角色类型创建精灵（仅用于其他玩家）"""
        # 简易实现：你可以使用更复杂的动画精灵，这里只是示例
        if char_type == "Player":
            texture = "public/graphics/character/Player.png"
        elif char_type == "Rambo":
            texture = "public/graphics/character/Rambo.png"
        elif char_type == "Redbit":
            texture = "public/graphics/character/Redbit.png"
        else:
            texture = ":resources:images/enemies/slimeBlue.png"
        sprite = arcade.Sprite(texture, scale=1.0)
        return sprite


    def _send_move_if_needed(self):
        now = time.time()
        if now-self.last_send_time>=self.send_interval:
            self.ws_client.send_json({"type": "move", "x": self.player.pos.x, "y": self.player.pos.y})
            self.last_send_time = now

    def _update_other_players_positions(self):
        """使用线性插值平滑移动到目标位置，避免抖动"""
        for data in self.other_players.values():
            # 插值系数 0.2 可根据网络质量调整
            data["current_x"] += (data["target_x"] - data["current_x"]) * 0.2
            data["current_y"] += (data["target_y"] - data["current_y"]) * 0.2
            data["sprite"].center_x = data["current_x"]
            data["sprite"].center_y = data["current_y"]

    def on_key_press(self, key, modifiers) -> None:
        """Called whenever a key is pressed."""

        if key == arcade.key.W:
            self.player.move_up = True
        elif key == arcade.key.S:
            self.player.move_down = True
        elif key == arcade.key.A:
            self.player.move_left = True
        elif key == arcade.key.D:
            self.player.move_right = True

    def on_key_release(self, key, modifiers) -> None:

        if key == arcade.key.W:
            self.player.move_up = False
        elif key == arcade.key.S:
            self.player.move_down = False
        elif key == arcade.key.A:
            self.player.move_left = False
        elif key == arcade.key.D:
            self.player.move_right = False

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        """Mouse movement."""
        self.mouse_x = x
        self.mouse_y = y
        self.mouse_pos.x = self.mouse_x + self.camera_sprites.position.x
        self.mouse_pos.y = self.mouse_y + self.camera_sprites.position.y
        self.mouse_sprite.center_x = self.mouse_x
        self.mouse_sprite.center_y = self.mouse_y

    def scroll_to_player(self) -> None:
        x = self.player.pos.x - float(self.w / 2)
        if self.player.pos.x < float(self.w / 2):
            x = 0
        elif self.player.pos.x > float(self.room.width - self.w / 2):
            x = float(self.room.width - self.w)

        y = self.player.pos.y - float(self.h / 2)
        if self.player.pos.y < float(self.h / 2):
            y = 0
        elif self.player.pos.y > float(self.room.height - self.h / 2):
            y = float(self.room.height - self.h)

        self.camera_sprites.move_to((x, y), CAMERA_SPEED)

    def resize_camera(self, width, height) -> None:
        self.w = width
        self.h = height
        self.camera_sprites.resize(width, height)
        self.camera_gui.resize(width, height)

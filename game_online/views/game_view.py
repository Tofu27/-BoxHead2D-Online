import arcade
from views.base_view import FadingView
from utils.utils import Utils
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from entities.character import Player, Rambo, Redbit
from entities.room import Room
from views.base_view import CAMERA_SPEED

import time
import threading
from network.wsClient import GameWebSocketClient


class GameView(FadingView):
    """主游戏视图。"""

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
        self.player_bullet_list = None
        
        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        self.camera_sprites = arcade.Camera(self.w, self.h)
        self.camera_gui = arcade.Camera(self.w, self.h)

    def setup(self, player_meta: any, map: Room) -> None:
        """
        初始化游戏。
        player_meta 应包含: player (类), uuid, name
        room_class 是房间类（可调用返回 Room 实例）
        """

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


        # GameObject lists
        self.wall_list = arcade.SpriteList()
        self.player_bullet_list = arcade.SpriteList()

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
        self.player.uuid = player_meta['uuid']
        self.player.username = player_meta['name']


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
        """服务器推送所有玩家状态（子线程回调，仅存储数据）"""

        now = time.time()
        if now - self._last_ws_print_time >= self._ws_print_interval:
            print("ws消息 (节流):", players_list)
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
        for data in self.other_players.values():
            data["player"].draw()  # 自动绘制身体、脚、武器等

        # 绘制子弹
        self.player_bullet_list.draw()

        self.camera_gui.use() # 切换 GUi相机，绘制准许，信息UI

        # 鼠标准星
        if self.mouse_x and self.mouse_y:
            self.mouse_sprite.draw()

    def on_update(self, delta_time) -> None:
        # 先处理待决的网络数据
        with self._pending_lock:
            if self._pending_players:
                self._sync_other_players(self._pending_players)
                self._pending_players = []

        self.physics_engine.step()
        self.player.update()
        self.update_player_attack()
        self.scroll_to_player()

        
        # 发送本地玩家状态给服务器
        self._send_status_if_needed()
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
            x, y = p["x"], p["y"]

            if pid not in self.other_players:
                # 新玩家
                instance = self._create_other_player(p.get("char_type", "Player"), x, y)
                instance.username = p.get("name", "")
                self.other_players[pid] = {
                    "player": instance,
                    "target_x": p["x"],
                    "target_y": p["y"],
                    "current_x": p["x"],
                    "current_y": p["y"]
                }
            else:
                # 已存在玩家：更新目标位置
                data = self.other_players[pid]
                data["target_x"] = x
                data["target_y"] = y
                player = data["player"]
                player.username = p.get("name", "")
                player.is_walking = p.get("is_walking", False)
                mouse_pos = p.get("mouse_pos", {})
                player.remote_mouse_pos = Vec2(mouse_pos.get('x', 0), mouse_pos.get('y', 0))

        # 移除离开的玩家
        for pid in current_ids - received_ids:
            if pid in self.other_players:
                self.physics_engine.remove_sprite(self.other_players[pid]["player"])
                del self.other_players[pid]

    def _create_other_player(self, char_type: str, x: float = 0, y: float = 0) -> Player:
        """根据角色类型创建其他玩家的完整角色实例（无物理引擎）"""
        class_map = {
            "Player": Player,
            "Rambo": Rambo,
            "Redbit": Redbit,
        }
        cls = class_map.get(char_type, Player)
        # 物理引擎传 None，避免不必要的物理模拟
        instance = cls(x, y, physics_engine=None)
        # 可选：设置初始位置（稍后会通过 target_x/target_y 覆盖）
        instance.center_x = x
        instance.center_y = y
        instance.is_remote = True
        
        # 手动添加为运动学物体，只参与碰撞，不主动移动
        self.physics_engine.add_sprite(
            instance,
            friction=0,
            moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
            damping=0,
            collision_type="player",
            elasticity=0.1,
            body_type=PymunkPhysicsEngine.KINEMATIC,   # 关键！
        )

        return instance

    def _send_status_if_needed(self):
        now = time.time()
        if now - self.last_send_time >= self.send_interval:
            self.ws_client.send_json({
                "type": "player_game_status", 
                "x": self.player.pos.x, 
                "y": self.player.pos.y,
                "is_walking": self.player.is_walking,
                "mouse_pos": {
                    "x": self.mouse_pos.x,
                    "y": self.mouse_pos.y
                },
            })
            self.last_send_time = now

    def _update_other_players_positions(self):
        for data in self.other_players.values():
            # 线性插值
            data["current_x"] += (data["target_x"] - data["current_x"]) * 0.2
            data["current_y"] += (data["target_y"] - data["current_y"]) * 0.2
            player_obj = data["player"]

            # player_obj.center_x = data["current_x"]
            # player_obj.center_y = data["current_y"]

            # 🔥 关键：用物理引擎方法移动整个物体（精灵+碰撞体）
            self.physics_engine.set_position(
                player_obj,
                (data["current_x"], data["current_y"])
            )

            # 调用 update()
            player_obj.update()



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
        self.mouse_sprite.center_x = x
        self.mouse_sprite.center_y = y

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = True
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.player.use_skill()

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

    def update_player_attack(self) -> None:
        if self.player.is_attack:
            # 冷却时间满了
            if self.player.cd == self.player.cd_max:
                self.player.cd = 0

            if self.player.cd == 0:

                # 如果武器是枪
                if self.player.current_weapon.is_gun:

                    # 创建子弹
                    bullets = self.player.attack()

                    self.player.current_weapon.play_sound(
                        self.window.effect_volume)
                    
                    for bullet in bullets:
                        bullet.change_x = bullet.aim.x
                        bullet.change_y = bullet.aim.y
                        self.player_bullet_list.append(bullet)
            
        # 冷却中
        self.player.cd = min(self.player.cd + 1, self.player.cd_max)
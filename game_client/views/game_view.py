
import time
from typing import Any

import arcade
import queue
from attr import dataclass
from pyglet.math import Vec2
from views.base_view import FadingView
from core.systems.world_system import WorldSystem
from entities.character import CreatePlayer
from core.systems.remote_player_system import RemotePlayerManager
from core.systems.camera_system import CameraSystem
from core.systems.combat_system import CombatSystem
from core.systems.bullet_system import BulletSystem
from core.systems.network_system import NetworkSystem
from network.ws_client import GameWebSocketClient

@dataclass
class NetworkMessage:
    type: str               # "game_state", "game_state_diff", "player_leave", "reset"
    payload: Any = None     # 相应数据
    
class GameView(FadingView):
    def __init__(self):
        super().__init__()
        self.w, self.h = self.window.get_size()

        # 系统实例
        self.world_sys = None
        self.camera_sys = None
        self.remote_sys = None
        self.combat_sys = None
        self.bullet_sys = None
        self.network_sys = None

        # 本地玩家
        self.player = None
        self.mouse_sprite = arcade.Sprite("public/graphics/ui/Cursor.png")
        self.camera_sprites = arcade.Camera(self.w, self.h)
        self.camera_gui = arcade.Camera(self.w, self.h)

        # ----- 鼠标和 UI -----
        self.mouse_x = None                        # 鼠标在窗口中的 X 坐标
        self.mouse_y = None                        # 鼠标在窗口中的 Y 坐标
        self.mouse_pos = Vec2(0, 0)

        # 网络
        self.ws_client = None
        self.message_queue = queue.Queue()
        self.last_send = 0
        self.send_interval = 0.05


    def setup(self, player_meta, map):
        # 初始化世界系统
        self.world_sys = WorldSystem()
        self.world_sys.setup(map, gravity=(0, 0), damping=0.01)

        # 创建本地玩家
        self.player = CreatePlayer(
            player_meta['player_char_type'],
            self.world_sys.room.width / 2,
            self.world_sys.room.height / 2,
            self.world_sys.physics_engine,
            is_remote=False
        )
        self.player.uuid = player_meta['uuid']
        self.player.username = player_meta['name']
        self.player.register_mouse_pos(self.mouse_pos)
        self.world_sys.add_sprite(self.player,
                        collision_type="player",
                        friction=0,
                        moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
                        damping=0.001,
                        elasticity=0.1)


        # 创建远程玩家系统（管理远程实体）
        self.remote_sys = RemotePlayerManager(
            self.world_sys.physics_engine
        )

        
        self.camera_sys = CameraSystem(self.camera_sprites)
        self.combat_sys = CombatSystem(self.world_sys, self.remote_sys, self.window)
        self.bullet_sys = BulletSystem(self.world_sys)
        self.network_sys = NetworkSystem(self.message_queue, self.remote_sys, self.player.uuid)

        # 5. 启动网络连接
        self.ws_client = GameWebSocketClient(
            serverUrl="ws://localhost:8888/ws",
            playerUUID=self.player.uuid,
            onGameMsg=self._enqueue_ws_message,
            onConnected=self._on_ws_connected,
            onError=self._on_ws_error,
            onClose=self._on_ws_close
        )
        self.ws_client.Start()
        
        # 播放音乐...
        self.window.play_game_music(1)

    def on_update(self, delta_time):
        #消费网络消息，同步远程玩家
        self.network_sys.update()

        # 物理步进
        self.world_sys.step()

        # 本地玩家逻辑（移动、动画）
        self.player.update()
        
        # 远程玩家插值更新（不含攻击）
        self.remote_sys.update()

        
        # 战斗处理（攻击、生成子弹）
        self.combat_sys.update_local(self.player)
        self.combat_sys.update_remote()


        # 子弹更新（生命、碰撞）
        self.bullet_sys.update()


        # 摄像机跟随
        self.camera_sys.follow(self.player,
                               self.world_sys.room.width,
                               self.world_sys.room.height,
                               self.w, self.h)
        

        # 发送自身状态给服务器
        self._send_status_if_needed()


        # ---------- 渲染 ----------
    def on_draw(self):
        self.clear()
        # 游戏世界（随摄像机移动）
        self.camera_sprites.use()
        self.world_sys.room.draw_ground()
        self.world_sys.room.draw_walls()
        self.player.draw()
        self.remote_sys.draw()
        self.world_sys.bullet_list.draw()

        # GUI 层（固定屏幕）
        self.camera_gui.use()
        if self.mouse_x and self.mouse_y:
            self.mouse_sprite.draw()


    # ---------- 输入处理（直接修改本地玩家属性）----------
    def on_key_press(self, key, modifiers):
        if key == arcade.key.W: self.player.move_up = True
        elif key == arcade.key.S: self.player.move_down = True
        elif key == arcade.key.A: self.player.move_left = True
        elif key == arcade.key.D: self.player.move_right = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W: self.player.move_up = False
        elif key == arcade.key.S: self.player.move_down = False
        elif key == arcade.key.A: self.player.move_left = False
        elif key == arcade.key.D: self.player.move_right = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        # 世界坐标 = 窗口坐标 + 摄像机偏移
        self.mouse_pos.x = x + self.camera_sprites.position.x
        self.mouse_pos.y = y + self.camera_sprites.position.y
        self.mouse_sprite.center_x = x
        self.mouse_sprite.center_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = True
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.player.use_skill()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = False


    # ---------- WebSocket 回调 ----------
    def _enqueue_ws_message(self, msg: dict):
        msg_type = msg.get("type")
        if msg_type == "game_state":
            players = msg.get("snapshots", {}).get("Players", [])
            self.message_queue.put(NetworkMessage("game_state", players))
        elif msg_type == "game_state_diff":
            players = msg.get("snapshots", {}).get("Players", [])
            self.message_queue.put(NetworkMessage("game_state_diff", players))
        elif msg_type == "player_leave":
            uuid = msg.get("uuid")
            self.message_queue.put(NetworkMessage("player_leave", uuid))


    def _on_ws_connected(self):
        join_msg = {
            "type": "join",
            "uuid": self.player.uuid,
            "name": self.player.username,
            "char_type": self.player.char_type
        }
        self.ws_client.SendJsonMsg(join_msg)


    def _on_ws_error(self, err):
        print("WS 错误:", err)

    def _on_ws_close(self):
        self.message_queue.put(NetworkMessage("reset"))


    # ---------- 网络发送 ----------------
    def _send_status_if_needed(self):
        now = time.time()
        if now - self.last_send >= self.send_interval:
            self.ws_client.SendJsonMsg({
                "type": "player_game_status",
                "x": self.player.pos.x,
                "y": self.player.pos.y,
                "is_walking": self.player.is_walking,
                "is_attack": self.player.is_attack,
                "mouse_pos": {
                    "x": self.mouse_pos.x,
                    "y": self.mouse_pos.y
                },
            })
            self.last_send = now
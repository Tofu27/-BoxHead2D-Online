import arcade
from core.global_state import GlobalState, AppState
from core.ws_client import WSClient
from core.proto import packets_pb2
from core.resource_manager import ResourceManager
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from game.character import Player
from core.config_loader import ConfigLoader


CAMERA_SPEED = 1.0   # ✅ 定义相机跟随速度

class InGameView(arcade.View):
    """进入状态视图：连接服务器，等待 ID"""

    def __init__(self):
        super().__init__()
        self.g = GlobalState()
        self.resource_mgr = ResourceManager()
        self.config = ConfigLoader()
        self.physics_engine = None
        
        self.player = None

        self.w, self.h = self.window.get_size()
        self.camera_sprites = arcade.Camera(self.w, self.h)
        self.camera_gui = arcade.Camera(self.w, self.h)

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # ✅ 地图尺寸（从 ResourceManager 获取）
        self.map_width = 0
        self.map_height = 0

        
        # ✅ 保存回调引用，以便取消注册
        self._report_timer = 0.0
        self._packet_callback_ref = self._on_packet_received


    def setup(self):
        """类似于 Godot 的 _ready()，在切换到这个状态时调用"""
        
        # 1. 加载配置（只加载一次）
        self.config.load("resources")

        # 1. 加载地图（如果尚未加载）
        if self.resource_mgr.get_tile_map() is None:
            self.resource_mgr.load_map()

        # 2. 获取地图资源
        wall_list = self.resource_mgr.get_wall_list()
        self.map_width, self.map_height = self.resource_mgr.get_map_wh()

        # Create the physics engine
        damping = 0.01
        gravity = (0, 0)
        self.physics_engine = PymunkPhysicsEngine(gravity, damping)
        self.player = Player(-1000, -1000, self.physics_engine)

        self.physics_engine.add_sprite(
            self.player,
            friction=0,
            moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.001,
            collision_type="player",
            elasticity=0.1
        )
        self.physics_engine.add_sprite_list(
            wall_list,
            friction=0,
            collision_type="wall",
            body_type=PymunkPhysicsEngine.STATIC,
        )

        # 6. ✅ 注册通用数据包回调（类似于 Godot 的 connect）
        ws = self.g.ws
        ws.on_packet(self._packet_callback_ref)

        # 7. 发送初始化请求
        pkt = packets_pb2.Packet()
        ws.send(pkt)


    def on_hide_view(self):
        """视图隐藏时取消注册，避免消息泄漏"""
        print("InGameView: 取消数据包回调")
        ws = self.g.ws
        if ws:
            ws.remove_packet_callback(self._packet_callback_ref)

    def on_draw(self):
        self.clear()
        self.camera_sprites.use()

        # 绘制地图
        tile_map = self.resource_mgr.get_tile_map()
        if tile_map:
            # 绘制所有图层
            for layer in tile_map.sprite_lists.values():
                layer.draw()

        self.player.draw()
        self.camera_gui.use()
        

    def on_update(self, delta_time):
        # 物理更新
        if self.physics_engine:
            self.physics_engine.step()
            
        self.player.update()
        self.scroll_to_player()

        # 定期上报状态
        self._report_timer += delta_time
        if self._report_timer >= 1.0 / 1:  # 每秒 1 次
            self._report_timer = 0
            self._send_player_state()

    def _on_packet_received(self, pkt: packets_pb2.Packet):
        print("接收到消息:", pkt)
        if pkt.HasField('player_spawn'):
            if pkt.sender_id != self.g.client_id:
                return
            
            player_spawn = pkt.player_spawn
            self.player.pos.x = player_spawn.x
            self.player.pos.y = player_spawn.y
            self.player.health = player_spawn.health
            self.player.max_health = player_spawn.max_health
            self.player.speed = player_spawn.speed

            self.physics_engine.set_position(self.player, (player_spawn.x, player_spawn.y))
    
    def _send_player_state(self):
        """向服务端上报当前玩家的完整状态"""
        ws = self.g.ws
        if not ws or not ws.connected:
            return
        
        if not self.player:
            return

        pkt = packets_pb2.Packet()
        report = pkt.player_spawn
        report.x = self.player.pos.x
        report.y = self.player.pos.y
        report.health = self.player.health
        report.max_health = self.player.max_health
        report.speed = self.player.speed
        ws.send(pkt)

    def scroll_to_player(self) -> None:
        """
        Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """

        if not self.player:
            return

        x = self.player.pos.x - float(self.w / 2)
        y = self.player.pos.y - float(self.h / 2)

        if self.player.pos.x < float(self.w / 2):
            x = 0
        elif self.player.pos.x > float(self.map_width - self.w / 2):
            x = float(self.map_width - self.w)

        if self.player.pos.y < float(self.h / 2):
            y = 0
        elif self.player.pos.y > float(self.map_height - self.h / 2):
            y = float(self.map_height - self.h)

        self.camera_sprites.move_to((x, y), CAMERA_SPEED)

    
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
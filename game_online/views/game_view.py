import arcade
from views.base_view import FadingView
from utils.utils import Utils
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from entities.character import Player, Rambo, Redbit
from entities.room import Room
from entities.weapon import Missile
from views.base_view import CAMERA_SPEED

import time
import threading
from network.wsClient import GameWebSocketClient
from network.remoteManager import RemotePlayerManager


class GameView(FadingView):
    """
    主游戏视图。
    负责：
    - 显示地图、玩家（本地+远程）、子弹
    - 处理用户输入（移动、射击）
    - 通过 WebSocket 与服务器同步其他玩家状态
    - 管理本地物理世界和渲染
    """

    def __init__(self):
        super().__init__()

        # ----- 多人联机相关 -----
        self.RemoteManager = None   # 将在 setup 中初始化
        self.WsClient = None                        # WebSocket 客户端实例
        self._PendingPlayers = []                   # 临时存储从服务器接收的玩家快照（待主线程处理）
        self._PendingLock = threading.Lock()        # 保护 _PendingPlayers 的线程锁
        self.LastSendTime = 0                       # 上次向服务器发送状态的时间戳
        self.SendInterval = 0.05                    # 发送间隔（秒），约20Hz，匹配服务器 tick 频率
        self._LastWsPrintTime = 0                   # 上次打印 WebSocket 消息的时间（用于节流）
        self._WsPrintInterval = 2.0                 # 打印间隔（秒），避免控制台刷屏

        # ----- 鼠标和 UI -----
        self.mouse_x = None                        # 鼠标在窗口中的 X 坐标
        self.mouse_y = None                        # 鼠标在窗口中的 Y 坐标
        self.mouse_pos = Vec2(0, 0)                # 鼠标在世界空间中的位置（考虑摄像机偏移）
        self.mouse_sprite = arcade.Sprite("public/graphics/ui/Cursor.png")   # 自定义鼠标光标
        self.physics_engine = None                 # Pymunk 物理引擎实例
        self.manager = None                        # GUI 管理器（商店等，暂未使用）

        # ----- 精灵列表 -----
        self.WallList = None                      # 墙壁精灵列表
        self.player = None                         # 本地玩家角色
        self.PlayerBulletList = None             # 玩家发射的子弹列表

        # ----- 移动按键状态 -----
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # ----- 摄像机 -----
        self.camera_sprites = arcade.Camera(self.w, self.h)   # 用于绘制游戏世界（跟随玩家）
        self.camera_gui = arcade.Camera(self.w, self.h)       # 用于绘制 GUI（固定位置）

    def setup(self, player_meta: any, map: Room) -> None:
        """
        初始化游戏。
        :param player_meta: 包含玩家信息的字典，必须有 'player'（角色类）、'uuid'、'name'、'char_type'
        :param map: 房间类（可调用，返回 Room 实例）
        """

        # ----- 1. 启动 WebSocket 客户端，连接游戏服务器 -----
        self.WsClient = GameWebSocketClient(
            serverUrl="ws://localhost:8888/ws",
            playerUUID=player_meta['uuid'],
            onGameState=self.on_ws_game_state,   # 接收游戏状态的回调
            onConnected=self.on_ws_connected,     # 连接成功后发送 join 消息
            onError=self.on_ws_error,
            onClose=self.on_ws_close
        )
        self.WsClient.Start()   # 在后台线程中运行

        # ----- 2. 播放游戏背景音乐 -----
        self.window.play_game_music(1)

        # ----- 3. 初始化游戏对象和物理世界 -----
        self.WallList = arcade.SpriteList()
        self.PlayerBulletList = arcade.SpriteList()

        damping = 0.01
        gravity = (0, 0)
        self.physics_engine = PymunkPhysicsEngine(gravity, damping)

        # 创建房间（地图）
        self.room = map()
        self.WallList = self.room.walls

        # 创建本地玩家角色
        player: Player = player_meta['player']
        self.player = player(
            float(self.room.width / 2), float(self.room.height / 2), self.physics_engine
        )
        self.player.register_mouse_pos(self.mouse_pos)   # 让玩家知道鼠标位置（用于瞄准）
        self.player.uuid = player_meta['uuid']
        self.player.username = player_meta['name']

        # 将玩家加入物理世界（动态刚体）
        self.physics_engine.add_sprite(
            self.player,
            friction=0,
            moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.001,
            collision_type="player",
            elasticity=0.1
        )
        # 将墙壁加入物理世界（静态刚体）
        self.physics_engine.add_sprite_list(
            self.room.walls,
            friction=0,
            collision_type="wall",
            body_type=PymunkPhysicsEngine.STATIC,
        )
        # 注意：商店代码暂被注释


         # 创建远程玩家管理器，传入物理引擎、子弹列表、窗口
        self.RemoteManager = RemotePlayerManager(
            physics_engine=self.physics_engine,
            BulletList=self.PlayerBulletList,
            window=self.window,
            LocalUUID= self.player.uuid
        )

    # -------------------- WebSocket 回调函数（由子线程调用）--------------------
    def on_ws_game_state(self, players_list):
        """
        服务器推送所有玩家状态时回调。
        运行在 WebSocket 子线程中，仅存储数据到 _pending_players，
        避免在多线程中直接操作游戏主线程的精灵。
        """
        now = time.time()
        # 控制台输出节流，避免刷屏
        if now - self._LastWsPrintTime >= self._WsPrintInterval:
            print("ws消息 (节流):", players_list)
            self._LastWsPrintTime = now

        with self._PendingLock:
            self._PendingPlayers = players_list   # 替换为新快照

    def on_ws_connected(self):
        """WebSocket 连接成功后调用（子线程）。发送 join 消息通知服务器该玩家加入。"""
        join_msg = {
            "type": "join",
            "uuid": self.player.uuid,
            "name": self.player.username,
            "char_type": self.player.char_type   # 玩家选择的角色类型（Player/Rambo/Redbit）
        }
        self.WsClient.SendJsonMsg(join_msg)

    def on_ws_error(self, err):
        print("WS 报错:", err)

    def on_ws_close(self):
        print("WS 关闭")

    # -------------------- 渲染 --------------------
    def on_draw(self) -> None:
        """绘制每一帧。"""
        self.clear()

        # 1. 绘制世界（玩家、墙壁、子弹等）——使用世界相机
        self.camera_sprites.use()
        self.room.draw_ground()
        self.room.draw_walls()
        self.player.draw()

        # 绘制远程玩家
        self.RemoteManager.draw()

        self.PlayerBulletList.draw()

        # 2. 绘制 GUI（准星等）——使用 GUI 相机（固定屏幕位置）
        self.camera_gui.use()
        if self.mouse_x and self.mouse_y:
            self.mouse_sprite.draw()

    # -------------------- 每帧更新 --------------------
    def on_update(self, delta_time) -> None:
        """
        每帧更新：
        - 处理新接收的玩家状态（同步）
        - 更新物理世界
        - 更新本地玩家逻辑（移动、攻击）
        - 更新子弹
        - 发送本地状态给服务器
        - 平滑插值其他玩家的位置
        """
        # 1. 从待决缓冲区取出新数据，同步其他玩家
        with self._PendingLock:
            if self._PendingPlayers:
                self.RemoteManager.sync_from_snapshot(self._PendingPlayers)
                self._PendingPlayers = []

        # 2. 物理引擎步进
        self.physics_engine.step()

        # 3. 更新本地玩家状态、攻击、子弹
        self.player.update()
        self.update_player_attack()

        # 更新远程玩家（内部处理位置插值和攻击模拟）
        self.RemoteManager.update()

        self.process_player_bullet()

        # 4. 摄像机跟随本地玩家
        self.scroll_to_player()

        # 5. 发送本地玩家的位置、状态给服务器（限频）
        self._send_status_if_needed()


    def _send_status_if_needed(self):
        """限制频率向服务器发送本地玩家的状态（位置、动作、鼠标指向等）。"""
        now = time.time()
        if now - self.LastSendTime >= self.SendInterval:
            self.WsClient.SendJsonMsg({
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
            self.LastSendTime = now

    # -------------------- 玩家输入处理 --------------------
    def on_key_press(self, key, modifiers) -> None:
        """键盘按下：更新移动标志。"""
        if key == arcade.key.W:
            self.player.move_up = True
        elif key == arcade.key.S:
            self.player.move_down = True
        elif key == arcade.key.A:
            self.player.move_left = True
        elif key == arcade.key.D:
            self.player.move_right = True

    def on_key_release(self, key, modifiers) -> None:
        """键盘释放：复位移动标志。"""
        if key == arcade.key.W:
            self.player.move_up = False
        elif key == arcade.key.S:
            self.player.move_down = False
        elif key == arcade.key.A:
            self.player.move_left = False
        elif key == arcade.key.D:
            self.player.move_right = False

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        """鼠标移动：记录窗口坐标、世界坐标，更新自定义光标位置。"""
        self.mouse_x = x
        self.mouse_y = y
        # 世界坐标 = 窗口坐标 + 摄像机偏移
        self.mouse_pos.x = self.mouse_x + self.camera_sprites.position.x
        self.mouse_pos.y = self.mouse_y + self.camera_sprites.position.y
        self.mouse_sprite.center_x = x
        self.mouse_sprite.center_y = y

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        """鼠标点击：左键开始攻击，右键使用技能。"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = True
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.player.use_skill()

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        """鼠标释放：左键停止攻击。"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = False

    # -------------------- 辅助功能 --------------------
    def scroll_to_player(self) -> None:
        """摄像机平滑跟随本地玩家，并限制边界（不超出房间范围）。"""
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
        """窗口大小改变时，调整两个摄像机的视口大小。"""
        self.w = width
        self.h = height
        self.camera_sprites.resize(width, height)
        self.camera_gui.resize(width, height)

    # -------------------- 本地玩家攻击与子弹逻辑 --------------------
    def update_player_attack(self) -> None:
        """
        本地玩家的攻击逻辑：根据 is_attack 标志和冷却时间发射子弹。
        与远程玩家的攻击逻辑类似，但使用本地鼠标位置（self.mouse_pos）。
        """
        if self.player.is_attack:
            if self.player.cd == self.player.cd_max:
                self.player.cd = 0

            if self.player.cd == 0:
                if self.player.current_weapon.is_gun:
                    bullets = self.player.attack()
                    self.player.current_weapon.play_sound(self.window.effect_volume)
                    for bullet in bullets:
                        bullet.change_x = bullet.aim.x
                        bullet.change_y = bullet.aim.y
                        self.PlayerBulletList.append(bullet)

        self.player.cd = min(self.player.cd + 1, self.player.cd_max)

    def process_player_bullet(self) -> None:
        """
        更新所有玩家发射的子弹：
        - 减少生命周期
        - 碰撞检测（目前只与墙壁碰撞）
        - 撞墙或生命周期耗尽则移除子弹
        """
        self.PlayerBulletList.update()

        for bullet in self.PlayerBulletList:
            bullet.life_span -= 1

            # 仅检测与墙壁的碰撞（敌人碰撞待后续实现）
            hit_list = arcade.check_for_collision_with_list(bullet, self.WallList)
            if len(hit_list) > 0:
                bullet.remove_from_sprite_lists()
                continue

            if bullet.life_span <= 0:
                bullet.remove_from_sprite_lists()
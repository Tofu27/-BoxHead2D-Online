import arcade
from views.base_view import FadingView
from utils.utils import Utils
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from entities.room import StartRoom
from utils.utils import Color, Style
from entities.character import Player
from views.base_view import CAMERA_SPEED


# ==================== 开始菜单视图（带物理引擎和UI） ====================
class StartView(FadingView):
    """游戏主菜单视图，包含角色控制演示、按钮（开始/选项/退出）。"""

    def __init__(self) -> None:
        super().__init__()
        self.mouse_x = None
        self.mouse_y = None
        self.mouse_pos = Vec2(0, 0)

        # 游戏对象列表
        self.wall_list = None
        self.player = None
        self.player_bullet_list = None

        # 物理引擎（用于墙壁碰撞和角色移动）
        self.physics_engine = None

        # 相机（用于滚动，当前未使用）
        self.camera_sprites = arcade.Camera(self.w, self.h)

    def setup(self) -> None:
        """初始化开始菜单：播放音乐、创建物理世界、角色、墙壁、UI按钮和指南图片。"""
        # 播放开始界面音乐
        self.window.play_start_music(0)

        # 物理引擎（无重力，高阻尼）
        damping = 0.01
        gravity = (0, 0)
        self.physics_engine = PymunkPhysicsEngine(damping=damping, gravity=gravity)

        # 子弹列表（初始为空）
        self.player_bullet_list = arcade.SpriteList()

        # 创建房间（墙壁和地面）
        room_w = Utils.round_to_multiple(self.w, 30)
        room_h = Utils.round_to_multiple(self.h, 30)
        self.room = StartRoom(room_w, room_h)
        self.wall_list = self.room.walls

        # 创建玩家角色（支持WASD移动）
        self.player = Player(
            float(self.w / 2), float(self.h / 2) + 20, self.physics_engine
        )
        self.player.register_mouse_pos(self.mouse_pos) #鼠标坐标信息传递给用户角色

        arcade.set_background_color(Color.BLACK)

        # 将玩家添加到物理引擎（动态物体）
        self.physics_engine.add_sprite(
            self.player,
            friction=0,
            moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.001,
            collision_type="player",
            elasticity=0.1
        )

        # 添加墙壁（静态物体）
        self.physics_engine.add_sprite_list(
            self.room.walls,
            friction=0,
            collision_type="wall",
            body_type=PymunkPhysicsEngine.STATIC,
        )

        # 操作指南图片（移动、射击、暂停、换武器、商店）
        self.start_sprite_list = arcade.SpriteList()
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="graphics/ui/MoveGuide.png",
                scale=0.3,
                center_x=200,
                center_y=200
            )
        )
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="graphics/ui/ShootGuide.png",
                scale=0.3,
                center_x=self.w - 200,
                center_y=200,
            )
        )
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="graphics/ui/PauseGuide.png",
                scale=0.3,
                center_x=200,
                center_y=self.h - 100,
            )
        )
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="graphics/ui/WeaponChangeGuide.png",
                scale=0.3,
                center_x=200,
                center_y=self.h - 200,
            )
        )
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="graphics/ui/ShopGuide.png",
                scale=0.3,
                center_x=self.w - 200,
                center_y=self.h - 100,
            )
        )

        # 作者信息文字（带阴影效果）
        self.about_text = arcade.Text("Created by Unchain.",
                                      self.w - 600,
                                      120,
                                      color=Color.DARK_GRAY,
                                      font_size=14,
                                      font_name="Cubic 11",
                                      anchor_x="center")
        self.about_text_shadow = arcade.Text("Created by Unchain.",
                                             self.w - 602,
                                             120,
                                             color=Color.LIGHT_GRAY,
                                             font_size=14,
                                             font_name="Cubic 11",
                                             anchor_x="center")

        # 图形用户界面管理器（按钮）
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.vertical_box = arcade.gui.UIBoxLayout(x=200)

        # 标题Logo（作为UI控件）
        title = arcade.Sprite(filename="graphics/ui/TitleLogo.png", scale=1)
        title_ui = arcade.gui.UISpriteWidget(sprite=title, width=400, height=200)
        self.vertical_box.add(title_ui.with_space_around(bottom=0))

        # 三个按钮：开始游戏、选项、退出
        start_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.START, width=150, style=Style.BUTTON_DEFAULT
        )
        option_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.OPTION, width=150, style=Style.BUTTON_DEFAULT
        )
        quit_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.QUIT, width=150, style=Style.BUTTON_DEFAULT
        )

        self.vertical_box.add(start_button.with_space_around(bottom=20))
        self.vertical_box.add(option_button.with_space_around(bottom=20))
        self.vertical_box.add(quit_button.with_space_around(bottom=20))

        start_button.on_click = self.on_click_start
        option_button.on_click = self.on_click_option
        quit_button.on_click = self.on_click_quit  # 退出按钮回调
        # 将按钮垂直布局居中显示
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x", anchor_y="center_y", child=self.vertical_box
            )
        )

    def on_draw(self) -> None:
        """绘制菜单：地面、墙壁、指南图片、玩家、子弹、UI按钮和作者信息。"""
        self.clear()
        self.camera_sprites.use()

        self.room.draw_ground()
        self.room.draw_walls()

        self.start_sprite_list.draw()
        self.player.draw()
        self.player_bullet_list.draw()

        self.manager.draw()
        self.about_text_shadow.draw()
        self.about_text.draw()

    def on_update(self, delta_time: float) -> None:
        """每帧更新：处理淡入淡出、物理模拟和玩家动画。"""

        self.update_fade()
        self.physics_engine.step()
        self.player.update()        # 玩家状态更新
        self.update_player_attack() # 玩家攻击时，子弹创建
        self.process_player_bullet() # 玩家子弹状态

        self.scroll_to_player()

    # 键盘控制玩家移动
    def on_key_press(self, key, modifiers) -> None:
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

    def update_player_attack(self) -> None:
        if self.player.is_attack:
            if self.player.cd == self.player.cd_max:
                self.player.cd = 0

            if self.player.cd == 0 and self.player.energy - self.player.current_weapon.cost >= 0:
                self.player.energy -= self.player.current_weapon.cost
                bullets = self.player.attack()
                self.player.current_weapon.play_sound(
                    self.window.effect_volume)
                for bullet in bullets:
                    bullet.change_x = bullet.aim.x
                    bullet.change_y = bullet.aim.y
                    self.player_bullet_list.append(bullet)

        self.player.cd = min(self.player.cd + 1, self.player.cd_max)
            
            
    def process_player_bullet(self) -> None:
        self.player_bullet_list.update()

        for bullet in self.player_bullet_list:
            bullet.life_span -= 1

            hit_list = arcade.check_for_collision_with_list(
                bullet, self.wall_list)

            if len(hit_list) > 0:
                bullet.remove_from_sprite_lists()

            if bullet.life_span <= 0:
                bullet.remove_from_sprite_lists()

    def scroll_to_player(self) -> None:
        """
        Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """
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

    # 鼠标移动
    def on_mouse_motion(self, x, y, dx, dy) -> None:
        """Mouse movement."""

        self.mouse_x = x
        self.mouse_y = y
        self.mouse_pos.x = self.mouse_x + self.camera_sprites.position.x
        self.mouse_pos.y = self.mouse_y + self.camera_sprites.position.y

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = True
        
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = False


    def on_click_start(self, event) -> None:
        Utils.clear_ui_manager(self.manager)
        self.window.select_view.setup()
        self.window.show_view(self.window.select_view)
    
    def on_click_option(self, event) -> None:
        Utils.clear_ui_manager(self.manager)
        self.window.option_view.setup(self)
        self.window.show_view(self.window.option_view)

    def on_click_quit(self, event) -> None:
        """退出游戏的回调函数。"""
        arcade.exit()

        
    def resize_camera(self, width, height) -> None:
        self.w = width
        self.h = height
        self.setup()
        self.camera_sprites.resize(width, height)

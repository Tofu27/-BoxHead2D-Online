import arcade
from views.base_view import FadingView
from core.systems.physics_system import PhysicsSystem
from core.systems.camera_system import CameraSystem
from entities.character import CreatePlayer
from entities.room import StartRoom
from core.constants import Color, Style
from pyglet.math import Vec2
from utils.utils import Utils

class StartView(FadingView):
    """游戏主菜单视图，包含角色控制演示、按钮（开始/选项/退出）。"""
    def __init__(self):
        super().__init__()
        # 鼠标位置（必须在 setup 之前定义，因为玩家要注册它）
        self.mouse_pos = Vec2(0, 0)
        self.mouse_x = None
        self.mouse_y = None

        # 游戏对象列表
        self.wall_list = None
        self.player = None
        self.player_bullet_list = None

        # 系统组件
        self.physics = None           # PhysicsSystem
        self.camera_sys = None        # CameraSystem

        # 相机（用于滚动）
        self.camera_sprites = arcade.Camera(self.w, self.h)

    def setup(self):
        """初始化开始菜单：播放音乐、创建物理世界、角色、墙壁、UI按钮和指南图片。"""
        # 1. 播放音乐
        self.window.play_start_music(0)
        w, h = self.window.get_size()
        self.w, self.h = w, h

        # 创建摄像机
        self.camera_sprites = arcade.Camera(w, h)
        self.camera_sys = CameraSystem(self.camera_sprites)

        # 子弹列表（初始为空）
        self.player_bullet_list = arcade.SpriteList()

        # 创建房间和物理系统
        room_w = Utils.round_to_multiple(self.w, 30)
        room_h = Utils.round_to_multiple(self.h, 30)
        self.room = StartRoom(room_w, room_h)
        self.wall_list = self.room.walls
        self.physics = PhysicsSystem()
        self.physics.add_walls(self.wall_list)

        # 创建本地玩家
        self.player = CreatePlayer(
            "Player", w/2, h/2+20, self.physics.engine, False
        )
        self.player.register_mouse_pos(self.mouse_pos)
        self.physics.add_player(self.player)

        
        # 创建 UI 管理器及按钮（原 start_view 的逻辑）
        self._setup_ui()


    def _setup_ui(self):
        """搭建开始菜单的 UI 按钮"""
        # 操作指南图片（移动、射击、暂停、换武器、商店）
        self.start_sprite_list = arcade.SpriteList()
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="public/graphics/ui/MoveGuide.png",
                scale=0.3,
                center_x=200,
                center_y=200
            )
        )
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="public/graphics/ui/ShootGuide.png",
                scale=0.3,
                center_x=self.w - 200,
                center_y=200,
            )
        )
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="public/graphics/ui/PauseGuide.png",
                scale=0.3,
                center_x=200,
                center_y=self.h - 100,
            )
        )
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="public/graphics/ui/WeaponChangeGuide.png",
                scale=0.3,
                center_x=200,
                center_y=self.h - 200,
            )
        )
        self.start_sprite_list.append(
            arcade.Sprite(
                filename="public/graphics/ui/ShopGuide.png",
                scale=0.3,
                center_x=self.w - 200,
                center_y=self.h - 100,
            )
        )

        # 作者信息文字（带阴影效果）
        self.about_text = arcade.Text("Created by Unchain.",
                                      self.w / 2,
                                      90,
                                      color=Color.DARK_GRAY,
                                      font_size=14,
                                      font_name="Cubic 11",
                                      anchor_x="center")
        self.about_text_shadow = arcade.Text("Created by Unchain.",
                                             self.w /2 -2,
                                             90,
                                             color=Color.LIGHT_GRAY,
                                             font_size=14,
                                             font_name="Cubic 11",
                                             anchor_x="center")

        # 图形用户界面管理器（按钮）
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.vertical_box = arcade.gui.UIBoxLayout(x=200)

        # 标题Logo（作为UI控件）
        title = arcade.Sprite(filename="public/graphics/ui/TitleLogo.png", scale=1)
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

    def on_draw(self):
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

    def on_update(self, delta_time):
        """每帧更新：淡入淡出、物理、玩家、攻击、子弹、摄像机跟随。"""
        self.update_fade()
        self.physics.step()               # 物理步进
        self.player.update()
        self.update_player_attack()
        self.process_player_bullet()
        # 使用摄像机系统跟随玩家
        self.camera_sys.follow(self.player, self.room.width, self.room.height, self.w, self.h)

    # ---------- 输入处理 ----------
    def on_key_press(self, key, modifiers) -> None:
        if key == arcade.key.W: self.player.move_up = True
        elif key == arcade.key.S: self.player.move_down = True
        elif key == arcade.key.A: self.player.move_left = True
        elif key == arcade.key.D: self.player.move_right = True

    def on_key_release(self, key, modifiers) -> None:
        if key == arcade.key.W: self.player.move_up = False
        elif key == arcade.key.S: self.player.move_down = False
        elif key == arcade.key.A: self.player.move_left = False
        elif key == arcade.key.D: self.player.move_right = False

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        self.mouse_x = x
        self.mouse_y = y
        self.mouse_pos.x = self.mouse_x + self.camera_sprites.position.x
        self.mouse_pos.y = self.mouse_y + self.camera_sprites.position.y

    def on_mouse_press(self, x, y, button, mod) -> None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = True

    def on_mouse_release(self, x, y, button, mod) -> None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.player.is_attack = False

    # ---------- 游戏逻辑 ----------
    def update_player_attack(self) -> None:
        if self.player.is_attack:
            if self.player.cd == self.player.cd_max:
                self.player.cd = 0
            if self.player.cd == 0 and self.player.energy >= self.player.current_weapon.cost:
                self.player.energy -= self.player.current_weapon.cost
                bullets = self.player.attack()
                self.player.current_weapon.play_sound(self.window.effect_volume)
                for bullet in bullets:
                    bullet.change_x = bullet.aim.x
                    bullet.change_y = bullet.aim.y
                    self.player_bullet_list.append(bullet)
        self.player.cd = min(self.player.cd + 1, self.player.cd_max)

    def process_player_bullet(self) -> None:
        self.player_bullet_list.update()
        for bullet in self.player_bullet_list:
            bullet.life_span -= 1
            hit_list = arcade.check_for_collision_with_list(bullet, self.wall_list)
            if hit_list:
                bullet.remove_from_sprite_lists()
            elif bullet.life_span <= 0:
                bullet.remove_from_sprite_lists()

    # ---------- 按钮回调 ----------
    def on_click_start(self, event) -> None:
        Utils.clear_ui_manager(self.manager)
        self.window.select_view.setup()
        self.window.show_view(self.window.select_view)

    def on_click_option(self, event) -> None:
        Utils.clear_ui_manager(self.manager)
        self.window.option_view.setup(self)
        self.window.show_view(self.window.option_view)

    def on_click_quit(self, event) -> None:
        arcade.exit()

    def resize_camera(self, width, height) -> None:
        self.w = width
        self.h = height
        self.setup()                        # 原版逻辑：重建整个场景
        self.camera_sprites.resize(width, height)
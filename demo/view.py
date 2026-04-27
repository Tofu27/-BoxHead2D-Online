import arcade
import arcade.gui
import utils
import room
import character
# import weapon
# import item
# import effect
import math
import random
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine

FADE_RATE = 8   # 淡入淡出速度（每帧变化量）
CAMERA_SPEED = 1

# ==================== 淡入淡出过渡视图基类 ====================
class FadingView(arcade.View):
    """支持淡入淡出转场效果的视图基类。"""

    def __init__(self) -> None:
        super().__init__()
        self.fade_out = None    # 淡出值（0-255），None表示未开始淡出
        self.fade_in = 255      # 淡入值（从255降到0）
        self.w, self.h = self.window.get_size()
        self.next_view = None   # 要切换到的下一个视图类

    def update_fade(self) -> None:
        """每帧更新淡出/淡入状态，完成后自动切换视图。"""
        if self.fade_out is not None:
            self.fade_out += FADE_RATE
            # 淡出完成且存在下一个视图时，切换视图
            if self.fade_out > 255 and self.next_view is not None:
                self.window.start_view = self.next_view()
                self.window.start_view.setup()
                self.window.show_view(self.window.start_view)

        if self.fade_in is not None:
            self.fade_in -= FADE_RATE
            if self.fade_in <= 0:
                self.fade_in = None   # 淡入完成

    def draw_fading(self) -> None:
        """绘制半透明遮罩实现淡入淡出效果。"""
        if self.fade_out is not None:
            arcade.draw_rectangle_filled(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height,
                (0, 0, 0, self.fade_out),
            )

        if self.fade_in is not None:
            arcade.draw_rectangle_filled(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height,
                (0, 0, 0, self.fade_in),
            )

# ==================== 默认启动视图（按任意键） ====================
class DefaultView(FadingView):
    """游戏启动时显示的视图，提示按任意键继续。"""

    def setup(self) -> None:
        """设置背景、标题Logo和闪烁文字。"""
        arcade.set_background_color(utils.Color.GROUND_WHITE)
        self.w, self.h = self.window.get_size()
        
        # 标题Logo图片
        self.title = arcade.Sprite(
            filename="graphics/ui/TitleLogo.png",
            scale=1,
            center_x=self.w / 2,
            center_y=self.h / 2 + 20,
        )
        self.text_alpha = 250
        self.text_fading = -5   # 每帧透明度变化量，实现闪烁

        # 提示文字（按任意键）
        self.title_text = arcade.Text(
            self.window.cur_lang.PRESS_ANY_KEY,
            self.w / 2,
            self.h / 2 - 100,
            color=(0, 0, 0, 250),
            font_size=24,
            font_name="Cubic 11",
            anchor_x="center",
        )

    def on_update(self, delta_time: float) -> None:
        """每帧更新：处理淡入淡出，并让提示文字闪烁。"""
        self.update_fade()

        # 文字透明度循环变化
        self.text_alpha += self.text_fading
        if self.text_alpha == 10 or self.text_alpha == 250:
            self.text_fading = -self.text_fading
        self.text_alpha %= 255
        self.title_text.color = (0, 0, 0, self.text_alpha)

    def on_draw(self) -> None:
        """绘制当前视图内容。"""
        self.clear()
        self.title_text.draw()
        self.title.draw()
        self.draw_fading()

    # 鼠标点击或键盘按键都会触发切换到开始菜单视图
    def on_mouse_press(self, _x, _y, _button, _modifiers) -> None:
        self.next_view = StartView
        if self.fade_out is None:
            self.fade_out = 0   # 开始淡出

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.next_view = StartView
        if self.fade_out is None:
            self.fade_out = 0

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
        room_w = utils.Utils.round_to_multiple(self.w, 30)
        room_h = utils.Utils.round_to_multiple(self.h, 30)
        self.room = room.StartRoom(room_w, room_h)
        self.wall_list = self.room.walls

        # 创建玩家角色（支持WASD移动）
        self.player = character.Player(
            float(self.w / 2), float(self.h / 2) + 20, self.physics_engine
        )
        self.player.register_mouse_pos(self.mouse_pos) #鼠标坐标信息传递给用户角色

        arcade.set_background_color(utils.Color.BLACK)

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
                                      color=utils.Color.DARK_GRAY,
                                      font_size=14,
                                      font_name="Cubic 11",
                                      anchor_x="center")
        self.about_text_shadow = arcade.Text("Created by Unchain.",
                                             self.w - 602,
                                             120,
                                             color=utils.Color.LIGHT_GRAY,
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
            text=self.window.cur_lang.START, width=150, style=utils.Style.BUTTON_DEFAULT
        )
        option_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.OPTION, width=150, style=utils.Style.BUTTON_DEFAULT
        )
        quit_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.QUIT, width=150, style=utils.Style.BUTTON_DEFAULT
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
        utils.Utils.clear_ui_manager(self.manager)
        self.window.select_view.setup()
        self.window.show_view(self.window.select_view)
    
    def on_click_option(self, event) -> None:
        utils.Utils.clear_ui_manager(self.manager)
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


class SelectionView(FadingView):
    """Character and map selection."""

    def on_show_view(self) -> None:
        arcade.set_background_color(utils.Color.GROUND_WHITE)

    def setup(self) -> None:
        self.w = self.window.width
        self.h = self.window.height

        self.name_list = []
        self.describe_list = []
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.selection_box = arcade.gui.UIBoxLayout(vertical=False)
        self.rest_box = arcade.gui.UIBoxLayout(vertical=False)


        # Characters
        self.char_sprites = arcade.SpriteList()
        self.char_list = [
            character.Player,
            character.Rambo,
            character.Redbit,
        ]
        self.cur_char_idx = 0
        self.cur_char = character.Character(
            float(self.w/2 - 240), float(self.h/2 + 100))

        self.name_list.append(
            arcade.Text(
                text="",
                start_x=float(self.w/2 - 240),
                start_y=float(self.h/2 + 20),
                font_size=12,
                font_name="Cubic 11",
                anchor_x="center",
                align="center",
                width=120,
                color=utils.Color.BLACK,
            )
        )
        self.describe_list.append(
            arcade.Text(
                text="",
                start_x=float(self.w/2 - 240),
                start_y=float(self.h/2 - 10),
                font_size=12,
                font_name="Cubic 11",
                anchor_x="center",
                align="center",
                multiline=False,
                width=240,
                color=utils.Color.BLACK,
            )
        )
        self.set_character()


        # Maps
        self.map_list = [
            room.GameRoom0,
            # room.GameRoom1,
            # room.GameRoom2,
        ]
        self.cur_map_idx = 0
        self.cur_map = self.map_list[self.cur_map_idx]
        self.cur_map_sprite = arcade.Sprite()
        self.name_list.append(
            arcade.Text(
                text="",
                start_x=float(self.w/2 + 220),
                start_y=float(self.h/2 - 20),
                font_size=12,
                font_name="Cubic 11",
                anchor_x="center",
                align="center",
                width=120,
                color=utils.Color.BLACK,
            )
        )
        self.set_maps()
        
        # Selection buttons
        character_left_button = arcade.gui.UIFlatButton(
            text="<", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        character_right_button = arcade.gui.UIFlatButton(
            text=">", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        map_left_button = arcade.gui.UIFlatButton(
            text="<", width=80, style=utils.Style.BUTTON_DEFAULT
        )
        map_right_button = arcade.gui.UIFlatButton(
            text=">", width=80, style=utils.Style.BUTTON_DEFAULT
        )

        self.selection_box.add(
            character_left_button.with_space_around(right=20))
        self.selection_box.add(
            character_right_button.with_space_around(right=300))
        self.selection_box.add(map_left_button.with_space_around(right=20))
        self.selection_box.add(map_right_button.with_space_around(right=0))
        
        character_left_button.on_click = self.on_click_last_char
        character_right_button.on_click = self.on_click_next_char

        # Rest buttons
        back_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.BACK, width=120, style=utils.Style.BUTTON_DEFAULT
        )
        next_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.NEXT, width=120, style=utils.Style.BUTTON_DEFAULT
        )
        self.rest_box.add(back_button.with_space_around(right=200))
        self.rest_box.add(next_button.with_space_around(right=0))
        back_button.on_click = self.on_click_back
        next_button.on_click = self.on_click_next

        # Add box layouts
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                align_y=-100, child=self.selection_box)
        )
        self.manager.add(arcade.gui.UIAnchorWidget(
            align_y=-200, child=self.rest_box))
        
    def set_maps(self, idx: int = 0) -> None:
        self.cur_map_idx += idx
        self.cur_map_idx %= len(self.map_list)
        self.cur_map = self.map_list[self.cur_map_idx]
        self.cur_map_sprite = self.cur_map.layout_sprite
        self.cur_map_sprite.center_x = float(self.w/2 + 220)
        self.cur_map_sprite.center_y = float(self.h/2 + 70)
        self.name_list[1].text = self.window.cur_lang.DescribeText[
            self.map_list[self.cur_map_idx].name]

    
    def set_character(self, idx: int = 0) -> None:
        self.cur_char_idx += idx
        self.cur_char_idx %= len(self.char_list)
        self.char_sprites.clear()
        self.cur_char.body.texture = self.char_list[self.cur_char_idx].body_texture
        self.char_sprites.extend(self.cur_char.parts)
        self.name_list[0].text = self.window.cur_lang.DescribeText[
            self.char_list[self.cur_char_idx].name]
        self.describe_list[0].text = self.window.cur_lang.DescribeText[
            self.char_list[self.cur_char_idx].description]


    def on_draw(self):
        self.clear()
        self.manager.draw()
        self.char_sprites.draw()
        self.cur_map_sprite.draw()
        for name in self.name_list:
            name.draw()
        for des in self.describe_list:
            des.draw()

            
    def on_update(self, delta_time: float):
        self.cur_char.update()


    def on_click_last_char(self, event) -> None:
        self.set_character(-1)
        self.window.play_button_sound()

    def on_click_next_char(self, event) -> None:
        self.set_character(1)
        self.window.play_button_sound()

    def on_click_back(self, event) -> None:
        utils.Utils.clear_ui_manager(self.manager)
        self.window.start_view.setup()
        self.window.start_view.resize_camera(
            self.window.width, self.window.height)
        self.window.show_view(self.window.start_view)
        self.window.play_button_sound()

    def on_click_next(self, event) -> None:
        utils.Utils.clear_ui_manager(self.manager)
        self.window.game_view = GameView()
        self.window.game_view.setup(
            self.char_list[self.cur_char_idx], self.cur_map)
        self.window.show_view(self.window.game_view)
        self.window.play_button_sound()
        

class GameView(FadingView):
    """Main game view."""

    def __init__(self):
        super().__init__()
        self.mouse_x = None
        self.mouse_y = None
        self.mouse_pos = Vec2(0, 0)
        self.mouse_sprite = arcade.Sprite("graphics/ui/Cursor.png")
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

    def setup(self, player: character.Player, map: room.Room) -> None:
        """Set up the game and initialize the variables."""

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

    def on_draw(self) -> None:
        self.clear()
        self.camera_sprites.use() # 世界相机，绘制场景、玩家、敌人

        self.room.draw_ground()
        self.room.draw_walls()
        self.player.draw()

        self.camera_gui.use() # 切换 GUi相机，绘制准许，信息UI

        # Mouse cursor
        if self.mouse_x and self.mouse_y:
            self.mouse_sprite.draw()


    def on_update(self, delta_time) -> None:
        self.physics_engine.step()

        # Update player
        self.player.update()
        self.scroll_to_player()

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


class OptionView(arcade.View):
    """Optional menu."""

    def __init__(self):
        super().__init__()
        self.manager = None
        self.last_view = None

    def on_show_view(self) -> None:
        arcade.set_background_color(utils.Color.GROUND_WHITE)
        self.window.set_mouse_visible(True)

    def setup(self, last_view) -> None:
        self.last_view = last_view

        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.lang_box = arcade.gui.UIBoxLayout(vertical=False)
        self.effect_volume_box = arcade.gui.UIBoxLayout(vertical=False)
        self.music_volume_box = arcade.gui.UIBoxLayout(vertical=False)
        self.screen_box = arcade.gui.UIBoxLayout(vertical=False)
        self.resolution_box = arcade.gui.UIBoxLayout(vertical=False)
        self.rest_box = arcade.gui.UIBoxLayout(vertical=False)

        # Language settings
        lang_label = arcade.gui.UITextArea(
            text=self.window.cur_lang.LANG,
            width=200,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        lang_left_button = arcade.gui.UIFlatButton(
            text="<", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        lang_text = arcade.gui.UITextArea(
            text=self.window.cur_lang.CUR_LANG,
            width=120,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        lang_right_button = arcade.gui.UIFlatButton(
            text=">", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        self.lang_box.add(
            lang_label.with_space_around(right=20))
        self.lang_box.add(
            lang_left_button.with_space_around(right=20)
        )
        self.lang_box.add(
            lang_text.with_space_around(right=10))
        self.lang_box.add(
            lang_right_button.with_space_around(right=0))
        lang_left_button.on_click = self.on_click_lang_left
        lang_right_button.on_click = self.on_click_lang_right

        # Effect volume settings
        effect_volume_label = arcade.gui.UITextArea(
            text=self.window.cur_lang.EFFECT_VOLUME,
            width=300,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        effect_volume_down_button = arcade.gui.UIFlatButton(
            text="-", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        self.effect_volume_text = arcade.gui.UITextArea(
            text=str(self.window.effect_volume),
            width=40,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        effect_volume_up_button = arcade.gui.UIFlatButton(
            text="+", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        self.effect_volume_box.add(
            effect_volume_label.with_space_around(right=20))
        self.effect_volume_box.add(
            effect_volume_down_button.with_space_around(right=20)
        )
        self.effect_volume_box.add(
            self.effect_volume_text.with_space_around(right=10))
        self.effect_volume_box.add(
            effect_volume_up_button.with_space_around(right=0))
        effect_volume_up_button.on_click = self.on_click_effect_volume_up
        effect_volume_down_button.on_click = self.on_click_effect_volume_down

        # Music volume settings
        music_volume_label = arcade.gui.UITextArea(
            text=self.window.cur_lang.MUSIC_VOLUME,
            width=300,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        music_volume_down_button = arcade.gui.UIFlatButton(
            text="-", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        self.music_volume_text = arcade.gui.UITextArea(
            text=str(self.window.music_volume),
            width=40,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        music_volume_up_button = arcade.gui.UIFlatButton(
            text="+", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        self.music_volume_box.add(
            music_volume_label.with_space_around(right=20))
        self.music_volume_box.add(
            music_volume_down_button.with_space_around(right=20))
        self.music_volume_box.add(
            self.music_volume_text.with_space_around(right=10))
        self.music_volume_box.add(
            music_volume_up_button.with_space_around(right=0))
        music_volume_up_button.on_click = self.on_click_music_volume_up
        music_volume_down_button.on_click = self.on_click_music_volume_down

        # Screen settings
        fullscreen_label = arcade.gui.UITextArea(
            text=self.window.cur_lang.FULLSCREEN,
            width=200,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        self.fullscreen_text = arcade.gui.UITextArea(
            text=str(self.window.fullscreen),
            width=120,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        fullscreen_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.SWITCH, width=120, style=utils.Style.BUTTON_DEFAULT
        )
        self.screen_box.add(fullscreen_label.with_space_around(right=20))
        self.screen_box.add(self.fullscreen_text.with_space_around(right=20))
        self.screen_box.add(fullscreen_button.with_space_around(right=0))
        fullscreen_button.on_click = self.on_click_fullscreen

        # Resolution settings
        resolution_label = arcade.gui.UITextArea(
            text=self.window.cur_lang.RESOLUTION,
            width=200,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        resolution_down_button = arcade.gui.UIFlatButton(
            text="<", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        self.resolution_text = arcade.gui.UITextArea(
            text="1280 x 720",
            width=200,
            height=40,
            font_size=24,
            text_color=utils.Color.BLACK,
            font_name="Cubic 11",
        )
        resolution_up_button = arcade.gui.UIFlatButton(
            text=">", width=60, style=utils.Style.BUTTON_DEFAULT
        )
        self.resolution_box.add(resolution_label.with_space_around(right=20))
        self.resolution_box.add(
            resolution_down_button.with_space_around(right=40))
        self.resolution_box.add(
            self.resolution_text.with_space_around(right=0))
        if self.window.fullscreen:
            self.resolution_text.text = self.window.cur_lang.FULLSCREEN
        else:
            self.resolution_text.text = str(
                self.window.w_scale[self.window.res_index]) + " x " + str(self.window.h_scale[self.window.res_index])
        self.resolution_box.add(
            resolution_up_button.with_space_around(right=0))
        resolution_up_button.on_click = self.on_click_resolution_up
        resolution_down_button.on_click = self.on_click_resolution_down

        # Rest buttons
        back_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.BACK, width=120, style=utils.Style.BUTTON_DEFAULT
        )
        start_view_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.START_MENU, width=180, style=utils.Style.BUTTON_DEFAULT
        )
        quit_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.QUIT, width=120, style=utils.Style.BUTTON_DEFAULT
        )
        self.rest_box.add(back_button.with_space_around(right=100))
        self.rest_box.add(start_view_button.with_space_around(right=100))
        self.rest_box.add(quit_button.with_space_around(right=0))
        back_button.on_click = self.on_click_back
        start_view_button.on_click = self.on_click_start_menu
        quit_button.on_click = self.on_click_quit

        # Add box layouts
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                align_y=220, child=self.lang_box)
        )
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                align_y=140, child=self.effect_volume_box)
        )
        self.manager.add(
            arcade.gui.UIAnchorWidget(align_y=60, child=self.music_volume_box)
        )
        self.manager.add(arcade.gui.UIAnchorWidget(
            align_y=-20, child=self.screen_box))
        self.manager.add(
            arcade.gui.UIAnchorWidget(align_y=-100, child=self.resolution_box)
        )
        self.manager.add(arcade.gui.UIAnchorWidget(
            align_y=-240, child=self.rest_box))

    def on_draw(self) -> None:
        self.clear()
        self.manager.draw()

    def on_key_press(self, key, modifiers) -> None:
        if key == arcade.key.ESCAPE:
            self.on_click_back(event=None)

    def on_click_effect_volume_up(self, event) -> None:
        self.window.effect_volume = min(20, self.window.effect_volume + 1)
        self.effect_volume_text.text = str(self.window.effect_volume)
        self.window.play_button_sound()

    def on_click_effect_volume_down(self, event) -> None:
        self.window.effect_volume = max(0, self.window.effect_volume - 1)
        self.effect_volume_text.text = str(self.window.effect_volume)
        self.window.play_button_sound()

    def on_click_music_volume_up(self, event) -> None:
        self.window.music_volume = min(20, self.window.music_volume + 1)
        self.music_volume_text.text = str(self.window.music_volume)
        self.window.play_button_sound()
        self.window.update_music_volume()

    def on_click_music_volume_down(self, event) -> None:
        self.window.music_volume = max(0, self.window.music_volume - 1)
        self.music_volume_text.text = str(self.window.music_volume)
        self.window.play_button_sound()
        self.window.update_music_volume()

    def on_click_fullscreen(self, event) -> None:
        self.window.set_fullscreen(not self.window.fullscreen)
        self.fullscreen_text.text = str(self.window.fullscreen)
        width, height = self.window.get_size()
        self.window.set_viewport(0, width, 0, height)
        if self.window.fullscreen:
            self.resolution_text.text = self.window.cur_lang.FULLSCREEN
        else:
            self.resolution_text.text = str(
                self.window.w_scale[self.window.res_index]) + " x " + str(self.window.h_scale[self.window.res_index])
        self.window.play_button_sound()

    def on_click_resolution_up(self, event) -> None:
        if self.window.fullscreen:
            return
        self.window.res_index += 1
        self.window.res_index %= 4
        self.window.set_size(self.window.w_scale[self.window.res_index],
                             self.window.h_scale[self.window.res_index])
        width, height = self.window.get_size()
        self.window.set_viewport(0, width, 0, height)
        self.resolution_text.text = str(
            self.window.w_scale[self.window.res_index]) + " x " + str(self.window.h_scale[self.window.res_index])
        self.window.play_button_sound()

    def on_click_resolution_down(self, event) -> None:
        if self.window.fullscreen:
            return
        self.window.res_index -= 1
        self.window.res_index %= 4
        self.window.set_size(self.window.w_scale[self.window.res_index],
                             self.window.h_scale[self.window.res_index])
        width, height = self.window.get_size()
        self.window.set_viewport(0, width, 0, height)
        self.resolution_text.text = str(
            self.window.w_scale[self.window.res_index]) + " x " + str(self.window.h_scale[self.window.res_index])
        self.window.play_button_sound()

    def on_click_back(self, event) -> None:
        utils.Utils.clear_ui_manager(self.manager)
        if type(self.last_view) == StartView:
            self.last_view.setup()
        self.last_view.resize_camera(self.window.width, self.window.height)
        self.window.show_view(self.last_view)
        self.window.play_button_sound()

    def on_click_start_menu(self, event) -> None:
        self.last_view = None
        utils.Utils.clear_ui_manager(self.manager)
        self.window.start_view.setup()
        self.window.start_view.resize_camera(
            self.window.width, self.window.height)
        self.window.show_view(self.window.start_view)
        self.window.play_button_sound()

    def on_click_quit(self, event) -> None:
        self.window.play_button_sound()
        utils.Utils.save_settings(self.window)
        arcade.exit()

    def on_click_lang_left(self, event) -> None:
        idx = self.window.lang_idx - 1
        idx = idx % len(self.window.lang)
        self.window.set_cur_lang(idx)
        self.setup(self.last_view)

    def on_click_lang_right(self, event) -> None:
        idx = self.window.lang_idx + 1
        idx = idx % len(self.window.lang)
        self.window.set_cur_lang(idx)
        self.setup(self.last_view)

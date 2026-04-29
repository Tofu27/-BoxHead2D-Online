import arcade
from views.base_view import FadingView
from utils.utils import Utils
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from entities.room import StartRoom, GameRoom0
from utils.utils import Color, Style
from entities.character import CreatePlayer, CHARACTER_REGISTRY
from views.base_view import CAMERA_SPEED
from views.game_view import GameView
from network.http import HttpCreatePlayer

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
        self.player = CreatePlayer(
            char_type="Player", 
            x=float(self.w / 2), 
            y=float(self.h / 2) + 20, 
            physics_engine=self.physics_engine, 
            is_remote=False
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



class SelectionView(FadingView):
    """Character and map selection."""
        

    def on_show_view(self) -> None:
        arcade.set_background_color(Color.GROUND_WHITE)

    def setup(self) -> None:
        self.w = self.window.width
        self.h = self.window.height

        self.playerUUID = None
        self.playerName = None

        self.name_list = []
        self.describe_list = []
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.selection_box = arcade.gui.UIBoxLayout(vertical=False)
        self.rest_box = arcade.gui.UIBoxLayout(vertical=False)

        # 名字输入与联机按钮
        input_h_box = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        self.name_input = arcade.gui.UIInputText(
            width=200, height=30, text="",
            font_size=16, text_color=arcade.color.BLACK,
            border_color=arcade.color.GRAY, caret_color=arcade.color.RED,
            bg_color=arcade.color.WHITE,
        )
        self.confirm_name_button = arcade.gui.UIFlatButton(
            text="创建玩家", width=120, style=Style.BUTTON_DEFAULT
        )
        input_h_box.add(self.name_input)
        input_h_box.add(self.confirm_name_button)

        # 提示标签
        self.input_error_label = arcade.gui.UILabel(
            text="", font_size=14, align="center",
            width=320, height=20,
            text_color=(255, 0, 0, 255)
        )
        
        # 垂直布局整合
        input_v_box = arcade.gui.UIBoxLayout(vertical=True, space_between=5)
        input_v_box.add(input_h_box)
        input_v_box.add(self.input_error_label)

        
        # 绑定事件
        @self.name_input.event("on_change")
        def on_name_change(event):
            if len(event.new_value) > 6:
                self.name_input.text = event.new_value[:6]
            self.input_error_label.text = ""


        # Characters
        self.char_sprites = arcade.SpriteList()
        self.char_types = ["Player", "Rambo", "Redbit"]
        self.cur_char_idx = 0
        self.cur_char = CreatePlayer(
            char_type=self.char_types[0],
            x=float(self.w/2 - 240), 
            y=float(self.h/2 + 100),
            physics_engine=None,
            is_remote=False
        )
        self.cur_char.center_x = float(self.w/2 - 240)
        self.cur_char.center_y = float(self.h/2 + 100)

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
                color=Color.BLACK,
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
                color=Color.BLACK,
            )
        )
        self.set_character(0)


        # Maps
        self.map_list = [
            GameRoom0,
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
                color=Color.BLACK,
            )
        )
        self.set_maps()
        
        # Selection buttons
        character_left_button = arcade.gui.UIFlatButton(
            text="<", width=60, style=Style.BUTTON_DEFAULT
        )
        character_right_button = arcade.gui.UIFlatButton(
            text=">", width=60, style=Style.BUTTON_DEFAULT
        )
        map_left_button = arcade.gui.UIFlatButton(
            text="<", width=80, style=Style.BUTTON_DEFAULT
        )
        map_right_button = arcade.gui.UIFlatButton(
            text=">", width=80, style=Style.BUTTON_DEFAULT
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
            text=self.window.cur_lang.BACK, width=120, style=Style.BUTTON_DEFAULT
        )
        next_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.NEXT, width=120, style=Style.BUTTON_DEFAULT
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
        
        # 将垂直布局添加到 manager（替换原有的直接添加 input_h_box）
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center", anchor_y="top",
                align_x=20, align_y=-50,
                child=input_v_box
            )
        )

        @self.confirm_name_button.event("on_click")
        def on_confirm_name(event):
            name = self.name_input.text.strip()
            if not name:
                self.input_error_label.text = "名字不能为空！"
                self.input_error_label.color = arcade.color.RED
                return
            elif len(name) > 6:
                self.input_error_label.text = "名字长度不能超过6个字符！"
                self.input_error_label.color = arcade.color.RED
                return
            
            info, err = HttpCreatePlayer(name)
            if err is not None:
                self.input_error_label.text = err
                self.input_error_label.color = arcade.color.RED
                return

            self.input_error_label.text = f"✓ 名字已设为：{name}"
            self.input_error_label.color = arcade.color.GREEN
            self.playerUUID = info['uuid']
            self.playerName = info['username']
            arcade.schedule(self.clear_input_message, 3.0)
        
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
        self.cur_char_idx = (self.cur_char_idx + idx) % len(self.char_types)
        char_type = self.char_types[self.cur_char_idx]
        config = CHARACTER_REGISTRY[char_type]
        # 更换纹理
        self.cur_char.body.texture = arcade.load_texture(config["texture"])
        # 更新本地化文本
        self.name_list[0].text = self.window.cur_lang.DescribeText.get(
            config["name"], config["name"]
        )
        self.describe_list[0].text = self.window.cur_lang.DescribeText.get(
            config["description"], config["description"]
        )
        # 刷新绘制列表
        self.char_sprites.clear()
        self.char_sprites.extend(self.cur_char.parts)

    def clear_input_message(self, delta_time: float):
        self.input_error_label.text = ""
        arcade.unschedule(self.clear_input_message)

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
        Utils.clear_ui_manager(self.manager)
        self.window.start_view.setup()
        self.window.start_view.resize_camera(
            self.window.width, self.window.height)
        self.window.show_view(self.window.start_view)
        self.window.play_button_sound()

    def on_click_next(self, event) -> None:
        if not self.playerUUID:
            self.input_error_label.text = "需要先创建玩家"
            self.input_error_label.color = arcade.color.RED
            arcade.schedule(self.clear_input_message, 3.0)
            return

        player_meta = {
            "uuid": self.playerUUID,
            "name": self.playerName,
            "player_char_type": self.char_types[self.cur_char_idx],
        }

        Utils.clear_ui_manager(self.manager)
        self.window.game_view = GameView()
        self.window.game_view.setup(
            player_meta, self.cur_map)
        self.window.show_view(self.window.game_view)
        self.window.play_button_sound()

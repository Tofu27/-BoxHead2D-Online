import arcade
from views.base_view import FadingView
from utils.utils import Utils, Color, Style
from views.start_view import StartView
from views.game_view import GameView
from entities.character import Character, Player, Rambo, Redbit
from entities.room import GameRoom0

# ==================== 默认启动视图（按任意键） ====================
class DefaultView(FadingView):
    """游戏启动时显示的视图，提示按任意键继续。"""

    def setup(self) -> None:
        """设置背景、标题Logo和闪烁文字。"""
        arcade.set_background_color(Color.GROUND_WHITE)
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


class OptionView(arcade.View):
    """Optional menu."""

    def __init__(self):
        super().__init__()
        self.manager = None
        self.last_view = None

    def on_show_view(self) -> None:
        arcade.set_background_color(Color.GROUND_WHITE)
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
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        lang_left_button = arcade.gui.UIFlatButton(
            text="<", width=60, style=Style.BUTTON_DEFAULT
        )
        lang_text = arcade.gui.UITextArea(
            text=self.window.cur_lang.CUR_LANG,
            width=120,
            height=40,
            font_size=24,
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        lang_right_button = arcade.gui.UIFlatButton(
            text=">", width=60, style=Style.BUTTON_DEFAULT
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
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        effect_volume_down_button = arcade.gui.UIFlatButton(
            text="-", width=60, style=Style.BUTTON_DEFAULT
        )
        self.effect_volume_text = arcade.gui.UITextArea(
            text=str(self.window.effect_volume),
            width=40,
            height=40,
            font_size=24,
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        effect_volume_up_button = arcade.gui.UIFlatButton(
            text="+", width=60, style=Style.BUTTON_DEFAULT
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
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        music_volume_down_button = arcade.gui.UIFlatButton(
            text="-", width=60, style=Style.BUTTON_DEFAULT
        )
        self.music_volume_text = arcade.gui.UITextArea(
            text=str(self.window.music_volume),
            width=40,
            height=40,
            font_size=24,
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        music_volume_up_button = arcade.gui.UIFlatButton(
            text="+", width=60, style=Style.BUTTON_DEFAULT
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
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        self.fullscreen_text = arcade.gui.UITextArea(
            text=str(self.window.fullscreen),
            width=120,
            height=40,
            font_size=24,
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        fullscreen_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.SWITCH, width=120, style=Style.BUTTON_DEFAULT
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
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        resolution_down_button = arcade.gui.UIFlatButton(
            text="<", width=60, style=Style.BUTTON_DEFAULT
        )
        self.resolution_text = arcade.gui.UITextArea(
            text="1280 x 720",
            width=200,
            height=40,
            font_size=24,
            text_color=Color.BLACK,
            font_name="Cubic 11",
        )
        resolution_up_button = arcade.gui.UIFlatButton(
            text=">", width=60, style=Style.BUTTON_DEFAULT
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
            text=self.window.cur_lang.BACK, width=120, style=Style.BUTTON_DEFAULT
        )
        start_view_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.START_MENU, width=180, style=Style.BUTTON_DEFAULT
        )
        quit_button = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.QUIT, width=120, style=Style.BUTTON_DEFAULT
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
        Utils.clear_ui_manager(self.manager)
        if type(self.last_view) == StartView:
            self.last_view.setup()
        self.last_view.resize_camera(self.window.width, self.window.height)
        self.window.show_view(self.last_view)
        self.window.play_button_sound()

    def on_click_start_menu(self, event) -> None:
        self.last_view = None
        Utils.clear_ui_manager(self.manager)
        self.window.start_view.setup()
        self.window.start_view.resize_camera(
            self.window.width, self.window.height)
        self.window.show_view(self.window.start_view)
        self.window.play_button_sound()

    def on_click_quit(self, event) -> None:
        self.window.play_button_sound()
        Utils.save_settings(self.window)
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


class SelectionView(FadingView):
    """Character and map selection."""

    def on_show_view(self) -> None:
        arcade.set_background_color(Color.GROUND_WHITE)

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
            Player,
            Rambo,
            Redbit,
        ]
        self.cur_char_idx = 0
        self.cur_char = Character(
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
        self.set_character()


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
        Utils.clear_ui_manager(self.manager)
        self.window.start_view.setup()
        self.window.start_view.resize_camera(
            self.window.width, self.window.height)
        self.window.show_view(self.window.start_view)
        self.window.play_button_sound()

    def on_click_next(self, event) -> None:
        Utils.clear_ui_manager(self.manager)
        self.window.game_view = GameView()
        self.window.game_view.setup(
            self.char_list[self.cur_char_idx], self.cur_map)
        self.window.show_view(self.window.game_view)
        self.window.play_button_sound()
       
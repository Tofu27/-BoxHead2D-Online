import arcade
from views.base_view import FadingView
from utils.utils import Utils
from core.constants import Color, Style
from core.services.player_creator import PlayerCreator
from entities.character import CreatePlayer, CHARACTER_REGISTRY
from entities.room import GameRoom0
from views.game_view import GameView
class SelectionView(FadingView):
    """角色与地图选择视图（重构后）"""

    def __init__(self) -> None:
        super().__init__()
        self.w = 0
        self.h = 0

        # 玩家创建相关
        self.player_uuid: str = None
        self.player_name: str = None

        # UI 管理器
        self.manager = None

        # 角色选择
        self.char_types = ["Player", "Rambo", "Redbit"]
        self.cur_char_idx = 0
        self.cur_char = None          # 当前展示的角色实体
        self.char_sprites = None      # 用于绘制展示角色
        self.name_list = []           # 角色/地图名称文本
        self.describe_list = []       # 角色描述文本

        # 地图选择
        self.map_list = [GameRoom0]   # 可扩展更多地图
        self.cur_map_idx = 0
        self.cur_map = None
        self.cur_map_sprite = None

        # 名字输入
        self.name_input = None
        self.input_error_label = None

    def setup(self) -> None:
        """初始化 UI 和数据"""
        self.w = self.window.width
        self.h = self.window.height
        arcade.set_background_color(Color.GROUND_WHITE)

        # 重置状态
        self.player_uuid = None
        self.player_name = None

        # ----- UI 管理器 -----
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # ----- 名字输入区域 -----
        self._setup_name_input()

        # ----- 角色展示区域 -----
        self._setup_character_display()

        # ----- 地图展示区域 -----
        self._setup_map_display()

        # ----- 选择按钮（左右箭头） -----
        self._setup_selection_buttons()

        # ----- 底部按钮（返回 / 下一步） -----
        self._setup_bottom_buttons()

    # ---------- UI 搭建子方法 ----------
    def _setup_name_input(self):
        """创建名字输入框、确认按钮和错误提示"""
        input_h_box = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        self.name_input = arcade.gui.UIInputText(
            width=200, height=30, text="",
            font_size=16, text_color=arcade.color.BLACK,
            border_color=arcade.color.GRAY, caret_color=arcade.color.RED,
            bg_color=arcade.color.WHITE,
        )
        confirm_button = arcade.gui.UIFlatButton(
            text="创建玩家", width=120, style=Style.BUTTON_DEFAULT
        )
        input_h_box.add(self.name_input)
        input_h_box.add(confirm_button)

        self.input_error_label = arcade.gui.UILabel(
            text="", font_size=14, align="center",
            width=320, height=20,
            text_color=(255, 0, 0, 255)
        )

        input_v_box = arcade.gui.UIBoxLayout(vertical=True, space_between=5)
        input_v_box.add(input_h_box)
        input_v_box.add(self.input_error_label)

        # 绑定事件
        @self.name_input.event("on_change")
        def on_name_change(event):
            # 限制最多6个字符
            if len(event.new_value) > 6:
                self.name_input.text = event.new_value[:6]
            self.input_error_label.text = ""

        @confirm_button.event("on_click")
        def on_confirm(event):
            name = self.name_input.text.strip()
            if not name:
                self.input_error_label.text = "名字不能为空！"
                self.input_error_label.color = arcade.color.RED
                return
            if len(name) > 6:
                self.input_error_label.text = "名字长度不能超过6个字符！"
                self.input_error_label.color = arcade.color.RED
                return

            # 通过服务创建玩家
            info, err = PlayerCreator.create(name)
            if err:
                self.input_error_label.text = err
                self.input_error_label.color = arcade.color.RED
                return

            self.player_uuid = info["uuid"]
            self.player_name = info["name"]
            self.input_error_label.text = f"✓ 玩家创建成功：{self.player_name}"
            self.input_error_label.color = arcade.color.GREEN
            arcade.schedule(self._clear_message, 3.0)   # 3秒后清除提示

        # 定位到顶部
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center", anchor_y="top",
                align_x=20, align_y=-50,
                child=input_v_box
            )
        )

    def _setup_character_display(self):
        """创建角色展示精灵和描述文本"""
        self.char_sprites = arcade.SpriteList()
        self.cur_char = CreatePlayer(
            char_type=self.char_types[0],
            x=self.w / 2 - 240,
            y=self.h / 2 + 100,
            physics_engine=None,
            is_remote=False
        )
        self.cur_char.center_x = float(self.w / 2 - 240)
        self.cur_char.center_y = float(self.h / 2 + 100)

        self.name_list = []
        self.describe_list = []

        # 角色名称
        self.name_list.append(
            arcade.Text(
                text="",
                start_x=float(self.w/2 - 240),
                start_y=float(self.h/2 + 20),
                font_size=12, font_name="Cubic 11",
                anchor_x="center", align="center",
                width=120, color=Color.BLACK
            )
        )
        # 角色描述
        self.describe_list.append(
            arcade.Text(
                text="",
                start_x=float(self.w/2 - 240),
                start_y=float(self.h/2 - 10),
                font_size=12, font_name="Cubic 11",
                anchor_x="center", align="center",
                multiline=False, width=240, color=Color.BLACK
            )
        )
        self.set_character(0)   # 初始化第一个角色

    def _setup_map_display(self):
        """创建地图展示精灵和名称文本"""
        self.cur_map = self.map_list[0]
        self.cur_map_sprite = self.cur_map.layout_sprite
        self.cur_map_sprite.center_x = self.w / 2 + 220
        self.cur_map_sprite.center_y = self.h / 2 + 70

        # 地图名称文本（追加到 name_list）
        self.name_list.append(
            arcade.Text(
                text="",
                start_x=float(self.w/2 + 220),
                start_y=float(self.h/2 - 20),
                font_size=12, font_name="Cubic 11",
                anchor_x="center", align="center",
                width=120, color=Color.BLACK
            )
        )
        self.set_maps(0)   # 初始化第一个地图

    def _setup_selection_buttons(self):
        """角色和地图左右切换按钮"""
        selection_box = arcade.gui.UIBoxLayout(vertical=False)

        char_left_btn = arcade.gui.UIFlatButton(text="<", width=60, style=Style.BUTTON_DEFAULT)
        char_right_btn = arcade.gui.UIFlatButton(text=">", width=60, style=Style.BUTTON_DEFAULT)
        map_left_btn = arcade.gui.UIFlatButton(text="<", width=80, style=Style.BUTTON_DEFAULT)
        map_right_btn = arcade.gui.UIFlatButton(text=">", width=80, style=Style.BUTTON_DEFAULT)

        selection_box.add(char_left_btn.with_space_around(right=20))
        selection_box.add(char_right_btn.with_space_around(right=300))
        selection_box.add(map_left_btn.with_space_around(right=20))
        selection_box.add(map_right_btn.with_space_around(right=0))

        char_left_btn.on_click = lambda event: self.on_click_last_char(event)
        char_right_btn.on_click = lambda event: self.on_click_next_char(event)
        map_left_btn.on_click = lambda event: self.on_click_last_map(event)
        map_right_btn.on_click = lambda event: self.on_click_next_map(event)

        self.manager.add(
            arcade.gui.UIAnchorWidget(align_y=-100, child=selection_box)
        )

    def _setup_bottom_buttons(self):
        """返回和下一步按钮"""
        rest_box = arcade.gui.UIBoxLayout(vertical=False)
        back_btn = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.BACK, width=120, style=Style.BUTTON_DEFAULT
        )
        next_btn = arcade.gui.UIFlatButton(
            text=self.window.cur_lang.NEXT, width=120, style=Style.BUTTON_DEFAULT
        )
        rest_box.add(back_btn.with_space_around(right=200))
        rest_box.add(next_btn.with_space_around(right=0))

        back_btn.on_click = self.on_click_back
        next_btn.on_click = self.on_click_next

        self.manager.add(
            arcade.gui.UIAnchorWidget(align_y=-200, child=rest_box)
        )

    # ---------- 角色/地图切换 ----------
    def set_character(self, offset: int = 0) -> None:
        """切换展示的角色（offset 为相对移动格数）"""
        self.cur_char_idx = (self.cur_char_idx + offset) % len(self.char_types)
        char_type = self.char_types[self.cur_char_idx]
        config = CHARACTER_REGISTRY[char_type]

        # 更新角色精灵纹理
        self.cur_char.body.texture = arcade.load_texture(config["texture"])
        # 更新名称和描述（支持多语言）
        self.name_list[0].text = self.window.cur_lang.DescribeText.get(
            config["name"], config["name"]
        )
        self.describe_list[0].text = self.window.cur_lang.DescribeText.get(
            config["description"], config["description"]
        )
        # 更新精灵绘制列表
        self.char_sprites.clear()
        self.char_sprites.extend(self.cur_char.parts)

    def set_maps(self, offset: int = 0) -> None:
        """切换地图（offset 为相对移动格数）"""
        self.cur_map_idx = (self.cur_map_idx + offset) % len(self.map_list)
        self.cur_map = self.map_list[self.cur_map_idx]
        self.cur_map_sprite = self.cur_map.layout_sprite
        self.cur_map_sprite.center_x = self.w / 2 + 220
        self.cur_map_sprite.center_y = self.h / 2 + 70
        self.name_list[1].text = self.window.cur_lang.DescribeText.get(
            self.map_list[self.cur_map_idx].name,
            self.map_list[self.cur_map_idx].name
        )

    # ---------- 按钮事件 ----------
    def on_click_last_char(self, event=None):
        self.set_character(-1)
        self.window.play_button_sound()

    def on_click_next_char(self, event=None):
        self.set_character(1)
        self.window.play_button_sound()

    def on_click_last_map(self, event=None):
        self.set_maps(-1)
        self.window.play_button_sound()

    def on_click_next_map(self, event=None):
        self.set_maps(1)
        self.window.play_button_sound()

    def on_click_back(self, event=None):
        Utils.clear_ui_manager(self.manager)
        self.window.start_view.setup()
        self.window.start_view.resize_camera(self.window.width, self.window.height)
        self.window.show_view(self.window.start_view)
        self.window.play_button_sound()

    def on_click_next(self, event=None):
        if not self.player_uuid:
            self.input_error_label.text = "请先创建玩家"
            self.input_error_label.color = arcade.color.RED
            arcade.schedule(self._clear_message, 3.0)
            return

        player_meta = {
            "uuid": self.player_uuid,
            "name": self.player_name,
            "player_char_type": self.char_types[self.cur_char_idx],
        }
        Utils.clear_ui_manager(self.manager)
        self.window.game_view = GameView()
        self.window.game_view.setup(player_meta, self.cur_map)
        self.window.show_view(self.window.game_view)
        self.window.play_button_sound()

    # ---------- 辅助 ----------
    def _clear_message(self, delta_time: float):
        """定时清除提示文字"""
        self.input_error_label.text = ""
        arcade.unschedule(self._clear_message)

    # ---------- 视图更新与绘制 ----------
    def on_update(self, delta_time: float):
        """更新角色动画"""
        if self.cur_char:
            self.cur_char.update()

    def on_draw(self):
        self.clear()
        self.manager.draw()               # 绘制所有 UI 按钮
        if self.char_sprites:
            self.char_sprites.draw()      # 绘制角色展示精灵
        self.cur_map_sprite.draw()        # 绘制地图缩略图
        for txt in self.name_list:
            txt.draw()
        for txt in self.describe_list:
            txt.draw()
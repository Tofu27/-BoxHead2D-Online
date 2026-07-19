# views/connected_view.py
import arcade
import arcade.gui
from core.global_state import GlobalState, AppState
from core.proto import packets_pb2
from typing import Optional
import pyglet

# ===================== 样式常量（统一管理，兼容低版本arcade） =====================
# 配色
COLOR_BG = arcade.color.WHITE
COLOR_TEXT_PRIMARY = arcade.color.BLACK
COLOR_TEXT_SECONDARY = (100, 100, 100)
COLOR_TEXT_ERROR = (220, 50, 50)
COLOR_INPUT_BG = arcade.color.WHITE
COLOR_BTN_PRIMARY = (30, 144, 255)    # 主按钮蓝色
COLOR_BTN_SECONDARY = (240, 240, 240) # 次按钮浅灰
COLOR_BTN_TEXT_PRIMARY = arcade.color.WHITE
COLOR_BTN_TEXT_SECONDARY = COLOR_TEXT_PRIMARY

# 尺寸与间距
FORM_SPACING = 18
LABEL_WIDTH = 80
INPUT_WIDTH = 260
INPUT_HEIGHT = 36
BTN_WIDTH = 110
BTN_HEIGHT = 42
STATUS_HEIGHT = 24  # 固定错误提示高度，解决文本不显示问题


class ConnectedView(arcade.View):
    def __init__(self):
        super().__init__()
        self.g = GlobalState()
        self.ui_manager: Optional[arcade.gui.UIManager] = None
        self.username_input: Optional[arcade.gui.UIInputText] = None
        self.password_input: Optional[arcade.gui.UIInputText] = None
        self.status_label: Optional[arcade.gui.UILabel] = None
        self._pending_action: Optional[str] = None  # 'login' or 'register'
        self._ui_initialized = False

    # ===================== 视图生命周期 =====================
    def on_show_view(self):
        """视图显示时调用：初始化UI、启用输入"""
        arcade.set_background_color(COLOR_BG)
        if not self._ui_initialized:
            self._setup_ui()
            self._ui_initialized = True
        self.ui_manager.enable()

    def on_hide_view(self):
        """视图隐藏时调用：禁用输入，避免事件残留"""
        if self.ui_manager:
            self.ui_manager.disable()

    # ===================== UI构建 =====================
    def _setup_ui(self):
        """构建所有UI元素，仅初始化一次"""
        self.ui_manager = arcade.gui.UIManager()

        # 构建表单主体
        form_layout = self._build_form_layout()

        # 整体居中锚定
        anchor = arcade.gui.UIAnchorWidget(
            anchor_x="center_x",
            anchor_y="center_y",
            child=form_layout
        )
        self.ui_manager.add(anchor)

    def _build_form_layout(self) -> arcade.gui.UIBoxLayout:
        """构建表单垂直布局，兼容所有arcade版本"""
        form_layout = arcade.gui.UIBoxLayout(
            vertical=True,
            spacing=FORM_SPACING,
            align="center"
        )

        # 顶部标题
        title = arcade.gui.UILabel(
            text="登录 / 注册",
            font_size=32,
            text_color=COLOR_TEXT_PRIMARY,
            bold=True,
            align="center"
        )
        form_layout.add(title)

        # 用户名行
        form_layout.add(self._build_input_row("用户名:", "test", is_password=False))

        # 密码行
        form_layout.add(self._build_input_row("密  码:", "123", is_password=True))

        # 按钮行
        btn_row = arcade.gui.UIBoxLayout(vertical=False, spacing=20, align="center")
        btn_row.add(self._build_primary_button("登录", self._on_login_clicked))
        btn_row.add(self._build_secondary_button("注册", self._on_register_clicked))
        form_layout.add(btn_row)

        # 状态提示标签（固定高度！解决空文本时布局塌陷、错误不显示的核心问题）
        self.status_label = arcade.gui.UILabel(
            text="",
            text_color=COLOR_TEXT_ERROR,
            font_size=14,
            width=INPUT_WIDTH + LABEL_WIDTH + 10,
            height=STATUS_HEIGHT,
            align="center",
            multiline=False
        )
        form_layout.add(self.status_label)

        return form_layout

    def _build_input_row(self, label_text: str, default_text: str, is_password: bool = False) -> arcade.gui.UIBoxLayout:
        """构建「标签+输入框」的水平行，复用代码"""
        row = arcade.gui.UIBoxLayout(vertical=False, spacing=10, align="center")

        # 左侧标签
        label = arcade.gui.UILabel(
            text=label_text,
            width=LABEL_WIDTH,
            align="right",
            text_color=COLOR_TEXT_SECONDARY,
            font_size=16
        )
        row.add(label)

        # 右侧输入框（兼容低版本，移除边框、密码掩码等高级属性）
        input_widget = arcade.gui.UIInputText(
            width=INPUT_WIDTH,
            height=INPUT_HEIGHT,
            text=default_text,
            font_size=15,
            bg_color=COLOR_INPUT_BG
        )
        row.add(input_widget)

        # 保存输入框引用
        if is_password:
            self.password_input = input_widget
        else:
            self.username_input = input_widget

        return row

    def _build_primary_button(self, text: str, on_click) -> arcade.gui.UIFlatButton:
        """构建主按钮（蓝色强调，兼容低版本）"""
        btn = arcade.gui.UIFlatButton(
            text=text,
            width=BTN_WIDTH,
            height=BTN_HEIGHT,
            style={
                "bg_color": COLOR_BTN_PRIMARY,
                "font_color": COLOR_BTN_TEXT_PRIMARY,
                "font_size": 16
            }
        )
        btn.on_click = on_click
        return btn

    def _build_secondary_button(self, text: str, on_click) -> arcade.gui.UIFlatButton:
        """构建次按钮（灰色弱化，兼容低版本）"""
        btn = arcade.gui.UIFlatButton(
            text=text,
            width=BTN_WIDTH,
            height=BTN_HEIGHT,
            style={
                "bg_color": COLOR_BTN_SECONDARY,
                "font_color": COLOR_BTN_TEXT_SECONDARY,
                "font_size": 16
            }
        )
        btn.on_click = on_click
        return btn

    # ===================== 交互逻辑 =====================
    def _on_login_clicked(self, event):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        if not self._validate_input(username, password):
            return

        if not self._check_network():
            return

        # 发送登录包
        packet = packets_pb2.Packet()
        packet.login_request.username = username
        packet.login_request.password = password
        self.g.ws.send(packet)

        self._pending_action = 'login'
        self._set_status("正在登录...", COLOR_TEXT_SECONDARY)

    def _on_register_clicked(self, event):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        if not self._validate_input(username, password):
            return

        if not self._check_network():
            return

        # 发送注册包
        packet = packets_pb2.Packet()
        packet.register_request.username = username
        packet.register_request.password = password
        self.g.ws.send(packet)

        self._pending_action = 'register'
        self._set_status("正在注册...", COLOR_TEXT_SECONDARY)

    # ===================== 工具方法 =====================
    def _validate_input(self, username: str, password: str) -> bool:
        """输入校验，统一处理"""
        if not username or not password:
            self._set_status("用户名和密码不能为空", COLOR_TEXT_ERROR)
            return False
        return True

    def _check_network(self) -> bool:
        """网络连接检查，统一处理"""
        ws = self.g.ws
        if not ws or not ws.connected:
            self._set_status("未连接到服务器", COLOR_TEXT_ERROR)
            return False
        return True

    def _set_status(self, text: str, color: tuple):
        """统一设置状态文本，避免重复代码"""
        self.status_label.text = text
        self.status_label.text_color = color

    # ===================== 帧更新与渲染 =====================
    def on_update(self, delta_time):
        ws = self.g.ws
        if not ws:
            return

        pkt = ws.get_packet()
        if not pkt:
            return

        if pkt.HasField('ok_response'):
            self._set_status("操作成功！", (50, 180, 50))
            if self._pending_action in ('login', 'register'):
                pyglet.clock.schedule_once(lambda dt: self.g.switch_to(AppState.INHALL), 0.3)
            self._pending_action = None

        elif pkt.HasField('deny_response'):
            reason = pkt.deny_response.reason
            self._set_status(f"失败: {reason}", COLOR_TEXT_ERROR)
            self._pending_action = None

    def on_draw(self):
        self.clear()
        if self.ui_manager:
            self.ui_manager.draw()

        # 顶部辅助文字
        arcade.draw_text(
            "登录界面 (Connected)",
            self.window.width / 2,
            self.window.height - 30,
            COLOR_TEXT_PRIMARY,
            16,
            anchor_x="center"
        )
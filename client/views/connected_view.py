# views/connected_view.py
import arcade
import arcade.gui
from core.global_state import GlobalState, AppState
from core.proto import packets_pb2

class ConnectedView(arcade.View):
    """连接状态：登录/注册界面"""

    def __init__(self):
        super().__init__()
        self.g = GlobalState()
        self.manager = None
        self.username = "test"
        self.password = "123"
        self._action_on_ok = None  # 登录成功后的回调

    def setup(self):
        """切换到该状态时调用，创建 UI"""
        arcade.set_background_color(arcade.color.WHITE)

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # 用户名输入
        # ... 构建 UI（略，可参考你原来的 OptionView 写法）

        # 登录按钮回调
        # login_button.on_click = self._on_login_clicked

    def _on_login_clicked(self, event):
        """点击登录按钮"""
        ws = self.g.ws
        if not ws or not ws.connected:
            print("未连接到服务器")
            return

        # 构造 LoginRequest
        packet = packets_pb2.Packet()
        packet.login_request.username = self.username
        packet.login_request.password = self.password
        ws.send(packet)

        # 设置成功回调
        # self._action_on_ok = lambda: self.g.switch_to(AppState.INGAME)

    def on_update(self, delta_time):
        ws = self.g.ws
        if ws:
            pkt = ws.get_packet()
            if pkt:
                if pkt.HasField('ok_response'):
                    if self._action_on_ok:
                        self._action_on_ok()
                        self._action_on_ok = None
                elif pkt.HasField('deny_response'):
                    print(f"登录失败: {pkt.deny_response.reason}")

    def on_draw(self):
        self.clear()
        if self.manager:
            self.manager.draw()
        arcade.draw_text("登录界面 (Connected)", 
                         self.window.width/2, self.window.height - 50,
                         arcade.color.BLACK, 20, anchor_x="center")
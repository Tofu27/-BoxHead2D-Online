# views/entered_view.py
import arcade
from core.global_state import GlobalState, AppState
from core.ws_client import WSClient
from core.proto import packets_pb2

class EnteredView(arcade.View):
    """进入状态视图：连接服务器，等待 ID"""

    def __init__(self):
        super().__init__()
        self.g = GlobalState()
        self.connected = False

    def setup(self):
        """类似于 Godot 的 _ready()，在切换到这个状态时调用"""

        print("EnteredView: 正在连接服务器...")
        # 连接 WebSocket
        ws = self.g.ws
        if ws and not ws.connected:
            ws.connect()

    def on_draw(self):
        self.clear()
        arcade.draw_text("正在连接服务器...", 
                         self.window.width/2, self.window.height/2,
                         arcade.color.WHITE, 24, anchor_x="center")

    def on_update(self, delta_time):
        # 检查是否收到消息
        ws = self.g.ws
        if ws:
            pkt = ws.get_packet()
            if pkt and pkt.HasField('id'):
                # 收到 ID，保存并切换到 CONNECTED
                self.g.client_id = pkt.id.client_id
                print(f"获得客户端 ID: {self.g.client_id}")
                self.g.switch_to(AppState.CONNECTED)
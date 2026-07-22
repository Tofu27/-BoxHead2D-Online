import arcade
from core.global_state import GlobalState, AppState
from core.ws_client import WSClient
from core.proto import packets_pb2

class InGameView(arcade.View):
    """进入状态视图：连接服务器，等待 ID"""

    def __init__(self):
        super().__init__()
        self.g = GlobalState()

    def setup(self):
        """类似于 Godot 的 _ready()，在切换到这个状态时调用"""


    def on_draw(self):
        pass

    def on_update(self, delta_time):
        # 检查是否收到消息
        pass
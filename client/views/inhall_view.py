# views/entered_view.py
import arcade
from core.global_state import GlobalState, AppState

class InHallView(arcade.View):
    """进入状态视图：连接服务器，等待 ID"""

    def __init__(self):
        super().__init__()
        self.g = GlobalState()

    def setup(self):
        """类似于 Godot 的 _ready()，在切换到这个状态时调用"""

        print("InHallView: 正在连接服务器...")
       

    def on_draw(self):
        self.clear()
        arcade.draw_text("大厅内...", 
                         self.window.width/2, self.window.height/2,
                         arcade.color.WHITE, 24, anchor_x="center")

    def on_update(self, delta_time):
       pass
# app.py
import os
import sys


# 将 proto 目录加入 Python 搜索路径
proto_dir = os.path.join(os.path.dirname(__file__), "core", "proto")
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir)


import arcade
import pickle
from core.global_state import GlobalState, AppState
from core.ws_client import WSClient
from views.entered_view import EnteredView
from views.connected_view import ConnectedView
from views.ingame_view import InGameView



class BoxHead2d(arcade.Window):
    def __init__(self):
        # ... 原有 settings 加载（保留）...
        super().__init__(1024, 600, "BoxHead2D Online")
        self.set_fullscreen(False)

        # 1. 初始化全局状态
        self.g = GlobalState()
        self.g.window = self

        # 2. 创建 WebSocket 客户端（不立即连接，由 EnteredView 负责连接）
        self.g.ws = WSClient("ws://localhost:8080/ws")

        # 3. 注册所有状态视图
        entered_view = EnteredView()
        connected_view = ConnectedView()
        ingame_view = InGameView()

        self.g.register_state(AppState.ENTERED, entered_view, "ENTERED")
        self.g.register_state(AppState.CONNECTED, connected_view, "CONNECTED")
        self.g.register_state(AppState.INGAME, ingame_view, "INGAME")

        # 4. 切换到初始状态：ENTERED（自动连接服务器）
        self.g.switch_to(AppState.ENTERED)

    # ... 保留原有的 set_up、音效等方法（如果需要）...

def main():
    print("=== 程序启动 ===")
    game = BoxHead2d()
    arcade.run()

if __name__ == "__main__":
    main()
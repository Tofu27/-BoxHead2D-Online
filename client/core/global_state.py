# core/global_state.py
from enum import Enum, auto
import arcade
from typing import Dict, Optional

class AppState(Enum):
    ENTERED = auto()      # 进入应用，连接服务器
    CONNECTED = auto()    # 已连接，显示登录界面
    INHALL = auto()       # 已登录，进入大厅


class GlobalState:
    _instance: Optional['GlobalState'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 确保只初始化一次
        if not hasattr(self, '_initialized'):
            self._state_scenes: Dict[AppState, str] = {}
            self._views: Dict[str, arcade.View] = {}
            self._current_state: Optional[AppState] = None
            self._current_view: Optional[arcade.View] = None
            self.window: Optional[arcade.Window] = None
            self.ws = None
            self.client_id: int = 0
            self._initialized = True

    def register_state(self, state: AppState, view: arcade.View, view_name: str):
        """注册状态对应的视图"""
        self._state_scenes[state] = view_name
        self._views[view_name] = view

    def switch_to(self, state: AppState):
        """
        切换状态（核心方法）
        类似 Godot 的 GameManager.set_state()
        """

        print(f"切换状态到: {state.name}", flush=True)
        
        if self._current_state == state:
            return

        # 获取目标视图名称
        view_name = self._state_scenes.get(state)
        if not view_name:
            print(f"错误：状态 {state} 未注册视图")
            return

        # 获取或创建视图实例
        view = self._views.get(view_name)
        if not view:
            print(f"错误：视图 {view_name} 未注册")
            return

        # 如果视图有 setup 方法，调用它（类似 Godot 的 _ready()）
        if hasattr(view, "setup") and callable(view.setup):
            view.setup()

        # 切换视图
        self.window.show_view(view)
        self._current_state = state
        self._current_view = view


    @property
    def current_state(self) -> AppState:
        return self._current_state
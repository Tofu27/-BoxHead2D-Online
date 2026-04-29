import asyncio
import json
import threading
import websockets
from typing import Callable, List, Optional, Dict, Any


class GameWebSocketClient:
    """
    游戏 WebSocket 客户端。
    在独立线程中运行异步事件循环，负责与游戏服务器的 WebSocket 连接、自动重连、
    接收游戏状态消息并分发至回调函数，同时支持线程安全地发送 JSON 数据。
    """

    def __init__(self,
                 server_url: str,
                 player_uuid: str,
                 on_game_state: Callable[[List[Dict[str, Any]]], None],
                 on_connected: Optional[Callable[[], None]] = None,
                 on_error: Optional[Callable[[str], None]] = None,
                 on_close: Optional[Callable[[], None]] = None):
        """
        初始化 WebSocket 客户端。

        :param server_url: WebSocket 服务器地址，例如 "ws://127.0.0.1:8000/ws"
        :param player_uuid: 玩家唯一标识，将作为查询参数附加到 URL 中
        :param on_game_state: 接收到游戏状态消息时的回调，参数为玩家数据列表
        :param on_connected: 连接建立成功后的回调（用于发送 join 等初始化消息）
        :param on_error: 发生致命错误时的回调
        :param on_close: 连接关闭时的回调
        """
        self.server_url = server_url
        self.player_uuid = player_uuid
        self.on_game_state = on_game_state
        self.on_connected = on_connected
        self.on_error = on_error
        self.on_close = on_close

        # WebSocket 连接对象（在异步任务中赋值）
        self._ws = None
        # 独立线程中的异步事件循环
        self._loop = None
        # 后台线程对象
        self._thread = None
        # 运行标志，用于控制客户端生命周期
        self._running = False
        # 断线重连等待秒数
        self._reconnect_delay = 3

    def start(self):
        """启动客户端：在后台线程中启动异步事件循环并尝试连接。"""
        if self._running:
            return
        self._running = True
        # 创建守护线程，主线程退出时自动终止
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止客户端：关闭 WebSocket 连接并等待线程结束。"""
        self._running = False
        if self._loop and self._ws:
            # 通过事件循环安全地关闭 WebSocket 连接
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def send_json(self, data: dict):
        """
        线程安全地发送 JSON 数据。
        将数据编码为 JSON 字符串并通过 WebSocket 发送。
        """
        if not self._running or not self._ws or not self._loop:
            return
        # 将协程提交到异步事件循环中执行
        asyncio.run_coroutine_threadsafe(
            self._ws.send(json.dumps(data)), self._loop
        )

    def _run_async_loop(self):
        """后台线程入口：创建新的事件循环并运行客户端主任务。"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._client_task())

    async def _client_task(self):
        """
        客户端主异步任务：
        - 不断尝试连接（带重连延迟）
        - 连接成功后处理消息接收
        - 连接断开后自动重连
        """
        while self._running:
            try:
                # 将玩家 UUID 作为查询参数附加到 URL
                uri = f"{self.server_url}?uuid={self.player_uuid}"
                # 建立 WebSocket 连接，设置心跳间隔、超时和关闭超时
                async with websockets.connect(uri, ping_interval=20,
                                             ping_timeout=10, close_timeout=5) as ws:
                    self._ws = ws
                    # 连接成功，调用同步回调（通常用于发送 "join" 等消息）
                    if self.on_connected:
                        self.on_connected()
                    # 持续接收消息，直到连接关闭
                    async for raw_msg in ws:
                        await self._handle_message(raw_msg)
            except (websockets.ConnectionClosed, OSError) as e:
                # 网络层面的断开或操作系统错误，等待后重连
                print(f"WebSocket 断开: {e}, {self._reconnect_delay} 秒后重连")
                await asyncio.sleep(self._reconnect_delay)
            except Exception as e:
                # 其他致命异常，触发错误回调并退出循环
                print(f"WebSocket 错误: {e}")
                if self.on_error:
                    self.on_error(str(e))
                break
        # 清理连接对象，触发关闭回调
        self._ws = None
        if self.on_close:
            self.on_close()

    async def _handle_message(self, raw_msg: str):
        """
        处理接收到的原始 WebSocket 消息。
        约定消息格式为 JSON，包含 "type" 字段。
        当前仅处理类型为 "game_state" 的消息，提取玩家快照列表并调用回调。
        """
        try:
            data = json.loads(raw_msg)
            msg_type = data.get("type")
            if msg_type == "game_state":
                snapshots = data.get("snapshots", {})
                players_data = snapshots.get("Players", [])
                # 确保玩家数据为列表类型，否则输出警告
                if isinstance(players_data, list):
                    self.on_game_state(players_data)
                else:
                    print(f"意外格式: players 不是列表，是 {type(players_data)}")
            # 可在此扩展其他消息类型的处理（如错误、心跳等）
        except Exception as e:
            print(f"解析消息失败: {e}")
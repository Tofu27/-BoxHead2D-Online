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
                 serverUrl: str,
                 playerUUID: str,
                 onGameState: Callable[[List[Dict[str, Any]]], None],
                 onConnected: Optional[Callable[[], None]] = None,
                 onError: Optional[Callable[[str], None]] = None,
                 onClose: Optional[Callable[[], None]] = None):
        """
        初始化 WebSocket 客户端。

        :param serverUrl: WebSocket 服务器地址，例如 "ws://127.0.0.1:8000/ws"
        :param playerUUID: 玩家唯一标识，将作为查询参数附加到 URL 中
        :param onGameState: 接收到游戏状态消息时的回调，参数为玩家数据列表
        :param onConnected: 连接建立成功后的回调（用于发送 join 等初始化消息）
        :param onError: 发生致命错误时的回调
        :param onClose: 连接关闭时的回调
        """
        self.serverUrl = serverUrl
        self.playerUUID = playerUUID
        self.onGameState = onGameState
        self.onConnected = onConnected
        self.onError = onError
        self.onClose = onClose

        # WebSocket 连接对象（在异步任务中赋值）
        self._ws = None
        # 独立线程中的异步事件循环
        self._loop = None
        # 后台线程对象
        self._thread = None
        # 运行标志，用于控制客户端生命周期
        self._running = False
        # 断线重连等待秒数
        self._reconnectDelay = 3

    def Start(self):
        """启动客户端：在后台线程中启动异步事件循环并尝试连接。"""
        if self._running:
            return
        self._running = True
        # 创建守护线程，主线程退出时自动终止
        self._thread = threading.Thread(target=self._RunAsyncLoop, daemon=True)
        self._thread.start()

    def Stop(self):
        """停止客户端：关闭 WebSocket 连接并等待线程结束。"""
        self._running = False
        if self._loop and self._ws:
            # 通过事件循环安全地关闭 WebSocket 连接
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def SendJsonMsg(self, data: dict):
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

    def _RunAsyncLoop(self):
        """后台线程入口：创建新的事件循环并运行客户端主任务。"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._ClientTask())

    async def _ClientTask(self):
        """
        客户端主异步任务：
        - 不断尝试连接（带重连延迟）
        - 连接成功后处理消息接收
        - 连接断开后自动重连
        """
        while self._running:
            try:
                # 将玩家 UUID 作为查询参数附加到 URL
                uri = f"{self.serverUrl}?uuid={self.playerUUID}"
                # 建立 WebSocket 连接，设置心跳间隔、超时和关闭超时
                async with websockets.connect(uri, ping_interval=20,
                                             ping_timeout=10, close_timeout=5) as ws:
                    self._ws = ws
                    # 连接成功，调用同步回调（通常用于发送 "join" 等消息）
                    if self.onConnected:
                        self.onConnected()
                    # 持续接收消息，直到连接关闭
                    async for rawMsg in ws:
                        await self._HandleMessage(rawMsg)
            except (websockets.ConnectionClosed, OSError) as e:
                # 网络层面的断开或操作系统错误，等待后重连
                print(f"WebSocket 断开: {e}, {self._reconnectDelay} 秒后重连")
                await asyncio.sleep(self._reconnectDelay)
            except Exception as e:
                # 其他致命异常，触发错误回调并退出循环
                print(f"WebSocket 错误: {e}")
                if self.onError:
                    self.onError(str(e))
                break
        # 清理连接对象，触发关闭回调
        self._ws = None
        if self.onClose:
            self.onClose()

    async def _HandleMessage(self, rawMsg: str):
        """
        处理接收到的原始 WebSocket 消息。
        约定消息格式为 JSON，包含 "type" 字段。
        当前仅处理类型为 "game_state" 的消息，提取玩家快照列表并调用回调。
        """
        try:
            data = json.loads(rawMsg)
            msgType = data.get("type")
            if msgType == "game_state":
                snapshots = data.get("snapshots", {})
                playersData = snapshots.get("Players", [])
                # 确保玩家数据为列表类型，否则输出警告
                if isinstance(playersData, list):
                    self.onGameState(playersData)
                else:
                    print(f"意外格式: players 不是列表，是 {type(playersData)}")
            # 可在此扩展其他消息类型的处理（如错误、心跳等）
        except Exception as e:
            print(f"解析消息失败: {e}")
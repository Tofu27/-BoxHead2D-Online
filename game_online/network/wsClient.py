import asyncio
import json
import threading
import websockets
from typing import Callable, List, Optional, Dict, Any


class GameWebSocketClient:
    def __init__(self,
                 server_url: str,
                 player_uuid: str,
                 on_game_state: Callable[[List[Dict[str, Any]]], None],
                 on_connected: Optional[Callable[[], None]] = None,
                 on_error: Optional[Callable[[str], None]] = None,
                 on_close: Optional[Callable[[], None]] = None):
        
        self.server_url = server_url
        self.player_uuid = player_uuid
        self.on_game_state = on_game_state
        self.on_connected = on_connected
        self.on_error = on_error
        self.on_close = on_close

        self._ws = None
        self._loop = None
        self._thread = None
        self._running = False
        self._reconnect_delay = 3

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._loop and self._ws:
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def send_json(self, data: dict):
        """线程安全的 JSON 发送"""
        if not self._running or not self._ws or not self._loop:
            return
        asyncio.run_coroutine_threadsafe(
            self._ws.send(json.dumps(data)), self._loop
        )

    def _run_async_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._client_task())

    async def _client_task(self):
        while self._running:
            try:
                uri = f"{self.server_url}?uuid={self.player_uuid}"
                async with websockets.connect(uri, ping_interval=20,
                                             ping_timeout=10, close_timeout=5) as ws:
                    self._ws = ws
                    # 连接成功回调（同步，由上层发送 join 等）
                    if self.on_connected:
                        self.on_connected()
                    async for raw_msg in ws:
                        await self._handle_message(raw_msg)
            except (websockets.ConnectionClosed, OSError) as e:
                print(f"WebSocket 断开: {e}, {self._reconnect_delay} 秒后重连")
                await asyncio.sleep(self._reconnect_delay)
            except Exception as e:
                print(f"WebSocket 错误: {e}")
                if self.on_error:
                    self.on_error(str(e))
                break
        self._ws = None
        if self.on_close:
            self.on_close()

    async def _handle_message(self, raw_msg):
        try:
            data = json.loads(raw_msg)
            msg_type = data.get("type")
            if msg_type == "game_state":
                snapshots = data.get("snapshots", {})
                players_data = snapshots.get("Players", [])
                if isinstance(players_data, list):
                    self.on_game_state(players_data)
                else:
                    print(f"意外格式: players 不是列表，是 {type(players_data)}")
            # 可扩展其他消息类型
        except Exception as e:
            print(f"解析消息失败: {e}")
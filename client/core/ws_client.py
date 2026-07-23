# core/ws_client.py
import threading
import queue
import websocket
import pyglet
from core.proto import packets_pb2


class WSClient:
    def __init__(self, uri="ws://localhost:8080/ws"):
        self.uri = uri
        self.ws = None
        self.recv_queue = queue.Queue()
        self.connected = False
        self._thread = None

        # ✅ 通用回调列表（类似 Godot 的信号连接）
        self._packet_callbacks = []

    def connect(self):
        """启动后台连接线程"""
        self.ws = websocket.WebSocketApp(
            self.uri,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self._thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self._thread.start()

    def _on_open(self, ws):
        self.connected = True
        print("WebSocket 已连接")

    def _on_message(self, ws, message):
        pkt = packets_pb2.Packet()
        pkt.ParseFromString(message)
        self.recv_queue.put(pkt)
        # ✅ 主动调度到主线程分发
        pyglet.clock.schedule_once(self._dispatch_on_main, 0.0)

    def _on_error(self, ws, error):
        print("WebSocket 错误:", error)

    def _on_close(self, ws, close_code, reason):
        self.connected = False
        print("WebSocket 已关闭")

    def send(self, pkt: packets_pb2.Packet):
        if self.ws and self.connected:
            self.ws.send(pkt.SerializeToString())
        else:
            print("未连接，无法发送消息")

    # ===== 通用事件注册（类似 Godot 的 connect） =====

    def on_packet(self, callback):
        """
        注册一个回调函数，当收到任何数据包时调用
        :param callback: 接收一个参数（packets_pb2.Packet）
        """
        if callback not in self._packet_callbacks:
            self._packet_callbacks.append(callback)

    def remove_packet_callback(self, callback):
        """取消注册"""
        if callback in self._packet_callbacks:
            self._packet_callbacks.remove(callback)

    # ===== 主线程分发 =====

    def _dispatch_on_main(self, dt):
        """在主线程执行分发"""
        while True:
            try:
                pkt = self.recv_queue.get_nowait()
            except queue.Empty:
                break

            # ✅ 分发给所有已注册的回调（每个回调自己判断类型）
            for cb in self._packet_callbacks:
                try:
                    cb(pkt)
                except Exception as e:
                    print(f"回调执行异常: {e}")

    # ===== 兼容旧接口（如果你还想保留轮询方式） =====

    def get_packet(self, block=False, timeout=0.1):
        try:
            return self.recv_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
# core/ws_client.py
import threading
import queue
import websocket
from core.proto import packets_pb2

class WSClient:
    def __init__(self, uri="ws://localhost:8080/ws"):
        self.uri = uri
        self.ws = None
        self.recv_queue = queue.Queue()
        self.connected = False
        self._thread = None

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
        # 反序列化 Protobuf
        pkt = packets_pb2.Packet()
        pkt.ParseFromString(message)
        print("收到消息:", pkt)          # 直接打印
        self.recv_queue.put(pkt)

    def _on_error(self, ws, error):
        print("WebSocket 错误:", error)

    def _on_close(self, ws, close_code, reason):
        self.connected = False
        print("WebSocket 已关闭")

    def send(self, pkt: packets_pb2.Packet):
        """发送 Protobuf 消息"""
        if self.ws and self.connected:
            self.ws.send(pkt.SerializeToString())
        else:
            print("未连接，无法发送消息")

    def get_packet(self, block=False, timeout=0.1):
        """
        从接收队列中获取一个包（非阻塞或阻塞）
        返回 packets_pb2.Packet 或 None
        """
        try:
            return self.recv_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
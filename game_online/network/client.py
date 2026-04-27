import socket
import json
import select




class GameClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.server_ip = "localhost"
        self.server_port = 8888
        self.connected = False
        self.local_player_id = None
        self.all_players = {}  # {player_id: {"x": int, "y": int, "health": int, ...}}

        # 尝试连接服务端（非阻塞）
        try:
            self.socket.connect((self.server_ip, self.server_port))
        except BlockingIOError:
            pass

            
    
    def close(self):
        """关闭连接"""
        self.socket.close()
        self.connected = False
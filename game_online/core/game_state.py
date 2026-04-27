
class GameState:
    def __init__(self):
        self.local_player = None  # 本地玩家实例
        self.remote_players = {}  # {player_id: Character实例}
        self.network_client = None  # 网络客户端实例

    def init_network(self, network_client):
        """初始化网络客户端"""
        self.network_client = network_client

    def clear(self):
        self.local_player = None
        self.remote_players = {}
        self.network_client = None
    
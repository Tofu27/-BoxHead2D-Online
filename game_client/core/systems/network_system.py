import queue
from core.manager.remote_player_manager import RemotePlayerManager
from core.systems.enemy_system import EnemySystem

class NetworkSystem:
    def __init__(self, message_queue: queue.Queue, remote_manager: RemotePlayerManager, enemy_system: EnemySystem, local_uuid: str):
        self.queue = message_queue
        self.remote_manager = remote_manager
        self.enemy_system = enemy_system
        self.local_uuid = local_uuid

    def update(self):
        while not self.queue.empty():
            try:
                msg = self.queue.get_nowait()
                if msg.type == "game_state":
                    self.remote_manager.apply_full_snapshot(msg.payload["Players"], self.local_uuid)
                    self.enemy_system.apply_full_snapshot(msg.payload["Monsters"])
                elif msg.type == "game_state_diff":
                    self.remote_manager.apply_diff_snapshot(msg.payload["Players"], self.local_uuid)
                    self.enemy_system.apply_diff_snapshot(msg.payload["Monsters"])
                elif msg.type == "player_leave":
                    self.remote_manager.remove(msg.payload)
                elif msg.type == "reset":
                    self.remote_manager.clear_all()
            except queue.Empty:
                break
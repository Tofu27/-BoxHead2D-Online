from core.systems.remote_player_system import RemotePlayerManager
import queue

class NetworkSystem:
    def __init__(self, message_queue: queue.Queue, remote_manager: RemotePlayerManager, local_uuid: str):
        self.queue = message_queue
        self.remote_manager = remote_manager
        self.local_uuid = local_uuid

    def update(self):
        while not self.queue.empty():
            try:
                msg = self.queue.get_nowait()
                if msg.type == "game_state":
                    self.remote_manager.apply_full_snapshot(msg.payload, self.local_uuid)
                elif msg.type == "game_state_diff":
                    self.remote_manager.apply_diff_snapshot(msg.payload, self.local_uuid)
                elif msg.type == "player_leave":
                    self.remote_manager.remove(msg.payload)
                elif msg.type == "reset":
                    self.remote_manager.clear_all()
            except queue.Empty:
                break
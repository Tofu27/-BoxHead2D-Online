
from typing import Dict

import arcade
from entities.character import RemotePlayer

class RemotePlayerManager:
    def __init__(self, physics_engine):
        self.physics_engine = physics_engine
        self.remote_players: Dict[str, RemotePlayer] = {}

    def apply_full_snapshot(self, players_data, local_uuid):
        received = set()
        for data in players_data:
            pid = data["uuid"]
            if pid == local_uuid: continue
            received.add(pid)
            self._add_or_update(pid, data)
        for pid in list(self.remote_players.keys()):
            if pid not in received:
                self.remove(pid)

    def apply_diff_snapshot(self, players_data, local_uuid):
        for data in players_data:
            pid = data["uuid"]
            if pid == local_uuid: continue
            self._add_or_update(pid, data)

    def remove(self, uuid):
        if uuid in self.remote_players:
            p = self.remote_players.pop(uuid)
            self.physics_engine.remove_sprite(p)

    def clear_all(self):
        for pid in list(self.remote_players.keys()):
            self.remove(pid)

    def update(self):
        for p in self.remote_players.values():
            p.update()

    def draw(self):
        for p in self.remote_players.values():
            p.draw()

    def _add_or_update(self, pid, data):
        if pid not in self.remote_players:
            player = RemotePlayer(
                char_type=data.get("character_type", "Player"),
                x=data.get("player_pos", {}).get("x", 0),
                y=data.get("player_pos", {}).get("y", 0),
                physics_engine=self.physics_engine
            )
            self.physics_engine.add_sprite(player, friction=0,
                moment_of_inertia=arcade.pymunk_physics_engine.PymunkPhysicsEngine.MOMENT_INF,
                damping=0,
                collision_type="player",
                elasticity=0.1,
                body_type=arcade.pymunk_physics_engine.PymunkPhysicsEngine.KINEMATIC)
            self.remote_players[pid] = player
        self.remote_players[pid].apply_snapshot(data)
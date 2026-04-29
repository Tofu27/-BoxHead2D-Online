from typing import Dict, List
import arcade
from entities.character import RemotePlayer


class RemotePlayerManager:
    """管理所有远程玩家，处理增删改查、更新、绘制。"""


    def __init__(self, physics_engine, bullet_list: arcade.SpriteList, window, local_uuid):
        self.physics_engine = physics_engine
        self.bullet_list = bullet_list   # 共享的子弹列表，远程玩家攻击时添加子弹
        self.window = window
        self.players: Dict[str, RemotePlayer] = {}   # uuid -> RemotePlayer
        self.local_uuid = local_uuid

    def sync_from_snapshot(self, snapshot: List[dict]):
        """
        根据服务器推送的快照同步玩家列表。
        snapshot 格式: [{"uuid":..., "x":..., "y":..., "char_type":..., ...}, ...]
        """
        received_uuids = set()

        for data in snapshot:
            pid = data["uuid"]
            if pid == self.local_uuid:
                continue

            received_uuids.add(pid)

            if pid not in self.players:
                # 创建新远程玩家
                player = RemotePlayer(
                    char_type=data.get("char_type", "Player"),
                    x=data["x"],
                    y=data["y"],
                    physics_engine=self.physics_engine
                )
                # 将玩家作为运动学刚体加入物理世界
                self.physics_engine.add_sprite(
                    player,
                    friction=0,
                    moment_of_inertia=arcade.pymunk_physics_engine.PymunkPhysicsEngine.MOMENT_INF,
                    damping=0,
                    collision_type="player",
                    elasticity=0.1,
                    body_type=arcade.pymunk_physics_engine.PymunkPhysicsEngine.KINEMATIC
                )
                # 将子弹列表引用传给玩家（以便添加子弹）
                player.bullet_list = self.bullet_list
                player.window = self.window
                self.players[pid] = player
            else:
                # 更新现有玩家
                self.players[pid].apply_snapshot(data)

        # 移除已离开的玩家
        for pid in list(self.players.keys()):
            if pid not in received_uuids:
                self.physics_engine.remove_sprite(self.players[pid])
                del self.players[pid]

    def update(self):
        """更新所有远程玩家。"""
        for player in self.players.values():
            player.update()

    def draw(self):
        """绘制所有远程玩家。"""
        for player in self.players.values():
            player.draw()
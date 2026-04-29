from typing import Dict, List
import arcade
from entities.character import RemotePlayer


class RemotePlayerManager:
    """管理所有远程玩家，处理增删改查、更新、绘制。"""


    def __init__(self, physics_engine, BulletList: arcade.SpriteList, window, LocalUUID):
        self.physics_engine = physics_engine
        self.BulletList = BulletList   # 共享的子弹列表，远程玩家攻击时添加子弹
        self.window = window
        self.RemotePlayers: Dict[str, RemotePlayer] = {}   # uuid -> RemotePlayer
        self.LocalUUID = LocalUUID

    def sync_from_snapshot(self, snapshot: List[dict]):
        """
        根据服务器推送的快照同步玩家列表。
        snapshot 格式: [{"uuid":..., "x":..., "y":..., "char_type":..., ...}, ...]
        """
        ReceivedUUIDs = set()

        for data in snapshot:
            pid = data["uuid"]
            if pid == self.LocalUUID:
                continue

            ReceivedUUIDs.add(pid)

            if pid not in self.RemotePlayers:
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
                player.BulletList = self.BulletList
                player.window = self.window
                self.RemotePlayers[pid] = player
            else:
                # 更新现有玩家
                self.RemotePlayers[pid].apply_snapshot(data)

        # 移除已离开的玩家
        for pid in list(self.RemotePlayers.keys()):
            if pid not in ReceivedUUIDs:
                self.physics_engine.remove_sprite(self.RemotePlayers[pid])
                del self.RemotePlayers[pid]

    def update(self):
        """更新所有远程玩家。"""
        for player in self.RemotePlayers.values():
            player.update()

    def draw(self):
        """绘制所有远程玩家。"""
        for player in self.RemotePlayers.values():
            player.draw()
from typing import Dict, List
import arcade
from entities.character import RemotePlayer, CHARACTER_REGISTRY


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
                    physics_engine=None
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
            self.update_player_attack(
                player=player
            )

             
    def update_player_attack(self, player: RemotePlayer) -> None:
        if player.remote_is_attack:
            if player.cd >= player.cd_max:
                player.cd = 0

            if player.cd == 0:
                if player.current_weapon.is_gun:
                    bullets = player.attack()
                    player.current_weapon.play_sound(self.window.effect_volume)
                    for bullet in bullets:
                        bullet.change_x = bullet.aim.x
                        bullet.change_y = bullet.aim.y
                        if self.BulletList is not None:
                            self.BulletList.append(bullet)

        player.cd = min(player.cd + 1, player.cd_max)

    def draw(self):
        """绘制所有远程玩家。"""
        for player in self.RemotePlayers.values():
            player.draw()
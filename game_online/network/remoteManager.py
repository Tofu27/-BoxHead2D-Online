from typing import Dict, List
import arcade
from entities.character import RemotePlayer, CHARACTER_REGISTRY


class RemotePlayerManager:
    """管理所有远程玩家，处理增删改查、更新、绘制。"""


    def __init__(self, physics_engine, BulletList: arcade.SpriteList, window, LocalUUID):
        self.physics_engine = physics_engine
        self.bullet_list = BulletList   # 共享的子弹列表，远程玩家攻击时添加子弹
        self.window = window
        self.remote_players: Dict[str, RemotePlayer] = {}   # uuid -> RemotePlayer
        self.local_uuid = LocalUUID


    # ---------- 网络数据应用 ----------
    def apply_full_snapshot(self, players_data: List[dict]):
        """服务器发来全量快照：同步整个远程玩家集合。"""
        received_ids = set()
        for data in players_data:
            pid = data["uuid"]
            if pid == self.local_uuid:
                continue
            received_ids.add(pid)
            self._add_or_update_player(pid, data)

        # 移除不在全量快照中的玩家（可能因离开消息丢失而残留）
        for pid in list(self.remote_players.keys()):
            if pid not in received_ids:
                self._remove_player_internal(pid)


    def apply_diff_snapshot(self, players_data: List[dict]):
        """增量更新：只更新变化了的玩家（也可创建新玩家）。"""
        for data in players_data:
            pid = data["uuid"]
            if pid == self.local_uuid:
                continue
            self._add_or_update_player(pid, data)

    def remove_player(self, uuid: str):
        """移除指定玩家（由 player_leave 消息触发）。"""
        if uuid in self.remote_players:
            self._remove_player_internal(uuid)

    def clear_all(self):
        """清除所有远程玩家（断线重连时用）。"""
        for pid in list(self.remote_players.keys()):
            self._remove_player_internal(pid)

    # ---------- 内部辅助 ----------
    def _add_or_update_player(self, pid: str, data: dict):
        """根据数据创建或更新远程玩家。"""
        if pid not in self.remote_players:
            player = RemotePlayer(
                char_type=data.get("character_type", "Player"),
                x=data.get("player_pos", {}).get("x", 0),
                y=data.get("player_pos", {}).get("y", 0),
                physics_engine=None
            )
            self.physics_engine.add_sprite(
                player,
                friction=0,
                moment_of_inertia=arcade.pymunk_physics_engine.PymunkPhysicsEngine.MOMENT_INF,
                damping=0,
                collision_type="player",
                elasticity=0.1,
                body_type=arcade.pymunk_physics_engine.PymunkPhysicsEngine.KINEMATIC
            )
            self.remote_players[pid] = player
        # 更新位置和状态
        self.remote_players[pid].apply_snapshot(data)


    def _remove_player_internal(self, pid: str):
        """实际移除精灵和字典条目（需在主线程调用）。"""
        player = self.remote_players.pop(pid, None)
        if player:
            self.physics_engine.remove_sprite(player)

    # ---------- 游戏循环更新与绘制 ----------
    def update(self):
        """每帧更新远程玩家动画/逻辑（不涉及网络）。"""
        for player in self.remote_players.values():
            player.update()
            self._update_remote_attack(player)  # 攻击 + 子弹生成

    def _update_remote_attack(self, player: RemotePlayer):
        """
        处理远程玩家的攻击逻辑，与原始代码完全一致。
        - 检查 remote_is_attack 标志
        - 冷却时间管理
        - 发射子弹，添加到共享的 bullet_list
        - 播放音效
        """
        if player.remote_is_attack:
            if player.cd == player.cd_max:
                player.cd = 0

            if player.cd == 0:
                if player.current_weapon.is_gun:
                    bullets = player.attack()
                    # 播放音效（使用 window 引用）
                    player.current_weapon.play_sound(self.window.effect_volume)
                    for bullet in bullets:
                        bullet.change_x = bullet.aim.x
                        bullet.change_y = bullet.aim.y
                        self.bullet_list.append(bullet)

        player.cd = min(player.cd + 1, player.cd_max)


    def draw(self):
        for player in self.remote_players.values():
            player.draw()

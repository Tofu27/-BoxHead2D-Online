import arcade
from core.systems.world_system import WorldSystem
from core.systems.enemy_system import EnemySystem
from core.systems.network_system import NetworkSystem
from core.manager.remote_player_manager import RemotePlayerManager


class CollisionSystem:
    def __init__(self, world_sys: WorldSystem, enemy_sys: EnemySystem, remote_sys: RemotePlayerManager, local_player):
        self.world_sys = world_sys          # 提供 wall_list, bullet_list
        self.enemy_sys = enemy_sys  # 提供 enemies 字典
        self.remote_sys = remote_sys
        self.local_player = local_player

    def update(self):
        self._check_bullet_wall()
        self._check_bullet_enemy()
        self._check_enemy_player()

    def _check_bullet_wall(self):
        for bullet in list(self.world_sys.bullet_list):
            if arcade.check_for_collision_with_list(bullet, self.world_sys.wall_list):
                bullet.remove_from_sprite_lists()
                # 可以在此播放弹孔特效

    def _check_bullet_enemy(self):
        
        if len(self.enemy_sys.enemy_sprites) == 0:
            return
        
        for bullet in list(self.world_sys.bullet_list):
            hit_list = arcade.check_for_collision_with_list(bullet, self.enemy_sys.enemy_sprites)
            if hit_list:
                bullet.remove_from_sprite_lists()
                # 可选：播放击中特效，无需知道具体敌人（服务器会广播伤害）

    def _check_enemy_player(self):
        # 只检测本地玩家与敌人的碰撞（用于视觉反馈，如震屏、闪烁）
        if len(self.enemy_sys.enemy_sprites) == 0:
            return
        # if arcade.check_for_collision_with_list(self.local_player, self.enemy_sys.enemy_sprites):
            # 受击闪烁（伤害由服务器决定）
            # self.local_player.get_damage_len = 8
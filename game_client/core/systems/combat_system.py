from core.systems.world_system import WorldSystem
from core.manager.remote_player_manager import RemotePlayerManager

class CombatSystem:
    def __init__(self, world: WorldSystem, remote_manager: RemotePlayerManager, window):
        self.world = world
        self.remote_manager = remote_manager
        self.window = window

    def update_local(self, player):
        # --- 递增冷却模型 ---
        if player.is_attack:
            # 当 cd 达到最大值时重置为 0，并立即攻击
            if player.cd == player.cd_max:
                player.cd = 0
            if player.cd == 0:
                self._fire_weapon(player)
        # 每帧 cd 递增（不超过 cd_max）
        player.cd = min(player.cd + 1, player.cd_max)

    def update_remote(self):
        for rp in self.remote_manager.remote_players.values():
            if rp.remote_is_attack:
                if rp.cd == rp.cd_max:
                    rp.cd = 0
                if rp.cd == 0:
                    self._fire_weapon(rp)
            rp.cd = min(rp.cd + 1, rp.cd_max)

    def _fire_weapon(self, player):
        if not player.current_weapon or not player.current_weapon.is_gun:
            return
        bullets = player.attack()
        player.current_weapon.play_sound(self.window.effect_volume)
        for bullet in bullets:
            bullet.change_x = bullet.aim.x
            bullet.change_y = bullet.aim.y
            self.world.bullet_list.append(bullet)
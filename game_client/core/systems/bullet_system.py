from core.systems.world_system import WorldSystem
import arcade

class BulletSystem:
    def __init__(self, world: WorldSystem):
        self.world = world

    def update(self):
        bullet_list = self.world.bullet_list
        bullet_list.update()
        for bullet in list(bullet_list):
            bullet.life_span -= 1
            if bullet.life_span <= 0:
                bullet.remove_from_sprite_lists()
                continue
            
            # 仅检测与墙壁的碰撞（可扩展）
            if arcade.check_for_collision_with_list(bullet, self.world.wall_list):
                bullet.remove_from_sprite_lists()
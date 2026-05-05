import arcade
from core.systems.world_system import WorldSystem

class BulletSystem:
    def __init__(self, world_sys: WorldSystem):
        self.world_sys = world_sys


    def update(self):
        bullet_list = self.world_sys.bullet_list
        bullet_list.update()
        for bullet in list(bullet_list):
            bullet.life_span -= 1
            if bullet.life_span <= 0:
                bullet.remove_from_sprite_lists()
                continue
          


import arcade
from arcade.pymunk_physics_engine import PymunkPhysicsEngine

class WorldSystem:
    def __init__(self):
        self.physics_engine = None
        self.walls = None
        self.room = None
        self.bullet_list = arcade.SpriteList()


    def setup(self, room_class, width=2100, height=1200, gravity=(0,0), damping=0.01):
        self.room = room_class(width, height)
        self.wall_list = self.room.walls
        self.physics_engine = PymunkPhysicsEngine(gravity, damping)
        self.physics_engine.add_sprite_list(
            self.wall_list, friction=0, collision_type="wall",
            body_type=PymunkPhysicsEngine.STATIC,
        )

    def step(self):
        self.physics_engine.step()
        
    def add_sprite(self, sprite, **kwargs):
        self.physics_engine.add_sprite(sprite, **kwargs)

    def remove_sprite(self, sprite):
        self.physics_engine.remove_sprite(sprite)

    def clear_bullets(self):
        self.bullet_list = arcade.SpriteList()
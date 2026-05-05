from arcade.pymunk_physics_engine import PymunkPhysicsEngine

class PhysicsSystem:
    """封装 Pymunk 物理引擎的常用操作。"""
    def __init__(self, gravity=(0, 0), damping=0.01):
        self.engine = PymunkPhysicsEngine(gravity, damping)

    def add_player(self, player, collision_type="player"):
        self.engine.add_sprite(
            player,
            friction=0,
            moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.001,
            collision_type=collision_type,
            elasticity=0.1,
        )

    def add_walls(self, wall_list):
        self.engine.add_sprite_list(
            wall_list,
            friction=0,
            collision_type="wall",
            body_type=PymunkPhysicsEngine.STATIC,
        )

    def add_sprite(self, sprite, **kwargs):
        self.engine.add_sprite(sprite, **kwargs)

    def remove_sprite(self, sprite):
        self.engine.remove_sprite(sprite)

    def step(self):
        self.engine.step()
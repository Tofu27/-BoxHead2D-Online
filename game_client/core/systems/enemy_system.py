import arcade
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine

class EnemySprite(arcade.Sprite):
    """简单的怪物精灵"""

    TEXTURES = {
        0: "public/graphics/character/EnemyWhite.png",
        1: "public/graphics/character/EnemyRed.png",
    }

    def __init__(self, monster_id, x, y, physics_engine, monster_type=0):
        texture = self.TEXTURES.get(monster_type, self.TEXTURES[0])
        super().__init__(texture, center_x=x, center_y=y, scale=1)
        self.monster_id = monster_id
        self.target_x = x
        self.target_y = y
        self.current_x = x
        self.current_y = y
        self.smoothing = 0.2

        # 添加为运动学刚体，位置完全由代码控制，但能参与碰撞检测
        if physics_engine:
            physics_engine.add_sprite(
                self,
                friction=0,
                moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
                damping=0,
                collision_type="enemy",
                elasticity=0.1,
                body_type=PymunkPhysicsEngine.KINEMATIC
            )

    def apply_snapshot(self, data):
        self.target_x = data["x"]
        self.target_y = data["y"]

    def update(self):
        # 平滑插值
        self.current_x += (self.target_x - self.current_x) * self.smoothing
        self.current_y += (self.target_y - self.current_y) * self.smoothing
        # 更新物理体位置（KINEMATIC 需要用 set_position）
        if self.physics_engines and len(self.physics_engines) > 0:
            self.physics_engines[0].set_position(self, (self.current_x, self.current_y))
        else:
            self.center_x = self.current_x
            self.center_y = self.current_y


class EnemySystem:
    def __init__(self, physics_engine):
        self.physics_engine = physics_engine
        self.enemies = {}  # id -> EnemySprite
        self.enemy_sprites = arcade.SpriteList()  # 用于碰撞检测

    def apply_full_snapshot(self, monsters_data):
        # 全量更新：服务器发来的怪物列表为最新集合
        received_ids = set()
        for data in monsters_data:
            mid = data["id"]
            received_ids.add(mid)
            if mid not in self.enemies:
                sprite = EnemySprite(mid, data["x"], data["y"], self.physics_engine, data.get("type", 0))
                self.enemies[mid] = sprite
                self.enemy_sprites.append(sprite)   # 同步加入列表
            else:
                self.enemies[mid].apply_snapshot(data)

        # 移除不在列表中的怪物
        for mid in list(self.enemies.keys()):
            if mid not in received_ids:
                enemy = self.enemies.pop(mid)
                self.physics_engine.remove_sprite(enemy)
                enemy.remove_from_sprite_lists()    # 从所有 SpriteList 中移除

    def apply_diff_snapshot(self, monsters_data):
        # 差量更新：服务器发来的怪物列表为变化集合
        for data in monsters_data:
            mid = data["id"]
            if mid not in self.enemies:
                self.enemies[mid] = EnemySprite(mid, data["x"], data["y"], self.physics_engine, data.get("type", 0))
            else:
                self.enemies[mid].apply_snapshot(data)
       
    def update(self):
        for enemy in self.enemies.values():
            enemy.update()

    def draw(self):
        for enemy in self.enemies.values():
            enemy.draw()
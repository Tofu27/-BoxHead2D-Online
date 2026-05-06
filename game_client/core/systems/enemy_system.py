import arcade
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from entities.character import Character

class Enemy(Character):
    """简单的怪物精灵"""

    TEXTURES = {
        0: "public/graphics/character/EnemyWhite.png",
        1: "public/graphics/character/EnemyRed.png",
    }

    def __init__(self, monster_id, x, y, monster_type=0, width=20, height=30):
        super().__init__(x, y, physics_engine=None)
        
        self.monster_id = monster_id
        self.monster_type = monster_type
        # 根据服务器下发的宽高重新设置碰撞体尺寸
        self.image_width = width
        self.image_height = height

        texture_path = self.TEXTURES.get(monster_type, self.TEXTURES[0])
        self.body.texture = arcade.load_texture(texture_path)

         # 根据纹理调整身体偏移，让怪物图像底部对齐碰撞体底部
        self.body_pos = Vec2(0, 0)

        # 位置插值同步属性
        self.target_x = x
        self.target_y = y
        self.current_x = x
        self.current_y = y
        self.smoothing = 0.2
        self.is_walking = False

    def apply_snapshot(self, data):
        self.target_x = data["x"]
        self.target_y = data["y"]
        self.is_walking = data.get("is_walking", False)
        if not self.is_walking:
            # 强制立即对齐，消除插值残留
            self.current_x = self.target_x
            self.current_y = self.target_y

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

        # 基类动画：身体浮动 + 行走脚部摆动
        self.update_body_anim()
        self.update_walk_anim()

class EnemySystem:
    def __init__(self, physics_engine):
        self.physics_engine = physics_engine
        self.enemies = {}  # id -> EnemySprite
        self.enemy_sprites = arcade.SpriteList()  # 用于碰撞检测

    def _add_enemy(self, mid, data):
        """创建并注册一个敌人到物理世界"""
        enemy = Enemy(
            mid,
            data["x"], data["y"],
            monster_type=data.get("char_type", data.get("type", 0)),
            width=data.get("width", 20),   # 从服务器获取
            height=data.get("height", 30)
        )
        # 添加为 KINEMATIC 刚体，位置完全由代码驱动但参与碰撞
        self.physics_engine.add_sprite(
            enemy,
            friction=0,
            moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
            damping=0,
            collision_type="enemy",
            elasticity=0.1,
            body_type=PymunkPhysicsEngine.KINEMATIC
        )
        self.enemies[mid] = enemy
        self.enemy_sprites.append(enemy)   # 同步加入碰撞列表

    def apply_full_snapshot(self, monsters_data):
        # 全量更新：服务器发来的怪物列表为最新集合
        received_ids = set()
        for data in monsters_data:
            mid = data["id"]
            received_ids.add(mid)
            if mid not in self.enemies:
                self._add_enemy(mid, data)
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
                self._add_enemy(mid, data)
            else:
                self.enemies[mid].apply_snapshot(data)
       
    def update(self):
        for enemy in self.enemies.values():
            enemy.update()

    def draw(self):
        for enemy in self.enemies.values():
            enemy.draw()
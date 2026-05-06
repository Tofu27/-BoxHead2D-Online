import arcade
from utils.utils import Utils
from core.constants import Color, Style
import random
from entities.weapon import Weapon
from pyglet.math import Vec2

# ==================== 角色动画关键帧数据 ====================
BODY_ANIM = [-1, -1, -1, -1, -1, -1, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0,
             1, 1, 1, 1, 1, 1, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0,]

BODY_WALK = [1, 1, 1, -1, -1, -1, 1, 1, 1, -1, -1, -1]

L_WALK_X = [-1, -1, -1, 0, 0, 0, 1, 1, 1, 0, 0,
            0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 0]
L_WALK_Y = [1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0,
            0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 0]
R_WALK_X = [1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0,
            0, -1, -1, -1, 0, 0, 0, 1, 1, 1, 0, 0, 0]
R_WALK_Y = [1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0,
            0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 0]

GET_DAMAGE_LEN = 8


class Character(arcade.Sprite):
    """所有角色基类：物理碰撞体、渲染部件、基本浮动动画"""
    def __init__(self, x: float = 0, y: float = 0,
                 physics_engine: arcade.PymunkPhysicsEngine = None) -> None:
        
        self.health = 100
        self.is_walking = False
        self.speed = 800
        self.cd = int(0)
        self.cd_max = int(40)

        self.pos = Vec2(x, y)
        self.last_pos = Vec2(0, 0)

        self.body_pos = Vec2(0, 0)
        self.foot_l_pos = Vec2(-8, -16)
        self.foot_r_pos = Vec2(8, -16)
        self.collider_pos = Vec2(0, -3)
        self.shadow_pos = Vec2(-1, -9)

        super().__init__(
            "public/graphics/character/CharacterCollider.png",
            center_x=self.pos.x + self.collider_pos.x,
            center_y=self.pos.y + self.collider_pos.y,
            image_width=20,
            image_height=30,
            scale=1,
        )

        if physics_engine is not None:
            self.register_physics_engine(physics_engine)

        self.shadow = arcade.Sprite(
            center_x=self.collider_pos.x + self.pos.x,
            center_y=self.collider_pos.y + self.pos.x,
            scale=1,
        )
        self.shadow.texture = arcade.make_soft_square_texture(
            22, Color.LIGHT_BLACK, 160, 100)

        self.body_move_up = False
        self.body_move_frames_max = len(BODY_ANIM)
        self.body_move_frames = self.body_move_frames_max
        self.walking_frames_max = len(L_WALK_X)
        self.walking_frames = self.walking_frames_max
        self.velocity = Vec2(0, 0)

        self.body = arcade.Sprite()
        self.foot_l = arcade.Sprite(
            filename="public/graphics/character/Foot.png",
            center_x=self.foot_l_pos.x + self.pos.x,
            center_y=self.foot_l_pos.y + self.pos.y,
            image_width=4,
            image_height=4,
            scale=1,
        )
        self.foot_r = arcade.Sprite(
            filename="public/graphics/character/Foot.png",
            center_x=self.foot_r_pos.x + self.pos.x,
            center_y=self.foot_r_pos.y + self.pos.y,
            image_width=4,
            image_height=4,
            scale=1,
        )
        self.damage_sprite = arcade.SpriteSolidColor(20, 24, Color.RED_TRANSPARENT)
        self.damage_sprite.alpha = 0

        self.parts = arcade.SpriteList()
        self.parts.append(self.shadow)
        self.parts.append(self.body)
        self.parts.append(self.foot_l)
        self.parts.append(self.foot_r)
        self.parts.append(self.damage_sprite)

    def draw(self, *, filter=None, pixelated=None, blend_function=None) -> None:
        self.parts.draw()

    def move(self) -> None:
        self.pos.x = self.center_x - self.collider_pos.x
        self.pos.y = self.center_y - self.collider_pos.y

        self.body.center_x = self.pos.x + self.body_pos.x
        self.body.center_y = self.pos.y + self.body_pos.y

        self.foot_l.center_x = self.pos.x + self.foot_l_pos.x
        self.foot_l.center_y = self.pos.y + self.foot_l_pos.y
        self.foot_r.center_x = self.pos.x + self.foot_r_pos.x
        self.foot_r.center_y = self.pos.y + self.foot_r_pos.y

        self.shadow.center_x = self.pos.x + self.shadow_pos.x
        self.shadow.center_y = self.pos.y + self.shadow_pos.y

        self.damage_sprite.center_x = self.center_x
        self.damage_sprite.center_y = self.center_y

    def update_body_anim(self) -> None:
        self.move()
        
        """仅更新身体浮动动画（子类可能自行调度）"""
        if self.body_move_frames == 0:
            self.body_move_frames = self.body_move_frames_max
            self.body_move_up = not self.body_move_up
        self.body_move_frames -= 1
        self.body.center_y += BODY_ANIM[self.body_move_frames]

    
    def register_dir_field(self, dir_field: dict) -> None:
        self.dir_field = dir_field


    def update_walk_anim(self):
        """根据 is_walking 更新脚部动画"""
        if self.walking_frames == 0:
            self.walking_frames = self.walking_frames_max
        self.walking_frames -= 1

        if self.is_walking:
            self.foot_l.center_x += L_WALK_X[self.walking_frames]
            self.foot_l.center_y += L_WALK_Y[self.walking_frames]
            self.foot_r.center_x += R_WALK_X[self.walking_frames]
            self.foot_r.center_y += R_WALK_Y[self.walking_frames]
        else:
            self.foot_l.center_x = self.foot_l_pos.x + self.pos.x
            self.foot_l.center_y = self.foot_l_pos.y + self.pos.y
            self.foot_r.center_x = self.foot_r_pos.x + self.pos.x
            self.foot_r.center_y = self.foot_r_pos.y + self.pos.y
            self.walking_frames = self.walking_frames_max


# ==================== 行为组件 ====================
class BaseBehavior:
    def on_damage(self, owner: 'Player', damage: int):
        pass

    def use_skill(self, owner: 'Player'):
        pass


class RamboBehavior(BaseBehavior):
    def on_damage(self, owner: 'Player', damage: int):
        owner.get_energy(damage)


class RedbitBehavior(BaseBehavior):
    def use_skill(self, owner: 'Player'):
        if owner.energy < 30:
            return
        elif 30 <= owner.energy < 500:
            owner.energy -= 30
        else:
            owner.energy -= owner.energy / 10

        dash_dir = owner.mouse_pos - owner.pos
        dash_dir = dash_dir.normalize().scale(owner.speed * 50)
        owner.physics_engines[0].apply_force(owner, (dash_dir.x, dash_dir.y))


# ==================== 角色注册表 ====================
CHARACTER_REGISTRY = {
    "Player": {
        "texture": "public/graphics/character/Player.png",
        "behavior": BaseBehavior(),
        "name": "Nameless",
        "description": "Nameless Description"
    },
    "Rambo": {
        "texture": "public/graphics/character/Rambo.png",
        "behavior": RamboBehavior(),
        "name": "Rambo",
        "description": "Rambo Description"
    },
    "Redbit": {
        "texture": "public/graphics/character/Redbit.png",
        "behavior": RedbitBehavior(),
        "name": "Redbit",
        "description": "Redbit Description"
    }
}


class Player(Character):
    """通用玩家：渲染、动画、武器、行为组件"""
    def __init__(self, char_type: str, x: float = 0, y: float = 0,
                 physics_engine: arcade.PymunkPhysicsEngine = None):
        super().__init__(x, y, physics_engine)
        config = CHARACTER_REGISTRY.get(char_type, CHARACTER_REGISTRY["Player"])
        self.char_type = char_type
        self.behavior = config["behavior"]
        self.body.texture = arcade.load_texture(config["texture"])
        self.name = config["name"]
        self.description = config["description"]

        # 通用状态
        self.uuid = None
        self.username = None
        self.speed = 1600
        self.energy = 0
        self.is_attack = False

        # 武器系统
        self.weapon_pos = Vec2(16, -2)
        self.weapons = []
        self.weapon_index = 0
        pistol = Weapon(x=self.pos.x + self.weapon_pos.x,
                        y=self.pos.y + self.weapon_pos.y)
        self.add_weapon(pistol)
        self.current_weapon = self.weapons[self.weapon_index]
        self.cd_max = self.current_weapon.cd_max

    def update(self):
        """模板方法：先动画，再子类控制，最后通用更新"""
        super().update_body_anim()
        self._update_control()        # 子类实现
        self._update_weapon()
        self.update_walk_anim()

    def _update_control(self):
        """子类覆盖：处理移动、攻击触发"""
        raise NotImplementedError

    def _update_weapon(self):
        """武器跟随与朝向更新"""
        if self.current_weapon.is_right:
            self.weapon_pos = Vec2(16, -2)
        else:
            self.weapon_pos = Vec2(9, -2)
        self.current_weapon.pos = self.pos + self.weapon_pos
        self.current_weapon.update()

    

    def draw(self) -> None:
        if self.current_weapon.is_right:
            self.current_weapon.draw()
            super().draw()
        else:
            super().draw()
            self.current_weapon.draw()
          

    def move(self) -> None:
        """视觉部件跟随物理体位置"""
        super().move()
        self.current_weapon.pos = self.pos + self.weapon_pos

    def aim(self):
        """根据鼠标位置更新武器朝向"""
        raise NotImplementedError  # 由子类决定鼠标来源

    def attack(self) -> arcade.SpriteList:
        """返回当前武器生成的一发子弹列表"""
        return self.current_weapon.get_bullet()

    def get_damage(self, damage: int):
        self.health = max(self.health - damage, 0)
        self.behavior.on_damage(self, damage)

    def get_energy(self, energy: int):
        self.energy += energy

    def use_skill(self):
        self.behavior.use_skill(self)

    def add_weapon(self, weapon):
        self.weapons.append(weapon)


class LocalPlayer(Player):
    """本地玩家：键盘移动、鼠标输入"""
    def __init__(self, char_type: str, x: float, y: float, physics_engine=None):
        super().__init__(char_type, x, y, physics_engine)
        self.move_left = False
        self.move_right = False
        self.move_up = False
        self.move_down = False
        self.mouse_pos = Vec2(0, 0)

    def draw(self):
        super().draw()

        if self.username:
            self.draw_name()

    def draw_name(self):
        arcade.draw_text(
            self.username,
            self.body.center_x + 2,
            self.body.center_y + 14,
            arcade.color.ORANGE,
            font_size=10,
            anchor_x="center",
            anchor_y="bottom",
            bold=True
        )

    def _update_control(self):
        # 键盘移动
        force = Vec2(0, 0)
        if self.move_up and not self.move_down:
            force.y = 1
        elif self.move_down and not self.move_up:
            force.y = -1
        if self.move_left and not self.move_right:
            force.x = -1
        elif self.move_right and not self.move_left:
            force.x = 1

        force = force.normalize().scale(self.speed) if force.mag else force
        if self.physics_engines and len(self.physics_engines) > 0:
            self.physics_engines[0].apply_force(self, (force.x, force.y))
        self.is_walking = force.mag != 0

        # 瞄准
        self.aim()


    def aim(self):
        """使用本地鼠标位置"""
        if self.mouse_pos is None:
            return
        aim_pos = self.mouse_pos - self.pos
        self.current_weapon.aim(aim_pos)

    def register_mouse_pos(self, mouse_pos: Vec2):
        self.mouse_pos = mouse_pos


class RemotePlayer(Player):
    """远程玩家：位置插值、快照应用、攻击模拟"""
    def __init__(self, char_type: str, x: float, y: float, physics_engine=None):
        super().__init__(char_type, x, y, physics_engine)
        self.target_x = x
        self.target_y = y
        self.current_x = x
        self.current_y = y
        self.smoothing = 0.2
        self.remote_mouse_pos = Vec2(0, 0)
        self.remote_is_walking = False
        self.remote_is_attack = False

    def draw(self):
        super().draw()

        if self.username:
            self.draw_name()

    def draw_name(self):
        arcade.draw_text(
            self.username,
            self.body.center_x + 2,
            self.body.center_y + 14,
            arcade.color.GREEN,
            font_size=10,
            anchor_x="center",
            anchor_y="bottom",
            bold=True
        )

    def _update_control(self):
        # 位置插值
        self.current_x += (self.target_x - self.current_x) * self.smoothing
        self.current_y += (self.target_y - self.current_y) * self.smoothing
        if self.physics_engines and len(self.physics_engines) > 0:
            self.physics_engines[0].set_position(self, (self.current_x, self.current_y))
        else:
            self.center_x = self.current_x
            self.center_y = self.current_y

        self.is_walking = self.remote_is_walking

        # 瞄准（使用远程鼠标）
        self.aim()


    def aim(self):
        """使用远程鼠标位置"""
        if self.remote_mouse_pos is None:
            return
        aim_pos = self.remote_mouse_pos - self.pos
        self.current_weapon.aim(aim_pos)

    def apply_snapshot(self, data: dict):
        self.target_x = data.get("player_pos", {}).get("x", 0)
        self.target_y = data.get("player_pos", {}).get("y", 0)
        self.username = data["name"]
        self.remote_is_walking = data.get("is_walking", False)
        self.remote_is_attack = data.get("is_attack", False)
        self.remote_mouse_pos = Vec2(data.get("mouse_pos", {}).get("x", 0),
                                     data.get("mouse_pos", {}).get("y", 0))




# ==================== 便捷工厂 ====================
def CreatePlayer(char_type: str, x: float, y: float, physics_engine=None, is_remote=False) -> Player:
    if is_remote:
        return RemotePlayer(char_type, x, y, physics_engine)
    else:
        return LocalPlayer(char_type, x, y, physics_engine)
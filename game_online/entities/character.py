import arcade
from utils.utils import Utils, Color, Style
import random
from entities.weapon import Weapon
from pyglet.math import Vec2

# ==================== 角色动画关键帧数据 ====================
# 身体上下浮动动画序列（索引控制偏移量）
BODY_ANIM = [-1, -1, -1, -1, -1, -1, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0,
             1, 1, 1, 1, 1, 1, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0,]

BODY_WALK = [1, 1, 1, -1, -1, -1, 1, 1, 1, -1, -1, -1]

# 左脚走路时X/Y偏移序列
L_WALK_X = [-1, -1, -1, 0, 0, 0, 1, 1, 1, 0, 0,
            0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 0]
L_WALK_Y = [1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0,
            0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 0]
# 右脚走路时X/Y偏移序列
R_WALK_X = [1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0,
            0, -1, -1, -1, 0, 0, 0, 1, 1, 1, 0, 0, 0]
R_WALK_Y = [1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0,
            0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0, 0, 0]

GET_DAMAGE_LEN = 8   # 受伤闪烁持续时间（帧数）

class Character(arcade.Sprite):
    """所有角色（玩家、敌人等）的基类，包含身体部件、物理引擎交互和基本动画。"""

    def __init__(self, x: float = 0, y: float = 0,
                 physics_engine: arcade.PymunkPhysicsEngine = None) -> None:
        
        self.is_walking = False         # 是否在行走
        self.speed = 800
        self.cd = int(0)
        self.cd_max = int(40)  # 2/3 s
        
        self.pos = Vec2(x, y)           # 角色逻辑位置（参考点）
        self.last_pos = Vec2(0, 0)

        self.body_pos = Vec2(0, 0)      # 身体偏移
        self.foot_l_pos = Vec2(-8, -16) # 左脚偏移
        self.foot_r_pos = Vec2(8, -16)  # 右脚偏移
        self.collider_pos = Vec2(0, -3) # 碰撞箱偏移（用于物理引擎）
        self.shadow_pos = Vec2(-1, -9)  # 阴影偏移

        # 初始化碰撞精灵（用于物理引擎）
        super().__init__(
            "public/graphics/character/CharacterCollider.png",
            center_x=self.pos.x + self.collider_pos.x,
            center_y=self.pos.y + self.collider_pos.y,
            image_width=20,
            image_height=30,
            scale=1,
        )

        if physics_engine is not None:
            self.register_physics_engine(physics_engine)    # 注册到物理引擎

        # 阴影精灵（半透明圆形）
        self.shadow = arcade.Sprite(
            center_x=self.collider_pos.x + self.pos.x,
            center_y=self.collider_pos.y + self.pos.x,
            scale=1,
        )
        self.shadow.texture = arcade.make_soft_square_texture(
            22, Color.LIGHT_BLACK, 160, 100)
        

        # 动画帧计数器
        self.body_move_up = False
        self.body_move_frames_max = len(BODY_ANIM)
        self.body_move_frames = self.body_move_frames_max
        self.walking_frames_max = len(L_WALK_X)
        self.walking_frames = self.walking_frames_max
        self.velocity = Vec2(0, 0)
        
        # 身体和脚的精灵
        self.body = arcade.Sprite()
       
        self.foot_l = arcade.Sprite(
            filename="public/graphics/character/Foot.png",
            center_x=self.foot_l_pos.x + self.pos.x,
            center_y=self.foot_l_pos.y + self.pos.x,
            image_width=4,
            image_height=4,
            scale=1,
        )
        self.foot_r = arcade.Sprite(
            filename="public/graphics/character/Foot.png",
            center_x=self.foot_r_pos.x + self.pos.x,
            center_y=self.foot_r_pos.y + self.pos.x,
            image_width=4,
            image_height=4,
            scale=1,
        )

        # 受伤闪红效果精灵（初始透明）
        self.damage_sprite = arcade.SpriteSolidColor(20, 24,
                                Color.RED_TRANSPARENT)
        self.damage_sprite.alpha = 0

        # 将所有可视部件放入一个列表，方便批量绘制
        self.parts = arcade.SpriteList()
        self.parts.append(self.shadow)
        self.parts.append(self.body)
        self.parts.append(self.foot_l)
        self.parts.append(self.foot_r)
        self.parts.append(self.damage_sprite)
        

    def draw(self, *, filter=None, pixelated=None, blend_function=None) -> None:
        """绘制角色的所有部件。"""
        self.parts.draw()


    def move(self) -> None:
        """根据物理引擎的碰撞箱位置更新所有部件的位置。"""
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
        
    def update(self) -> None:
        """每帧更新：更新部件位置。"""
        self.move()

        # 身体浮动动画（按帧改变身体Y轴偏移）
        if self.body_move_frames == 0:  # 重置动画周期
            self.body_move_frames = self.body_move_frames_max
            self.body_move_up = not self.body_move_up

        self.body_move_frames -= 1
        self.body.center_y += BODY_ANIM[self.body_move_frames]


class Player(Character):
    """玩家角色类，支持WASD移动控制和行走动画。"""

    body_texture = arcade.load_texture("public/graphics/character/Player.png")  # 身体贴图
    name = "Nameless"
    description = "Nameless Description"

    def __init__(self, x: float = 0, y: float = 0,
                physics_engine: arcade.PymunkPhysicsEngine = None,
            ) -> None:
        super().__init__(x, y, physics_engine)

        self.uuid = None
        self.username = None
        self.is_remote = False  # 是否是网络角色（默认本地角色）
        self.remote_mouse_pos = None # 远程角色的鼠标坐标
        
        self.char_type = "Player" # 类型
        self.speed = 1600       # 移动速度（力的大小）
        self.is_attack = False  # 是否在攻击
        
        self.energy = int(0)

        # 移动标志位（由键盘控制）
        self.move_left = False
        self.move_right = False
        self.move_up = False
        self.move_down = False

        # 玩家皮肤挂载
        self.body.texture = self.body_texture   # 应用玩家身体贴图


        # 创建武器
        self.weapon_pos = Vec2(16, -2)
        self.weapons = []
        self.weapon_index = 0
        pistol = Weapon(x=self.pos.x + self.weapon_pos.x,
                               y=self.pos.y + self.weapon_pos.y)
        self.add_weapon(pistol)
        self.current_weapon = self.weapons[self.weapon_index]
        self.cd_max = self.current_weapon.cd_max


    def draw(self) -> None:
        """绘制玩家，并额外处理身体上下浮动动画。"""
        if self.current_weapon.is_right:
            self.current_weapon.draw()
            super().draw()
        else:
            super().draw()
            self.current_weapon.draw()

        if self.username:
            self.draw_name()

    def update(self) -> None:
        """更新玩家状态：先移动部件，再更新走路动画。"""
        super().update()

        self.aim()

        if self.walking_frames == 0:  
            self.walking_frames = self.walking_frames_max

        self.walking_frames -= 1

        if self.is_walking:
            # 交替移动左脚和右脚的位置，模拟走路
            self.foot_l.center_x += L_WALK_X[self.walking_frames]
            self.foot_l.center_y += L_WALK_Y[self.walking_frames]
            self.foot_r.center_x += R_WALK_X[self.walking_frames]
            self.foot_r.center_y += R_WALK_Y[self.walking_frames]
        else:
            # 静止时，脚部复位到原始偏移
            self.foot_l.center_x = self.foot_l_pos.x + self.pos.x
            self.foot_l.center_y = self.foot_l_pos.y + self.pos.y
            self.foot_r.center_x = self.foot_r_pos.x + self.pos.x
            self.foot_r.center_y = self.foot_r_pos.y + self.pos.y
            self.walking_frames = self.walking_frames_max

        # 判断武器是左手还是右手
        if self.current_weapon.is_right:
            self.weapon_pos = Vec2(16, -2)
        else:
            self.weapon_pos = Vec2(9, -2)

        # 更新武器状态
        self.current_weapon.update()

    def draw_name(self):
        # 绘制在角色头顶上方 20 像素处
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

    def move(self) -> None:
        """根据键盘输入向物理引擎施加力，从而移动玩家。"""

        # 本地玩家就需要做引擎处理
        if self.is_remote == False:
            force = Vec2(0, 0)
            if self.move_up and not self.move_down:
                force.y = 1
            elif self.move_down and not self.move_up:
                force.y = -1
            if self.move_left and not self.move_right:
                force.x = -1
            elif self.move_right and not self.move_left:
                force.x = 1

            # 归一化后乘以速度，得到最终作用力
            force = force.normalize().scale(self.speed)
            self.physics_engines[0].apply_force(self, (force.x, force.y))
            
            # 根据是否有力作用设置行走标志
            if force.mag != 0:
                self.is_walking = True
            else:
                self.is_walking = False

        # 调用父类的move方法更新各部件位置
        super().move()
        # 武器坐标变化
        self.current_weapon.pos = self.pos + self.weapon_pos
    
    def register_mouse_pos(self, mouse_pos: Vec2) -> None:
        self.mouse_pos = mouse_pos
    
    def add_weapon(self, weapon: arcade.Sprite) -> None:
        self.weapons.append(weapon)

        
    def aim(self) -> None:

        mouse_pos = self.remote_mouse_pos if self.is_remote else self.mouse_pos
        if mouse_pos is None:
            return 

        aim_pos = mouse_pos - self.pos
        self.current_weapon.aim(aim_pos)

        
    def attack(self) -> arcade.SpriteList:
        return self.current_weapon.get_bullet()
    
    
    def get_damage(self, damage: int) -> None:
        self.health = max(self.health - damage, 0)
    
    def get_energy(self, energy: int) -> None:
        self.energy += energy

    def setGameInfo(self, info: any) -> None:
        self.username = info['username']
        self.uuid = info['uuid']
    
    
class Rambo(Player):
    "Rambo character."

    body_texture = arcade.load_texture("public/graphics/character/Rambo.png")
    name = "Rambo"
    description = "Rambo Description"

    def __init__(self, x = 0, y = 0, physics_engine = None):
        super().__init__(x, y, physics_engine)
        self.char_type = "Rambo"


    def get_damage(self, damage: int) -> None:
        super().get_damage(damage)
        self.get_energy(damage)


class Redbit(Player):
    "Redbit character."
    
    body_texture = arcade.load_texture("public/graphics/character/Redbit.png")
    name = "Redbit"
    description = "Redbit Description"

    def __init__(self, x = 0, y = 0, physics_engine = None):
        super().__init__(x, y, physics_engine)
        self.char_type = "Redbit"

    def use_skill(self) -> None:
        # Dashing
        dash_dir = self.mouse_pos - self.pos
        dash_dir = dash_dir.normalize().scale(self.speed * 50)
        if self.energy < 30:
            return
        elif self.energy >= 30 and self.energy < 500:
            self.energy -= 30
        else:
            self.energy -= self.energy / 10
        self.physics_engines[0].apply_force(self, (dash_dir.x, dash_dir.y))
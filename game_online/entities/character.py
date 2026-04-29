import arcade
from utils.utils import Utils, Color, Style
import random
from entities.weapon import Weapon
from pyglet.math import Vec2

# ==================== 角色动画关键帧数据 ====================
# 身体上下浮动动画序列（索引控制偏移量）
# 数值代表身体Y轴偏移像素：-1向下，0无偏移，1向上
BODY_ANIM = [-1, -1, -1, -1, -1, -1, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0,
             1, 1, 1, 1, 1, 1, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0,]

# 行走时身体的摆动幅度（暂未使用，预留）
BODY_WALK = [1, 1, 1, -1, -1, -1, 1, 1, 1, -1, -1, -1]

# 左脚走路时X/Y偏移序列（用于交替移动脚的位置模拟步行）
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
    """所有角色（玩家、敌人等）的基类，包含身体部件、物理引擎交互和基本动画。
    
    该类继承自 arcade.Sprite，用于与 PymunkPhysicsEngine 交互。
    角色由多个视觉部件（身体、脚、阴影、受伤特效）组成，并处理基础的浮动动画。
    """

    def __init__(self, x: float = 0, y: float = 0,
                 physics_engine: arcade.PymunkPhysicsEngine = None) -> None:
        """
        初始化角色。

        :param x: 初始 X 坐标
        :param y: 初始 Y 坐标
        :param physics_engine: 可选，Pymunk 物理引擎实例，若提供则自动注册
        """
        self.health = 100               # 生命值
        self.is_walking = False         # 是否在行走（影响脚部动画）
        self.speed = 800                # 移动速度（作用力大小，单位：牛顿）
        self.cd = int(0)                # 当前冷却帧数（用于攻击等）
        self.cd_max = int(40)           # 冷却最大值（40帧 ≈ 0.67秒，60帧下）
        
        self.pos = Vec2(x, y)           # 角色逻辑位置（参考点，通常是碰撞箱的中心偏移前的原点）
        self.last_pos = Vec2(0, 0)      # 上一帧位置（暂未使用）

        # 各部件相对于角色逻辑位置的偏移量
        self.body_pos = Vec2(0, 0)      # 身体偏移
        self.foot_l_pos = Vec2(-8, -16) # 左脚偏移
        self.foot_r_pos = Vec2(8, -16)  # 右脚偏移
        self.collider_pos = Vec2(0, -3) # 碰撞箱偏移（物理引擎使用的精灵中心相对位置）
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

        # 阴影精灵（半透明圆形贴图）
        self.shadow = arcade.Sprite(
            center_x=self.collider_pos.x + self.pos.x,
            center_y=self.collider_pos.y + self.pos.x,
            scale=1,
        )
        self.shadow.texture = arcade.make_soft_square_texture(
            22, Color.LIGHT_BLACK, 160, 100)
        

        # 动画帧计数器
        self.body_move_up = False               # 身体是否向上移动（影响动画方向）
        self.body_move_frames_max = len(BODY_ANIM)  # 身体浮动动画总帧数
        self.body_move_frames = self.body_move_frames_max  # 当前帧倒计时
        self.walking_frames_max = len(L_WALK_X)  # 行走动画总帧数
        self.walking_frames = self.walking_frames_max    # 当前行走帧倒计时
        self.velocity = Vec2(0, 0)              # 速度向量（暂未使用）
        
        # 身体和脚的精灵
        self.body = arcade.Sprite()             # 身体精灵（贴图由子类设置）
       
        self.foot_l = arcade.Sprite(           # 左脚精灵
            filename="public/graphics/character/Foot.png",
            center_x=self.foot_l_pos.x + self.pos.x,
            center_y=self.foot_l_pos.y + self.pos.y,
            image_width=4,
            image_height=4,
            scale=1,
        )
        self.foot_r = arcade.Sprite(           # 右脚精灵
            filename="public/graphics/character/Foot.png",
            center_x=self.foot_r_pos.x + self.pos.x,
            center_y=self.foot_r_pos.y + self.pos.y,
            image_width=4,
            image_height=4,
            scale=1,
        )

        # 受伤闪红效果精灵（初始透明）
        self.damage_sprite = arcade.SpriteSolidColor(20, 24, Color.RED_TRANSPARENT)
        self.damage_sprite.alpha = 0

        # 将所有可视部件放入一个列表，方便批量绘制和统一管理
        self.parts = arcade.SpriteList()
        self.parts.append(self.shadow)
        self.parts.append(self.body)
        self.parts.append(self.foot_l)
        self.parts.append(self.foot_r)
        self.parts.append(self.damage_sprite)
        

    def draw(self, *, filter=None, pixelated=None, blend_function=None) -> None:
        """绘制角色的所有部件（调用 parts 的 draw 方法）。"""
        self.parts.draw()


    def move(self) -> None:
        """根据物理引擎的碰撞箱位置更新所有部件的位置。
        
        该方法在每帧被调用，确保视觉部件跟随物理碰撞箱移动。
        """
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
        """每帧更新：更新部件位置，并处理身体上下浮动动画。"""
        self.move()

        # 身体浮动动画循环（按帧改变身体Y轴偏移）
        if self.body_move_frames == 0:  # 重置动画周期
            self.body_move_frames = self.body_move_frames_max
            self.body_move_up = not self.body_move_up

        self.body_move_frames -= 1
        self.body.center_y += BODY_ANIM[self.body_move_frames]  # 应用偏移


class Player(Character):
    """玩家角色类，支持WASD移动控制和行走动画，持有武器系统。"""

    body_texture = arcade.load_texture("public/graphics/character/Player.png")  # 默认玩家身体贴图
    name = "Nameless"
    description = "Nameless Description"

    def __init__(self, x: float = 0, y: float = 0,
                physics_engine: arcade.PymunkPhysicsEngine = None,
            ) -> None:
        """
        初始化玩家。

        :param x: 初始 X 坐标
        :param y: 初始 Y 坐标
        :param physics_engine: 物理引擎实例
        """
        super().__init__(x, y, physics_engine)

        self.uuid = None            # 网络唯一标识符（用于多人）
        self.username = None        # 玩家显示名称
        self.is_remote = False      # 是否是网络角色（True表示远程玩家，False表示本地玩家）
        self.remote_mouse_pos = None # 远程玩家的鼠标坐标（由网络同步）
        
        self.char_type = "Player"   # 角色类型标识
        self.speed = 1600           # 移动速度（作用力大小，比基类更大）
        self.is_attack = False      # 是否正在攻击（暂未使用）
        
        self.energy = int(0)        # 能量值（用于技能）

        # 移动标志位（由键盘控制，在外部更新）
        self.move_left = False
        self.move_right = False
        self.move_up = False
        self.move_down = False

        # 玩家皮肤挂载
        self.body.texture = self.body_texture   # 应用玩家身体贴图


        # 创建武器系统
        self.weapon_pos = Vec2(16, -2)          # 武器相对于角色逻辑位置的偏移
        self.weapons = []                       # 武器列表
        self.weapon_index = 0                   # 当前使用的武器索引
        pistol = Weapon(x=self.pos.x + self.weapon_pos.x,
                        y=self.pos.y + self.weapon_pos.y)
        self.add_weapon(pistol)
        self.current_weapon = self.weapons[self.weapon_index]  # 当前武器
        self.cd_max = self.current_weapon.cd_max               # 同步冷却时间


    def draw(self) -> None:
        """绘制玩家，并根据武器朝向调整绘制顺序（右手前，左手后）。"""
        if self.current_weapon.is_right:
            self.current_weapon.draw()   # 先画武器（右手时武器在上层）
            super().draw()
        else:
            super().draw()               # 左手时先画角色，武器在上层但实际顺序靠后
            self.current_weapon.draw()

        if self.username:
            self.draw_name()             # 绘制玩家名称

    def update(self) -> None:
        """更新玩家状态：移动部件、走路动画、武器瞄准与更新。"""
        super().update()                 # 更新基本部件位置和浮动动画

        self.aim()                       # 根据鼠标位置调整武器朝向

        # 行走动画控制
        if self.walking_frames == 0:  
            self.walking_frames = self.walking_frames_max

        self.walking_frames -= 1

        if self.is_walking:
            # 交替移动左脚和右脚的位置，模拟走路（根据动画帧表偏移）
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

        # 根据武器朝向调整武器挂载点偏移（右手在右前方，左手在左前方）
        if self.current_weapon.is_right:
            self.weapon_pos = Vec2(16, -2)
        else:
            self.weapon_pos = Vec2(9, -2)

        # 更新武器状态（位置跟随、冷却等）
        self.current_weapon.update()

    def draw_name(self):
        """在角色头顶绘制玩家名称（用于多人模式）。"""
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
        """根据键盘输入向物理引擎施加力，从而移动玩家（仅本地玩家有效）。"""
        # 本地玩家才向物理引擎施加力（远程玩家由网络同步位置）
        if not self.is_remote:
            force = Vec2(0, 0)
            if self.move_up and not self.move_down:
                force.y = 1
            elif self.move_down and not self.move_up:
                force.y = -1
            if self.move_left and not self.move_right:
                force.x = -1
            elif self.move_right and not self.move_left:
                force.x = 1

            # 归一化后乘以速度因子，得到最终作用力（向量）
            force = force.normalize().scale(self.speed)
            self.physics_engines[0].apply_force(self, (force.x, force.y))
            
            # 根据是否有力作用设置行走标志（用于动画）
            if force.mag != 0:
                self.is_walking = True
            else:
                self.is_walking = False

        # 调用父类方法更新所有视觉部件的位置
        super().move()
        # 更新武器的位置，使其跟随角色
        self.current_weapon.pos = self.pos + self.weapon_pos
    
    def register_mouse_pos(self, mouse_pos: Vec2) -> None:
        """注册本地鼠标位置（用于瞄准）。"""
        self.mouse_pos = mouse_pos
    
    def add_weapon(self, weapon: arcade.Sprite) -> None:
        """添加一把武器到武器列表。"""
        self.weapons.append(weapon)

        
    def aim(self) -> None:
        """根据鼠标位置（本地或远程）计算瞄准方向，并设置武器的角度。"""
        mouse_pos = self.remote_mouse_pos if self.is_remote else self.mouse_pos
        if mouse_pos is None:
            return 

        aim_pos = mouse_pos - self.pos          # 瞄准向量（从角色指向鼠标）
        self.current_weapon.aim(aim_pos)        # 让武器指向该方向

        
    def attack(self) -> arcade.SpriteList:
        """执行攻击：返回当前武器生成的一发子弹的 SpriteList。"""
        return self.current_weapon.get_bullet()
    
    def get_damage(self, damage: int) -> None:
        """受到伤害，减少生命值（不低于0）。"""
        self.health = max(self.health - damage, 0)
    
    def get_energy(self, energy: int) -> None:
        """增加能量值。"""
        self.energy += energy

    def use_skill(self) -> None:
        """使用技能（基类为空，由子类重写）。"""
        pass
    
class Rambo(Player):
    """Rambo 角色：受伤时获得等额能量。"""

    body_texture = arcade.load_texture("public/graphics/character/Rambo.png")
    name = "Rambo"
    description = "Rambo Description"

    def __init__(self, x = 0, y = 0, physics_engine = None):
        super().__init__(x, y, physics_engine)
        self.char_type = "Rambo"


    def get_damage(self, damage: int) -> None:
        """受伤时减少生命值，同时获得等值能量。"""
        super().get_damage(damage)
        self.get_energy(damage)          # 受伤加速能量获取

class Redbit(Player):
    """Redbit 角色：消耗能量进行冲刺（技能）。"""
    
    body_texture = arcade.load_texture("public/graphics/character/Redbit.png")
    name = "Redbit"
    description = "Redbit Description"

    def __init__(self, x = 0, y = 0, physics_engine = None):
        super().__init__(x, y, physics_engine)
        self.char_type = "Redbit"

    def use_skill(self) -> None:
        """消耗能量进行一次强力冲刺，向鼠标方向施加巨大瞬时力。"""
        # 计算冲刺方向（从角色指向鼠标）
        dash_dir = self.mouse_pos - self.pos
        dash_dir = dash_dir.normalize().scale(self.speed * 50)   # 获得一个极大的力
        if self.energy < 30:
            return          # 能量不足，无法释放
        elif self.energy >= 30 and self.energy < 500:
            self.energy -= 30
        else:
            self.energy -= self.energy / 10   # 能量充足时按比例消耗
        # 向物理引擎施加冲刺力（瞬间冲量）
        self.physics_engines[0].apply_force(self, (dash_dir.x, dash_dir.y))


class RemotePlayer(Player):
    """网络同步的远程玩家角色，支持位置插值和攻击模拟。"""

    def __init__(self, char_type: str, x: float, y: float, physics_engine=None):
        # 根据 char_type 选择合适的基类
        class_map = {"Player": Player, "Rambo": Rambo, "Redbit": Redbit}
        cls = class_map.get(char_type, Player)
         # 调用父类构造，但不传入 physics_engine（后面会手动以运动学方式添加）
        super().__init__(x, y, physics_engine=None)

        self.physics_engine = physics_engine
        self.char_type = char_type
        self.is_remote = True
        self.bullet_list = None

        # 插值状态
        self.target_x = x
        self.target_y = y
        self.current_x = x
        self.current_y = y
        self.smoothing = 0.2   # 插值因子

        # 从服务器同步的状态
        self.remote_is_walking = False
        self.remote_is_attack = False
        self.remote_mouse_pos = Vec2(0, 0)


    def update(self):
        """更新远程玩家位置插值、动画、攻击模拟。"""
        # 位置插值
        self.current_x += (self.target_x - self.current_x) * self.smoothing
        self.current_y += (self.target_y - self.current_y) * self.smoothing
        # 设置精灵位置（如果使用物理引擎，需通过引擎移动，否则直接设置坐标）
        if self.physics_engine:
            self.physics_engine.set_position(self, (self.current_x, self.current_y))
        else:
            self.center_x = self.current_x
            self.center_y = self.current_y

        # 更新动画（行走、空闲等）
        self.is_walking = self.remote_is_walking
        super().update()  # 调用父类的 update 来更新纹理、方向等

        # 模拟攻击
        self._update_remote_attack()


    def _update_remote_attack(self):
        """根据远程攻击标志和冷却发射子弹。"""
        if self.is_attack:

            if self.cd == self.cd_max:
                self.cd = 0

            if self.cd == 0:
                if self.current_weapon.is_gun:
                    bullets = self.attack()
                    self.current_weapon.play_sound(self.window.effect_volume)  # 需要传入 window 引用
                    for bullet in bullets:
                        bullet.change_x = bullet.aim.x
                        bullet.change_y = bullet.aim.y
                        self.bullet_list.append(bullet)

        self.cd = min(self.cd + 1, self.cd_max)

    def apply_snapshot(self, data: dict):
        """从服务器快照更新目标位置和状态。"""
        self.target_x = data["x"]
        self.target_y = data["y"]
        self.remote_is_walking = data.get("is_walking", False)
        self.is_attack = data.get("is_attack", False)
        mouse = data.get("mouse_pos", {})
        self.remote_mouse_pos = Vec2(mouse.get("x", 0), mouse.get("y", 0))
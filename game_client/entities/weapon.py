import arcade
import math
from arcade import Color
from utils.utils import Utils
from pyglet.math import Vec2



class Bullet(arcade.Sprite):
    """子弹基类，负责子弹的基础属性与初始化。"""

    def __init__(self, filename="public/graphics/weapon/Bullet.png",
                 width=6,
                 height=6,
                 scale=1) -> None:
        """
        初始化子弹精灵。

        :param filename: 子弹图片路径
        :param width: 图片宽度（像素）
        :param height: 图片高度（像素）
        :param scale: 缩放比例
        """
        super().__init__(
            filename=filename,
            image_width=width,
            image_height=height,
            scale=scale,
        )
        self.aim = Vec2(0, 0)       # 子弹速度向量（方向×速度）
        self.speed = float(0)       # 子弹速率（标量）
        self.damage = int(0)        # 子弹造成的伤害值
        self.life_span = int(20)    # 子弹存活帧数（超时后自动移除）

    def set_angle(self, rotate_angle: float) -> None:
        """
        设置子弹的旋转角度（用于某些需要旋转弹头的特效）。
        :param rotate_angle: 角度（度）
        """
        self.angle = rotate_angle


class Weapon(arcade.Sprite):
    """武器基类，处理武器的位置、瞄准、发射子弹及音效。"""

    def __init__(
        self, weapon_name: str = "public/graphics/weapon/Pistol.png", x: float = 0, y: float = 0
    ) -> None:
        """
        初始化武器精灵。

        :param weapon_name: 武器图片路径
        :param x: 武器初始 X 坐标
        :param y: 武器初始 Y 坐标
        """
        self.is_gun = True                     # 是否为枪械（预留标志）
        self.pos = Vec2(x, y)                  # 武器位置（世界坐标）
        self.aim_pos = Vec2(0, 0)              # 瞄准点（世界坐标）

        self.is_right = True                   # 武器朝向：True=面向右侧，False=面向左侧

        self.damage = int(30)                  # 单发伤害
        self.cd_max = int(30)                  # 攻击冷却最大值（帧数）
        self.cd_min = int(8)                   # 攻击冷却最小值（帧数，用于射速波动）

        self.bullet_speed = 25                 # 子弹飞行速度（像素/帧）
        self.cost = int(0)                     # 弹药消耗（预留）
        self.life_span = int(20)               # 子弹存活帧数

        # 预加载两个方向的纹理：原始（向右）和水平翻转（向左）
        self.texture_list = [
            arcade.load_texture(weapon_name),
            arcade.load_texture(weapon_name, flipped_horizontally=True),
        ]

        super().__init__(
            filename=weapon_name,
            center_x=self.pos.x,
            center_y=self.pos.y,
            image_width=20,
            image_height=10,
        )

        self.sound = arcade.Sound("public/audio/wpn_fire_usp45.wav")  # 开火音效
        self.bullet = Bullet                                         # 使用的子弹类（可被子类覆盖）

    def update(self) -> None:
        """
        每帧更新武器位置，并根据朝向切换纹理。
        """
        self.center_x = self.pos.x
        self.center_y = self.pos.y

        if self.is_right:
            self.texture = self.texture_list[0]   # 面向右侧使用原始纹理
        else:
            self.texture = self.texture_list[1]   # 面向左侧使用翻转纹理

    def aim(self, aim_pos: Vec2) -> None:
        """
        根据瞄准点调整武器朝向和旋转角度。

        :param aim_pos: 瞄准点（屏幕或世界坐标），相对于武器位置的偏移量。
                        正 X 表示目标在右侧，负 X 表示在左侧。
        """
        self.aim_pos = aim_pos
        if aim_pos.x >= 0:
            self.is_right = True
            # 计算角度：asin(sin) 得到夹角，再用 degrees 转换为度
            rotate_angle = math.degrees(math.asin(Utils.get_sin(aim_pos)))
        else:
            self.is_right = False
            # 向左时角度为负，实现对称旋转
            rotate_angle = -math.degrees(math.asin(Utils.get_sin(aim_pos)))

        self.angle = rotate_angle

    def get_bullet(self) -> arcade.SpriteList:
        """
        生成一发子弹，并设置其初始位置、速度、伤害和存活时间。

        :return: 包含这颗子弹的 SpriteList（方便直接添加到场景中）
        """
        bullets = arcade.SpriteList()
        bullet = self.bullet()                     # 创建子弹实例
        bullet.center_x = self.center_x - 10       # 从武器左侧偏移 10 像素产生（避免与枪身重叠）
        bullet.center_y = self.center_y
        bullet.speed = self.bullet_speed
        bullet.life_span = self.life_span
        # 将瞄准方向归一化后乘以速度标量，得到速度向量
        bullet.aim = self.aim_pos.normalize().scale(bullet.speed)
        bullet.damage = self.damage
        bullets.append(bullet)
        return bullets

    def play_sound(self, effect_volume: int) -> None:
        """
        播放开火音效。

        :param effect_volume: 音效音量（0~20 之间的整数），除以 20 后归一化为 0~1
        """
        self.sound.play(volume=effect_volume / 20)



        
class Missile(Bullet):
    """Missile from the Rocket."""

    def __init__(self) -> None:
        super().__init__("graphics/weapon/Missile.png", 15, 15)

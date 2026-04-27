import arcade
import math

from arcade import Color
import utils
from pyglet.math import Vec2


class Bullet(arcade.Sprite):
    """Bullet base class."""

    def __init__(self, filename="graphics/weapon/Bullet.png",
                 width=6,
                 height=6,
                 scale=1) -> None:
        super().__init__(
            filename=filename,
            image_width=width,
            image_height=height,
            scale=scale,
        )
        self.aim = Vec2(0, 0)
        self.speed = float(0)
        self.damage = int(0)
        self.life_span = int(20)

    def set_angle(self, rotate_angle: float) -> None:
        """Rotate the bullet sprite when needed."""
        self.angle = rotate_angle

class Weapon(arcade.Sprite):
    """Weapon base class."""

    def __init__(
        self, weapon_name: str = "graphics/weapon/Pistol.png", x: float = 0, y: float = 0
    ) -> None:
        """武器初始化"""

        self.is_gun = True
        self.pos = Vec2(x, y)
        self.aim_pos = Vec2(0, 0)
        
        self.is_right = True

        self.damage = int(30)
        self.cd_max = int(30)  # 30/60 s
        self.cd_min = int(8)

        self.bullet_speed = 25
        self.cost = int(0)
        self.life_span = int(20) #生命周期
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
        
        self.sound = arcade.Sound("audio/wpn_fire_usp45.wav")
        self.bullet = Bullet


    def update(self) ->None:
        self.center_x = self.pos.x
        self.center_y = self.pos.y

        if self.is_right:
            self.texture = self.texture_list[0]
        else:
            self.texture = self.texture_list[1]
    

    def aim(self, aim_pos: Vec2) -> None:
        """Adjust the sprite angle to the aiming position."""

        self.aim_pos = aim_pos
        if aim_pos.x >= 0:
            self.is_right = True
            rotate_angle = math.degrees(
                math.asin(utils.Utils.get_sin(aim_pos)))
        else:
            self.is_right = False
            rotate_angle = - \
                math.degrees(math.asin(utils.Utils.get_sin(aim_pos)))

        self.angle = rotate_angle

    def get_bullet(self) -> arcade.SpriteList:
        """Get the bullet list shot by the weapon."""
        bullets = arcade.SpriteList()
        bullet = self.bullet()  # 创建子弹
        bullet.center_x = self.center_x - 10
        bullet.center_y = self.center_y
        bullet.speed = self.bullet_speed
        bullet.life_span = self.life_span
        bullet.aim = self.aim_pos.normalize().scale(bullet.speed)
        bullet.damage = self.damage
        bullets.append(bullet)
        return bullets

    def play_sound(self, effect_volume: int) -> None:
        self.sound.play(volume=effect_volume/20)
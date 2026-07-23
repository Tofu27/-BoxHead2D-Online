# character.py
import arcade
from game.utils import Utils, Color
import random
from pyglet.math import Vec2
from core.config_loader import ConfigLoader

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
    """Character base class."""

    def __init__(self, x: float = 0, y: float = 0,
                 physics_engine: arcade.PymunkPhysicsEngine = None,
                 config: dict = None) -> None:
        """
        初始化角色
        :param config: 从 JSON 加载的角色配置字典
        """
        # ===== 从配置读取属性（如果没有配置则使用默认值） =====
        self._config = config or {}
        
        # 基础属性
        self.health = self._config.get("health", 100)
        self.max_health = self.health
        self.speed = self._config.get("speed", 800)
        self.hit_damage = self._config.get("hit_damage", 20)

        self.move_left = False
        self.move_right = False
        self.move_up = False
        self.move_down = False
        
       
        # 运行时状态
        self.is_walking = False
        self.cd = int(0)
        self.cd_max = int(40)
        self.get_damage_len = int(0)

        # Init position
        self.pos = Vec2(x, y)
        self.last_pos = Vec2(0, 0)

        # Relative positions for visuals
        self.body_pos = Vec2(0, 0)
        self.foot_l_pos = Vec2(-8, -16)
        self.foot_r_pos = Vec2(8, -16)
        self.collider_pos = Vec2(0, -3)
        self.shadow_pos = Vec2(-1, -9)

        # Init collider and physics engine
        super().__init__(
            "resources/graphics/character/CharacterCollider.png",
            center_x=self.pos.x + self.collider_pos.x,
            center_y=self.pos.y + self.collider_pos.y,
            image_width=20,
            image_height=30,
            scale=1,
        )
        self.register_physics_engine(physics_engine)

        # Animation init
        self.body_move_up = False
        self.body_move_frames_max = len(BODY_ANIM)
        self.body_move_frames = self.body_move_frames_max
        self.walking_frames_max = len(L_WALK_X)
        self.walking_frames = self.walking_frames_max
        self.velocity = Vec2(0, 0)

        # Visuals
        self.body = arcade.Sprite()
        self.foot_l = arcade.Sprite(
            filename="resources/graphics/character/Foot.png",
            center_x=self.foot_l_pos.x + self.pos.x,
            center_y=self.foot_l_pos.y + self.pos.x,
            image_width=4,
            image_height=4,
            scale=1,
        )
        self.foot_r = arcade.Sprite(
            filename="resources/graphics/character/Foot.png",
            center_x=self.foot_r_pos.x + self.pos.x,
            center_y=self.foot_r_pos.y + self.pos.x,
            image_width=4,
            image_height=4,
            scale=1,
        )
        self.shadow = arcade.Sprite(
            center_x=self.collider_pos.x + self.pos.x,
            center_y=self.collider_pos.y + self.pos.x,
            scale=1,
        )
        self.shadow.texture = arcade.make_soft_square_texture(
            22, Color.LIGHT_BLACK, 160, 100)
        self.damage_sprite = arcade.SpriteSolidColor(20, 24,
                                                     Color.RED_TRANSPARENT)
        self.damage_sprite.alpha = 0

        self.parts = arcade.SpriteList()
        self.parts.append(self.shadow)
        self.parts.append(self.body)
        self.parts.append(self.foot_l)
        self.parts.append(self.foot_r)
        self.parts.append(self.damage_sprite)

    def move(self) -> None:
        """Move all the body parts"""
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
        self.move()

        # Body animation
        if self.body_move_frames == 0:  # reset frames
            self.body_move_frames = self.body_move_frames_max
            self.body_move_up = not self.body_move_up

        self.body_move_frames -= 1
        self.body.center_y += BODY_ANIM[self.body_move_frames]

        self.get_damage_len -= 1

        if self.get_damage_len > 0:
            self.damage_sprite.alpha = 150
        else:
            self.damage_sprite.alpha = 0


    def draw(self, *, filter=None, pixelated=None, blend_function=None) -> None:
        self.parts.draw()


    def register_dir_field(self, dir_field: dict) -> None:
        self.dir_field = dir_field

    def follow_dir(self) -> None:
        grid_x = int(self.center_x / Utils.WALL_SIZE)
        grid_y = int(self.center_y / Utils.WALL_SIZE)
        self.force = self.dir_field[(grid_x, grid_y)]
        self.force = self.force.scale(self.speed)

        # Since the character collider are square,
        # it is still possible to be stuck with a wall.
        cur_pos = Vec2(self.center_x, self.center_y)
        if cur_pos.distance(self.last_pos) < 0.0001 and self.is_walking:
            # Apply opposite force to avoid
            self.force.x = random.choice([-1.0, 1.0])
            self.force.y = random.choice([-1.0, 1.0])
            self.force = self.force.scale(10 * self.speed)

        self.physics_engines[0].apply_force(
            self, (self.force.x, self.force.y))
        self.last_pos = cur_pos


    """Play characters"""

class Player(Character):
    """Player game object."""

    body_texture = arcade.load_texture("resources/graphics/character/Player.png")
    name = "Nameless"
    description = "Nameless Description"

    def __init__(self, x: float = 0, y: float = 0,
                 physics_engine: arcade.PymunkPhysicsEngine = None) -> None:
        
        cfg = ConfigLoader().get("characters", "player", {})

        super().__init__(x, y, physics_engine, cfg)

        self.speed = 1600
        self.health = int(500)

        # Player body sprite
        self.body.texture = self.body_texture

        # Track the player movement input
        self.move_left = False
        self.move_right = False
        self.move_up = False
        self.move_down = False


    def move(self) -> None:
        """Player move by applying force from physics engine."""
        force = Vec2(0, 0)

        if self.move_up and not self.move_down:
            force.y = 1
        elif self.move_down and not self.move_up:
            force.y = -1
        if self.move_left and not self.move_right:
            force.x = -1
        elif self.move_right and not self.move_left:
            force.x = 1

        force = force.normalize().scale(self.speed)
        self.physics_engines[0].apply_force(self, (force.x, force.y))

        if force.mag != 0:
            self.is_walking = True
        else:
            self.is_walking = False

        super().move()

    def draw(self) -> None:
        super().draw()

    def update(self) -> None:
        super().update()

        # Feet animation
        if self.walking_frames == 0:  # reset frames
            self.walking_frames = self.walking_frames_max
            
        self.walking_frames -= 1

        if self.is_walking:
            self.foot_l.center_x += L_WALK_X[self.walking_frames]
            self.foot_l.center_y += L_WALK_Y[self.walking_frames]
            self.foot_r.center_x += R_WALK_X[self.walking_frames]
            self.foot_r.center_y += R_WALK_Y[self.walking_frames]
        else:
            # reset the walking animation
            self.foot_l.center_x = self.foot_l_pos.x + self.pos.x
            self.foot_l.center_y = self.foot_l_pos.y + self.pos.y
            self.foot_r.center_x = self.foot_r_pos.x + self.pos.x
            self.foot_r.center_y = self.foot_r_pos.y + self.pos.y
            self.walking_frames = self.walking_frames_max

    def register_mouse_pos(self, mouse_pos: Vec2) -> None:
        self.mouse_pos = mouse_pos


    def get_energy(self, energy: int) -> None:
        self.energy += energy

    def use_skill(self) -> None:
        # To be implemented for characters with active skill
        pass
import arcade
from views.base_view import FadingView
from utils.utils import Utils
from pyglet.math import Vec2
from arcade.pymunk_physics_engine import PymunkPhysicsEngine
from entities.character import Player
from entities.room import Room
from views.base_view import CAMERA_SPEED
from core.config import get_root_dir


ROOT_DIR = get_root_dir()

class GameView(FadingView):
    """Main game view."""

    def __init__(self):
        super().__init__()
        self.mouse_x = None
        self.mouse_y = None
        self.mouse_pos = Vec2(0, 0)
        self.mouse_sprite = arcade.Sprite(ROOT_DIR/"graphics/ui/Cursor.png")
        self.physics_engine = None
        self.manager = None

        # Sprite lists
        self.wall_list = None
        self.player = None

        
        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        self.camera_sprites = arcade.Camera(self.w, self.h)
        self.camera_gui = arcade.Camera(self.w, self.h)

    def setup(self, player: Player, map: Room) -> None:
        """Set up the game and initialize the variables."""

        # Play game BGM
        self.window.play_game_music(1)


        # Create the physics engine
        damping = 0.01
        gravity = (0, 0)
        self.physics_engine = PymunkPhysicsEngine(gravity, damping)

        
        # Game room setup
        self.room = map()
        
        # Set up the player
        self.player = player(
            float(self.room.width / 2), float(self.room.height / 2), self.physics_engine)
        
        self.player.register_mouse_pos(self.mouse_pos)


        # Set up the shop
        # self.shop = item.Shop(self.player)

        self.physics_engine.add_sprite(
            self.player,
            friction=0,
            moment_of_inertia=PymunkPhysicsEngine.MOMENT_INF,
            damping=0.001,
            collision_type="player",
            elasticity=0.1
        )
        self.physics_engine.add_sprite_list(
            self.room.walls,
            friction=0,
            collision_type="wall",
            body_type=PymunkPhysicsEngine.STATIC,
        )

    def on_draw(self) -> None:
        self.clear()
        self.camera_sprites.use() # 世界相机，绘制场景、玩家、敌人

        self.room.draw_ground()
        self.room.draw_walls()
        self.player.draw()

        self.camera_gui.use() # 切换 GUi相机，绘制准许，信息UI

        # Mouse cursor
        if self.mouse_x and self.mouse_y:
            self.mouse_sprite.draw()


    def on_update(self, delta_time) -> None:
        self.physics_engine.step()

        # Update player
        self.player.update()
        self.scroll_to_player()

    def on_key_press(self, key, modifiers) -> None:
        """Called whenever a key is pressed."""

        if key == arcade.key.W:
            self.player.move_up = True
        elif key == arcade.key.S:
            self.player.move_down = True
        elif key == arcade.key.A:
            self.player.move_left = True
        elif key == arcade.key.D:
            self.player.move_right = True

    def on_key_release(self, key, modifiers) -> None:

        if key == arcade.key.W:
            self.player.move_up = False
        elif key == arcade.key.S:
            self.player.move_down = False
        elif key == arcade.key.A:
            self.player.move_left = False
        elif key == arcade.key.D:
            self.player.move_right = False

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        """Mouse movement."""
        self.mouse_x = x
        self.mouse_y = y
        self.mouse_pos.x = self.mouse_x + self.camera_sprites.position.x
        self.mouse_pos.y = self.mouse_y + self.camera_sprites.position.y
        self.mouse_sprite.center_x = self.mouse_x
        self.mouse_sprite.center_y = self.mouse_y

    def scroll_to_player(self) -> None:
        x = self.player.pos.x - float(self.w / 2)
        if self.player.pos.x < float(self.w / 2):
            x = 0
        elif self.player.pos.x > float(self.room.width - self.w / 2):
            x = float(self.room.width - self.w)

        y = self.player.pos.y - float(self.h / 2)
        if self.player.pos.y < float(self.h / 2):
            y = 0
        elif self.player.pos.y > float(self.room.height - self.h / 2):
            y = float(self.room.height - self.h)

        self.camera_sprites.move_to((x, y), CAMERA_SPEED)

    def resize_camera(self, width, height) -> None:
        self.w = width
        self.h = height
        self.camera_sprites.resize(width, height)
        self.camera_gui.resize(width, height)

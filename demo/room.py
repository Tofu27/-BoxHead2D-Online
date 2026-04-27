import arcade
import math
import utils
from pyglet.math import Vec2

WALL_SIZE = 30          # 墙壁方块尺寸（像素）
HALF_WALL_SIZE = 15     # 墙壁方块半长

# ==================== 墙壁基类 ====================
class Wall(arcade.Sprite):
    """基本的墙壁方块（纯虚类，实际使用子类）。"""

    def __init__(self, x: float = 0, y: float = 0) -> None:
        self.pos = Vec2(x, y)
        self.grid_idx = (math.floor(x / 30), math.floor(y / 30))  # 地图格子索引
        self.shadow = None   # 阴影精灵（子类负责实例化）

        super().__init__(
            filename=None,
            center_x=self.pos.x,
            center_y=self.pos.y,
            image_width=WALL_SIZE,
            image_height=WALL_SIZE,
        )

# ==================== 墙角墙壁（有阴影偏移） ====================
class WallCorner(Wall):
    """位于房间角落的墙壁，带投影效果。"""

    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__(x, y)
        self.texture = arcade.load_texture("graphics/room/WallCorner.png")
        # 阴影向下、向左偏移3像素
        self.shadow = arcade.Sprite(
            center_x=self.pos.x - 3,
            center_y=self.pos.y - 3,
            scale=1,
        )
        self.shadow.texture = arcade.make_soft_square_texture(
            30, utils.Color.LIGHT_BLACK, 150, 150)

# ==================== 水平侧墙壁（上方或下方） ====================
class WallSideHorizontal(Wall):
    """水平方向的墙壁（上下边框），阴影向下偏移。"""

    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__(x, y)
        self.texture = arcade.load_texture("graphics/room/WallSide.png")
        self.shadow = arcade.Sprite(
            center_x=self.pos.x,
            center_y=self.pos.y - 3,
            scale=1,
        )
        self.shadow.texture = arcade.make_soft_square_texture(
            30, utils.Color.LIGHT_BLACK, 150, 150)

# ==================== 垂直侧墙壁（左侧或右侧） ====================
class WallSideVertical(Wall):
    """垂直方向的墙壁（左右边框），阴影向左偏移。"""

    def __init__(self, x: float = 0, y: float = 0) -> None:
        super().__init__(x, y)
        self.texture = arcade.load_texture("graphics/room/WallSide.png")
        self.angle = -90   # 旋转90度使其垂直
        self.shadow = arcade.Sprite(
            center_x=self.pos.x - 3,
            center_y=self.pos.y,
            scale=1,
        )
        self.shadow.texture = arcade.make_soft_square_texture(
            30, utils.Color.LIGHT_BLACK, 150, 150)

# ==================== 房间基类 ====================
class Room:
    """房间基类，包含墙壁布局和地面绘制。"""

    def __init__(self, width: float = 2100, height: float = 1200) -> None:
        self.width = width
        self.height = height
        self.pos = Vec2(self.width / 2, self.height / 2)

        # 计算地图网格尺寸（每个格子为WALL_SIZE）
        self.grid_w = int(self.width / WALL_SIZE)
        self.grid_h = int(self.height / WALL_SIZE)
        self.grid = {(i, j): 0 for i in range(self.grid_w)
                     for j in range(self.grid_h)}

        self.spawn_pos = []
        self.walls = arcade.SpriteList()   # 墙壁精灵列表
        self.shadows = arcade.SpriteList() # 阴影精灵列表

    def set_up_shadow(self) -> None:
        """将所有墙壁的阴影加入shadows列表，以便统一绘制。"""
        for wall in self.walls:
            self.shadows.append(wall.shadow)

    def draw_ground(self) -> None:
        """绘制地面颜色块。"""
        arcade.draw_rectangle_filled(
            self.pos.x, self.pos.y, self.width, self.height, utils.Color.GROUND_WHITE
        )

    def draw_walls(self) -> None:
        """先绘制所有墙壁的阴影，再绘制墙壁本身。"""
        self.shadows.draw()
        self.walls.draw()

    
    def setup_grid(self) -> None:
        for wall in self.walls:
            if (wall.grid_idx[0] < self.grid_w and wall.grid_idx[1] < self.grid_h
                    and wall.grid_idx[0] >= 0 and wall.grid_idx[1] >= 0):
                x = wall.grid_idx[0]
                y = wall.grid_idx[1]
                self.grid[x, y] = 1

# ==================== 开始菜单专用房间 ====================
class StartRoom(Room):
    """为开始菜单创建的房间，四周生成墙壁边界。"""

    def __init__(self, width: float = 2100, height: float = 1200) -> None:
        super().__init__(width, height)

        self.walls = arcade.SpriteList()
        # 四个角落的墙角墙
        self.walls.append(WallCorner(HALF_WALL_SIZE, HALF_WALL_SIZE))
        self.walls.append(WallCorner(HALF_WALL_SIZE, self.height - HALF_WALL_SIZE))
        self.walls.append(WallCorner(self.width - HALF_WALL_SIZE, HALF_WALL_SIZE))
        self.walls.append(WallCorner(self.width - HALF_WALL_SIZE, self.height - HALF_WALL_SIZE))

        # 上下两排水平墙壁（不包含角落）
        for i in range(1, self.grid_w - 1):
            self.walls.append(WallSideHorizontal(
                HALF_WALL_SIZE + i * WALL_SIZE, HALF_WALL_SIZE))
            self.walls.append(WallSideHorizontal(
                HALF_WALL_SIZE + i * WALL_SIZE, self.height - HALF_WALL_SIZE))

        # 左右两列垂直墙壁（不包含角落）
        for i in range(1, self.grid_h - 1):
            self.walls.append(WallSideVertical(
                HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))
            self.walls.append(WallSideVertical(
                self.width - HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))

        # 生成所有墙壁对应的阴影精灵
        self.set_up_shadow()



        
class GameRoom0(Room):
    """Game room No. 0"""

    layout_sprite = arcade.Sprite("graphics/room/GameRoom0.png")
    name = "Blank room"

    
    def __init__(self, width: float = 2100, height: float = 1200) -> None:
        super().__init__(width, height)

        # Set boundary corner walls
        self.walls = arcade.SpriteList()
        self.walls.append(WallCorner(HALF_WALL_SIZE, HALF_WALL_SIZE))
        self.walls.append(WallCorner(
            HALF_WALL_SIZE, self.height - HALF_WALL_SIZE))
        self.walls.append(WallCorner(
            self.width - HALF_WALL_SIZE, HALF_WALL_SIZE))
        self.walls.append(WallCorner(
            self.width - HALF_WALL_SIZE, self.height - HALF_WALL_SIZE))
        

        # Set bottom and top walls
        for i in range(1, self.grid_w - 1):
            if i == math.floor(self.grid_w/2) - 2 or i == math.floor(self.grid_w/2) + 2:
                self.walls.append(WallCorner(
                    HALF_WALL_SIZE + i * WALL_SIZE, HALF_WALL_SIZE))
                self.walls.append(WallCorner(
                    HALF_WALL_SIZE + i * WALL_SIZE, self.height - HALF_WALL_SIZE))
                continue
            if i >= math.floor(self.grid_w/2) - 1 and i <= math.floor(self.grid_w/2) + 1:
                self.spawn_pos.append(
                    Vec2(HALF_WALL_SIZE + i * WALL_SIZE, HALF_WALL_SIZE))
                self.spawn_pos.append(
                    Vec2(HALF_WALL_SIZE + i * WALL_SIZE, self.height - HALF_WALL_SIZE))
                continue
            self.walls.append(WallSideHorizontal(
                HALF_WALL_SIZE + i * WALL_SIZE, HALF_WALL_SIZE))
            self.walls.append(WallSideHorizontal(
                HALF_WALL_SIZE + i * WALL_SIZE, self.height - HALF_WALL_SIZE))
        
        # Set left and right walls
        for i in range(1, self.grid_h - 1):
            if i == math.floor(self.grid_h/2) - 2 or i == math.floor(self.grid_h/2) + 2:
                self.walls.append(WallCorner(
                    HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))
                self.walls.append(WallCorner(
                    self.width - HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))
                continue
            if i >= math.floor(self.grid_h/2) - 1 and i <= math.floor(self.grid_h/2) + 1:
                self.spawn_pos.append(
                    Vec2(HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))
                self.spawn_pos.append(
                    Vec2(self.width - HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))
                continue
            self.walls.append(WallSideVertical(
                HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))
            self.walls.append(WallSideVertical(
                self.width - HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))
            
        self.setup_grid()

        # Set boundary walls
        for i in range(math.floor(self.grid_w/2) - 2, math.floor(self.grid_w/2) + 2):
            self.walls.append(WallCorner(
                HALF_WALL_SIZE + i * WALL_SIZE, -HALF_WALL_SIZE))
            self.walls.append(WallCorner(
                HALF_WALL_SIZE + i * WALL_SIZE, self.height + HALF_WALL_SIZE))
        for i in range(math.floor(self.grid_h/2) - 2, math.floor(self.grid_h/2) + 2):
            self.walls.append(WallCorner(
                -HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))
            self.walls.append(WallCorner(
                self.width + HALF_WALL_SIZE, HALF_WALL_SIZE + i * WALL_SIZE))

        self.set_up_shadow()
# client/core/resource_manager.py
import json
import os
import arcade
from typing import Optional, Dict, List, Tuple

class ResourceManager:
    """
    资源管理器单例
    负责加载地图、精灵、音频等资源
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 资源路径
        self._resource_dir = os.path.join(os.path.dirname(__file__), "..", "resources")
        self._map_data: Optional[dict] = None
        self._tile_map: Optional[arcade.TileMap] = None
        self._wall_list: Optional[arcade.SpriteList] = None
        self._ground_list: Optional[arcade.SpriteList] = None


        # ✅ 地图尺寸（像素）
        self._map_width: int = 0
        self._map_height: int = 0

        # 碰撞矩阵（与 Go 服务端保持一致）
        self._collision_grid: List[List[bool]] = []

    # ==================== 地图加载 ====================

    def load_map(self, map_path: str = None) -> bool:
        """
        加载地图文件
        :param map_path: 地图文件路径，默认 resources/map1.json
        :return: 是否加载成功
        """
        if map_path is None:
            map_path = os.path.join(self._resource_dir, "map1.json")

        if not os.path.exists(map_path):
            print(f"地图文件不存在: {map_path}")
            return False

        # 1. 读取 JSON 数据（用于服务端逻辑复用）
        with open(map_path, 'r', encoding='utf-8') as f:
            self._map_data = json.load(f)

        # 2. 使用 Arcade 加载 TileMap（用于渲染和本地物理）
        # Arcade 可以直接加载 .tmx 或 .json
        try:
            self._tile_map = arcade.load_tilemap(map_path)
            self._wall_list = self._tile_map.sprite_lists.get("wall")
            # 如果有地面图层，也可以加载
            self._ground_list = self._tile_map.sprite_lists.get("ground")
        except Exception as e:
            print(f"Arcade 加载地图失败: {e}")
            return False
        
        tile_width = self._map_data.get("tilewidth", 30)
        tile_height = self._map_data.get("tileheight", 30)
        map_width_tiles = self._map_data.get("width", 0)
        map_height_tiles = self._map_data.get("height", 0)
        self._map_width = map_width_tiles * tile_width
        self._map_height = map_height_tiles * tile_height

        # 3. 构建碰撞矩阵（与 Go 服务端保持一致）
        self._build_collision_grid()

        print(f"地图加载成功: {map_path}")
        print(f"  地图尺寸: {self._tile_map.width} x {self._tile_map.height}")
        print(f"  Wall 精灵数: {len(self._wall_list) if self._wall_list else 0}")
        return True

    def _build_collision_grid(self):
        """从地图数据构建碰撞矩阵（与 Go 服务端逻辑一致）"""
        if not self._map_data:
            return

        # 找到 wall 图层
        wall_layer = None
        for layer in self._map_data.get("layers", []):
            if layer.get("name") == "wall":
                wall_layer = layer
                break

        if not wall_layer:
            print("警告: 未找到 'wall' 图层")
            return

        width = wall_layer.get("width", 0)
        height = wall_layer.get("height", 0)
        data = wall_layer.get("data", [])

        # 构建二维布尔矩阵
        self._collision_grid = []
        for y in range(height):
            row = []
            for x in range(width):
                idx = y * width + x
                # 判断是否为碰撞格（非 0 且非纯空）
                # 注意：Tiled 中 0 表示空，其他值表示有图块
                is_collision = (data[idx] != 0)
                row.append(is_collision)
            self._collision_grid.append(row)

    # ==================== 获取资源 ====================

    def get_wall_list(self) -> Optional[arcade.SpriteList]:
        """获取墙精灵列表（用于物理碰撞）"""
        return self._wall_list

    def get_ground_list(self) -> Optional[arcade.SpriteList]:
        """获取地面精灵列表（用于渲染）"""
        return self._ground_list

    def get_tile_map(self) -> Optional[arcade.TileMap]:
        """获取完整的 TileMap 对象"""
        return self._tile_map

    def get_collision_grid(self) -> List[List[bool]]:
        """获取碰撞矩阵（用于服务端逻辑参考）"""
        return self._collision_grid
    
    def get_map_wh(self) -> Tuple[int, int]:
        return self._map_width, self._map_height

    def is_walkable(self, tile_x: int, tile_y: int) -> bool:
        """
        判断某个 Tile 坐标是否可通行
        与 Go 服务端逻辑保持一致
        """
        if tile_y < 0 or tile_y >= len(self._collision_grid):
            return False
        if tile_x < 0 or tile_x >= len(self._collision_grid[tile_y]):
            return False
        return not self._collision_grid[tile_y][tile_x]

    def world_to_tile(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """将世界坐标转换为 Tile 坐标"""
        tile_size = 32  # 与 Tiled 设置一致
        tile_x = int(world_x // tile_size)
        tile_y = int(world_y // tile_size)
        return tile_x, tile_y

    def is_walkable_world(self, world_x: float, world_y: float) -> bool:
        """判断世界坐标是否可通行"""
        tile_x, tile_y = self.world_to_tile(world_x, world_y)
        return self.is_walkable(tile_x, tile_y)
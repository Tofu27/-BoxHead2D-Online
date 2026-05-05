import math
import pickle
from pyglet.math import Vec2
import arcade.gui
from core.settings import Setting 
from config import get_root_dir

ROOT_DIR = get_root_dir()

class Utils:
    """Utility functions."""

    @staticmethod
    def round_to_multiple(number: int, multiple: int) -> int:
        """Round n to the nearest multiple of m."""
        quotient = round(number / multiple)
        return quotient * multiple

    @staticmethod
    def get_sin(v: Vec2) -> float:
        """Get sine value of a given vector."""
        d = v.distance(Vec2(0, 0))
        d = 0.001 if d == 0 else d
        return v.y / d
    
    
    @staticmethod
    def clear_ui_manager(manager: arcade.gui.UIManager):
        for _ in range(0, len(manager.children[0])):
            manager.clear()
        manager.clear()

        
    @staticmethod
    def save_settings(window: arcade.Window):
        with open(ROOT_DIR/"data/settings.bin", "wb") as setting_file:
            settings = Setting(window.effect_volume,
                               window.music_volume,
                               window.res_index,
                               window.fullscreen,
                               window.lang_idx)
            pickle.dump(settings, setting_file)
import arcade

class AssetLoader:
    """统一加载所有游戏资源，返回结构化字典。"""
    def __init__(self):
        self.sounds = {}
        self.music = {}

    def load_all(self):
        self._load_sounds()
        self._load_music()
        self._load_fonts()
        return self

    def _load_sounds(self):
        self.sounds = {
            "button": arcade.Sound("public/audio/ui_click.wav"),
            "explosion": arcade.Sound("public/audio/explosion_2.wav"),
            "refresh": arcade.Sound("public/audio/ui_refresh.wav"),
            "purchase": arcade.Sound("public/audio/ui_purchase.wav"),
            "purchase_fail": arcade.Sound("public/audio/ui_purchase_fail.wav"),
            "round_start": arcade.Sound("public/audio/round_start.wav"),
            "game_over": arcade.Sound("public/audio/game_over.wav"),
            "game_win": arcade.Sound("public/audio/mission_complete.wav"),
        }

    def _load_music(self):
        self.music = {
            "start": arcade.Sound("public/audio/the-best-jazz-club-in-new-orleans-164472.wav"),
            "game": arcade.Sound("public/audio/zapsplat_game_music_medium_action_electronic_techno.wav"),
        }

    def _load_fonts(self):
        # 加载自定义字体
        arcade.load_font("public/fonts/FFFFORWA.ttf")
        arcade.load_font("public/fonts/Cubic_11_1.013_R.ttf")
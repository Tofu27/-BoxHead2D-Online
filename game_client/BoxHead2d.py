import arcade
import pickle
from config import get_root_dir
from core.assets.asset_loader import AssetLoader
from core.settings import Setting 
from core.language import Language
from views.default_view import DefaultView, OptionView
from views.menu.start_view import StartView
from views.menu.selection_view import SelectionView

ROOT_DIR = get_root_dir()

class BoxHead2d(arcade.Window):
    def __init__(self):
        # 加载设置
        try:
            settings = pickle.load(open(ROOT_DIR / "data/settings.bin", "rb"))
        except OSError:
            settings = Setting(e_volume=2, m_volume=2, r_idx=0, fullscreen=False, lang_idx=1)
            pickle.dump(settings, open(ROOT_DIR / "data/settings.bin", "wb"))

        self.effect_volume = settings.effect_volume
        self.music_volume = settings.music_volume
        self.res_index = settings.res_index
        self.lang_idx = settings.lang_idx
        self.lang = [Language.EN, Language.CN]
        self.cur_lang = self.lang[self.lang_idx]
        self.w_scale = [1024, 1280, 1440, 1920]
        self.h_scale = [600, 720, 900, 1080]

        super().__init__(self.w_scale[self.res_index], self.h_scale[self.res_index], self.cur_lang.TITLE)
        self.set_fullscreen(self.fullscreen)

        # 资源系统
        self.assets = AssetLoader().load_all()

        # 音乐播放器
        self.start_music_player = None
        self.game_music_player = None
        self._init_music()

        # 视图引用（临时）
        self.start_view = StartView()
        self.option_view = OptionView()
        self.select_view = SelectionView()
        self.default_view = DefaultView
        self.game_view = None

    def _init_music(self):
        self.start_music_player = self.assets.music["start"].play(volume=self.music_volume / 20, loop=True)
        self.start_music_player.pause()
        self.game_music_player = self.assets.music["game"].play(volume=self.music_volume / 20, loop=True)
        self.game_music_player.pause()

    def play_sound(self, name):
        """通过字典键播放音效"""
        sound = self.assets.sounds.get(name)
        if sound:
            sound.play(volume=self.effect_volume / 20)
        else:
            print(f"音效 '{name}' 未找到")

    # 便捷音效方法
    def play_button_sound(self): self.play_sound("button")
    def play_explosion_sound(self): self.play_sound("explosion")
    def play_refresh_sound(self): self.play_sound("refresh")
    def play_purchase_sound(self): self.play_sound("purchase")
    def play_purchase_fail_sound(self): self.play_sound("purchase_fail")
    def play_round_start_sound(self): self.play_sound("round_start")
    def play_game_over_sound(self): self.play_sound("game_over")
    def play_game_win_sound(self): self.play_sound("game_win")

    def play_start_music(self, idx=0):
        if self.game_music_player and self.game_music_player.playing:
            self.game_music_player.pause()
        if self.start_music_player:
            if not self.start_music_player.playing:   # 如果没有在播放才启动
                self.start_music_player.play()

    def play_game_music(self, idx=0):
        self.start_music_player.pause()
        self.game_music_player.play()

    def update_music_volume(self):
        self.start_music_player.volume = self.music_volume / 20
        self.game_music_player.volume = self.music_volume / 20

    def set_cur_lang(self, idx):
        self.lang_idx = idx
        self.cur_lang = self.lang[self.lang_idx]
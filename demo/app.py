import arcade
import view
import utils
import pickle

# ==================== BoxHead2d 主窗口类 ====================
class BoxHead2d(arcade.Window):
    """游戏主窗口类，管理设置、资源加载和视图切换。"""

    def __init__(self):
        # 尝试从文件中加载设置（音量、分辨率、语言等）
        try:
            settings = pickle.load(open("data/settings.bin", "rb"))
        except (OSError) as e:
            # 若文件不存在，使用默认设置并保存
            settings = utils.Setting(e_volume=2,
                                     m_volume=2,
                                     r_idx=0,
                                     fullscreen=False,
                                     lang_idx=0)
            pickle.dump(settings, open("data/settings.bin", "wb"))

        # 应用加载的设置
        self.effect_volume = settings.effect_volume
        self.music_volume = settings.music_volume
        self.res_index = settings.res_index
        self.lang = [utils.Language.EN, utils.Language.CN]  # 支持的语言
        self.lang_idx = settings.lang_idx
        self.cur_lang = self.lang[self.lang_idx]           # 当前语言
        self.w_scale = [1024, 1280, 1440, 1920]            # 可选分辨率宽度
        self.h_scale = [600, 720, 900, 1080]               # 可选分辨率高度

        # 调用父类初始化，创建游戏窗口
        super().__init__(self.w_scale[self.res_index],
                         self.h_scale[self.res_index],
                         self.cur_lang.TITLE)
        
        # 根据设置决定是否全屏
        self.set_fullscreen(settings.fullscreen)

        self.start_view = None   # 用于视图切换的临时变量
        self.option_view = None
        self.select_view = None
        self.game_view = None
        self.game_over_view = None
        self.game_win_view = None

    def set_up(self) -> None:
        """加载字体、音效、音乐，并预播放背景音乐（初始暂停）。"""
        # 加载自定义字体
        arcade.load_font("fonts/FFFFORWA.ttf")
        arcade.load_font("fonts/Cubic_11_1.013_R.ttf")

        # 加载音效（点击、爆炸、刷新、购买、失败、回合开始、游戏结束、胜利）
        self.button_sound = arcade.Sound("audio/ui_click.wav")
        self.explosion_sound = arcade.Sound("audio/explosion_2.wav")
        self.explosion_sound_cnt: int = 0
        self.refresh_sound = arcade.Sound("audio/ui_refresh.wav")
        self.purchase_sound = arcade.Sound("audio/ui_purchase.wav")
        self.purchase_fail_sound = arcade.Sound("audio/ui_purchase_fail.wav")
        self.round_start_sound = arcade.Sound("audio/round_start.wav")
        self.game_over_sound = arcade.Sound("audio/game_over.wav")
        self.game_win_sound = arcade.Sound("audio/mission_complete.wav")

        # 加载背景音乐（开始界面和游戏界面）
        self.start_music = arcade.Sound(
            "audio/the-best-jazz-club-in-new-orleans-164472.wav")
        self.game_music = arcade.Sound(
            "audio/zapsplat_game_music_medium_action_electronic_techno.wav")


        self.option_view = view.OptionView()
        self.select_view = view.SelectionView()


        # 创建音乐播放器并立即暂停，稍后根据场景决定播放
        self.start_music_player = self.start_music.play(
            volume=self.music_volume/20, loop=True)
        self.start_music_player.pause()
        self.game_music_player = self.game_music.play(
            volume=self.music_volume/20, loop=True)
        self.game_music_player.pause()

        
    def play_button_sound(self) -> None:
        self.button_sound.play(volume=self.effect_volume/20)

    def play_explosion_sound(self) -> None:
        if self.explosion_sound_cnt == 0:
            # Avoid too many explosion noisy
            self.explosion_sound.play(volume=self.effect_volume/20)
            self.explosion_sound_cnt = 18

    def play_refresh_sound(self) -> None:
        self.refresh_sound.play(volume=self.effect_volume/20)

    def play_purchase_sound(self) -> None:
        self.purchase_sound.play(volume=self.effect_volume/20)

    def play_purchase_fail_sound(self) -> None:
        self.purchase_fail_sound.play(volume=self.effect_volume/20)

    def play_round_start_sound(self) -> None:
        self.round_start_sound.play(volume=self.effect_volume/20)

    def play_game_over_sound(self) -> None:
        self.game_over_sound.play(volume=self.effect_volume/20)

    def play_game_win_sound(self) -> None:
        self.game_win_sound.play(volume=self.effect_volume/20)

    def update_music_volume(self) -> None:
        self.start_music_player.volume = self.music_volume/20
        self.game_music_player.volume = self.music_volume/20

    def play_start_music(self, music_idx: int) -> None:
        """切换到开始界面的背景音乐。"""
        self.game_music_player.pause()      # 暂停游戏音乐
        self.start_music_player.play()      # 播放开始音乐

    def play_game_music(self, music_idx: int) -> None:
        self.start_music_player.pause()
        self.game_music_player.play()
        
    def set_cur_lang(self, lang_idx: int) -> None:
        self.lang_idx = lang_idx
        self.cur_lang = self.lang[self.lang_idx]

# ==================== 主函数入口 ====================
def main():
    """游戏启动函数：创建窗口、初始化资源、显示默认视图并运行主循环。"""
    game = BoxHead2d()
    game.set_up()
    default = view.DefaultView()
    default.setup()
    game.show_view(default)   # 显示默认视图（按任意键开始）
    arcade.run()

if __name__ == "__main__":
    main()
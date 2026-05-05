import arcade
import arcade.gui
from arcade.pymunk_physics_engine import PymunkPhysicsEngine

FADE_RATE = 8   # 淡入淡出速度（每帧变化量）
CAMERA_SPEED = 1

# ==================== 淡入淡出过渡视图基类 ====================
class FadingView(arcade.View):
    """支持淡入淡出转场效果的视图基类。"""

    def __init__(self) -> None:
        super().__init__()
        self.fade_out = None    # 淡出值（0-255），None表示未开始淡出
        self.fade_in = 255      # 淡入值（从255降到0）
        self.w, self.h = self.window.get_size()
        self.next_view = None   # 要切换到的下一个视图类

    def update_fade(self) -> None:
        """每帧更新淡出/淡入状态，完成后自动切换视图。"""
        if self.fade_out is not None:
            self.fade_out += FADE_RATE
            # 淡出完成且存在下一个视图时，切换视图
            if self.fade_out > 255 and self.next_view is not None:
                self.window.start_view = self.next_view()
                self.window.start_view.setup()
                self.window.show_view(self.window.start_view)

        if self.fade_in is not None:
            self.fade_in -= FADE_RATE
            if self.fade_in <= 0:
                self.fade_in = None   # 淡入完成

    def draw_fading(self) -> None:
        """绘制半透明遮罩实现淡入淡出效果。"""
        if self.fade_out is not None:
            arcade.draw_rectangle_filled(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height,
                (0, 0, 0, self.fade_out),
            )

        if self.fade_in is not None:
            arcade.draw_rectangle_filled(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height,
                (0, 0, 0, self.fade_in),
            )


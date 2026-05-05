# ==================== 主函数入口 ====================
import arcade
from BoxHead2d import BoxHead2d

def main():
    """游戏启动函数：创建窗口、初始化资源、显示默认视图并运行主循环。"""
    game = BoxHead2d()
    # game.set_up()
    default = game.default_view()
    default.setup()
    game.show_view(default)   # 显示默认视图（按任意键开始）
    arcade.run()

if __name__ == "__main__":
    main()
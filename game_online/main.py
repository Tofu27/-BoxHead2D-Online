from pathlib import Path
from core.config import set_root_dir

# main.py 所在目录就是项目根
set_root_dir(Path(__file__).resolve().parent)

import arcade
from entities.BoxHead2d import BoxHead2d




# ==================== 主函数入口 ====================
def main():
    """游戏启动函数：创建窗口、初始化资源、显示默认视图并运行主循环。"""
    game = BoxHead2d()
    game.set_up()
    default = game.default_view()
    default.setup()
    game.show_view(default)   # 显示默认视图（按任意键开始）
    arcade.run()

if __name__ == "__main__":
    main()
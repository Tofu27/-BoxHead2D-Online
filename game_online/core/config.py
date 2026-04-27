from pathlib import Path

_root_dir: Path = Path(".")  # 私有变量，初始值任意

def set_root_dir(path: Path):
    """由 main.py 调用，设置根目录"""
    global _root_dir
    _root_dir = path

def get_root_dir() -> Path:
    """返回项目根目录，任何模块需要路径时调用它"""
    return _root_dir





# 服务器配置（Golang 后端地址）
SERVER_WS = "ws://localhost:8080/ws"
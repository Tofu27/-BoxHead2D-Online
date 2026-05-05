from pathlib import Path

_root_dir: Path = Path(".")

def set_root_dir(path: Path):
    global _root_dir
    _root_dir = path

def get_root_dir() -> Path:
    return _root_dir
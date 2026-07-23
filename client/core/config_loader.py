# core/config_loader.py
import json
import os

class ConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance._loaded = False
        return cls._instance

    def load(self, config_dir="resources"):
        if self._loaded:
            return  # ✅ 防止重复加载
        self._loaded = True

        files = ["characters.json", "weapons.json", "bullets.json"]
        for f in files:
            path = os.path.join(config_dir, f)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as fp:
                    key = f.replace('.json', '')
                    self._data[key] = json.load(fp)
                    print(f"加载配置: {key}")
            else:
                print(f"警告: 配置文件不存在 {path}")

    def get(self, category, key, default=None):
        return self._data.get(category, {}).get(key, default)
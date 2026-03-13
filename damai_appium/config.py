# -*- coding: UTF-8 -*-
"""
__Author__ = "WECENG"
__Version__ = "1.0.0"
__Description__ = "配置类"
__Created__ = 2023/10/27 09:54
"""
import json


class Config:
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

    @staticmethod
    def load_config():
        with open("config.jsonc", "r", encoding="utf-8") as f:
            raw = json.load(f)

        return Config(dict(raw))

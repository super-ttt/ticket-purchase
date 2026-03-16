# -*- coding: UTF-8 -*-
"""配置类"""
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

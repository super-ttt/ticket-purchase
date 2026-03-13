# -*- coding: UTF-8 -*-
"""
__Author__ = "WECENG"
__Version__ = "1.0.0"
__Description__ = "配置类"
__Created__ = 2023/10/27 09:54
"""
import json


class Config:
    def __init__(self, server_url, keyword, users, city, date, price_indices, if_commit_order,
                 max_retries=3,
                 retry_interval_sec=0.1,
                 reinit_driver_on_retry=False,
                 default_wait_sec=1.0,
                 fast_click_timeout_sec=0.3,
                 smart_click_timeout_sec=0.3,
                 user_find_timeout_sec=0.8,
                 user_fuzzy_timeout_sec=0.5,
                 batch_click_delay_sec=0.02,
                 quantity_click_delay_sec=0.01,
                 post_run_sleep_sec=0.2,
                 skip_city_selection=False,
                 price_fast_timeout_sec=0.25,
                 price_fallback_timeout_sec=0.8,
                 order_modal_retry_max=10,
                 order_modal_retry_wait_sec=0.1):
        self.server_url = server_url
        self.keyword = keyword
        self.users = users
        self.city = city
        self.date = date
        self.price_indices = price_indices
        self.if_commit_order = if_commit_order

        # 重试与节奏配置
        self.max_retries = max_retries
        self.retry_interval_sec = retry_interval_sec
        self.reinit_driver_on_retry = reinit_driver_on_retry

        # 显式等待/点击节奏配置
        self.default_wait_sec = default_wait_sec
        self.fast_click_timeout_sec = fast_click_timeout_sec
        self.smart_click_timeout_sec = smart_click_timeout_sec
        self.user_find_timeout_sec = user_find_timeout_sec
        self.user_fuzzy_timeout_sec = user_fuzzy_timeout_sec
        self.batch_click_delay_sec = batch_click_delay_sec
        self.quantity_click_delay_sec = quantity_click_delay_sec
        self.post_run_sleep_sec = post_run_sleep_sec
        self.skip_city_selection = skip_city_selection
        self.price_fast_timeout_sec = price_fast_timeout_sec
        self.price_fallback_timeout_sec = price_fallback_timeout_sec
        # 提交订单遇「同一时间下单人数过多」弹窗时：order_modal_retry_max=最大重试次数；order_modal_retry_wait_sec=点击「继续尝试」后等待秒数再尝试提交
        self.order_modal_retry_max = order_modal_retry_max
        self.order_modal_retry_wait_sec = order_modal_retry_wait_sec

    @staticmethod
    def load_config():
        with open('config.jsonc', 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)

        return Config(
            config['server_url'],
            config['keyword'],
            config['users'],
            config['city'],
            config['date'],
            config.get('price_indices', []) if 'price_indices' in config else ([config['price_index']] if 'price_index' in config else []),
            config['if_commit_order'],
            config.get('max_retries', 3),
            config.get('retry_interval_sec', 0.1),
            config.get('reinit_driver_on_retry', False),
            config.get('default_wait_sec', 2.0),
            config.get('fast_click_timeout_sec', 0.8),
            config.get('smart_click_timeout_sec', 0.8),
            config.get('user_find_timeout_sec', 0.8),
            config.get('user_fuzzy_timeout_sec', 0.5),
            config.get('batch_click_delay_sec', 0.02),
            config.get('quantity_click_delay_sec', 0.01),
            config.get('post_run_sleep_sec', 0.2),
            config.get('skip_city_selection', False),
            config.get('price_fast_timeout_sec', 0.25),
            config.get('price_fallback_timeout_sec', 0.8),
            config.get('order_modal_retry_max', 10),
            config.get('order_modal_retry_wait_sec', 0.1),
        )
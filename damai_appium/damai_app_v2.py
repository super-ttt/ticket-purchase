# -*- coding: UTF-8 -*-
"""
大麦 app 抢票自动化 - 优化版
"""
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By

from config import Config
from damai_app_driver import setup_driver, safe_quit_driver
from damai_app_utils import ultra_fast_click
from damai_app_flow import (
    poll_until_booking_clickable,
    select_date_if_needed,
    select_price_by_indices,
    go_back_after_price_miss,
    submit_order_with_fallback,
)


class DamaiBot:
    def __init__(self):
        t0 = time.time()
        self.config = Config.load_config()
        self.driver = None
        self.wait = None
        self._setup_driver()
        print(f"[流程] 初始化驱动: 耗时 {time.time() - t0:.3f}s")

    def _setup_driver(self):
        """初始化驱动配置"""
        self.driver, self.wait = setup_driver(self.config)

    def _safe_quit_driver(self):
        """安全关闭 driver"""
        safe_quit_driver(self.driver)
        self.driver = None
        self.wait = None

    def run_ticket_grabbing(self):
        """执行抢票主流程"""
        try:
            print("开始抢票流程...")
            start_time = time.time()

            t1 = time.time()
            print("选择场次...")
            if not select_date_if_needed(self.driver, self.config):
                print(f"[流程] 选择场次: 失败，耗时 {time.time() - t1:.3f}s")
                return False
            print(f"[流程] 选择场次: 耗时 {time.time() - t1:.3f}s")

            t2 = time.time()
            print("等待并点击预约/购买入口...")
            if not poll_until_booking_clickable(self.driver, self.config):
                print(f"[流程] 预约/购买入口: 失败（轮询超时），耗时 {time.time() - t2:.3f}s")
                return False
            print(f"[流程] 预约/购买入口: 耗时 {time.time() - t2:.3f}s")

            t3 = time.time()
            print("选择票价...")
            if not select_price_by_indices(self.driver, self.config):
                print(f"[流程] 选择票价: 失败，耗时 {time.time() - t3:.3f}s")
                go_back_after_price_miss(self.driver, self.config)
                return False
            print(f"[流程] 选择票价: 耗时 {time.time() - t3:.3f}s")

            t4 = time.time()
            print("确定购买...")
            if not ultra_fast_click(self.driver, self.config, By.ID, "btn_buy_view"):
                if not ultra_fast_click(
                    self.driver,
                    self.config,
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textMatches(".*确定.*|.*购买.*")',
                ):
                    print(f"[流程] 确定购买: 失败，耗时 {time.time() - t4:.3f}s")
                    return False
            time.sleep(0.15)
            print(f"[流程] 确定购买: 耗时 {time.time() - t4:.3f}s")

            if self.config.if_commit_order:
                t5 = time.time()
                print("提交订单...")
                if not submit_order_with_fallback(self.driver, self.config):
                    print(f"[流程] 提交订单: 失败，耗时 {time.time() - t5:.3f}s")
                    return False
                print(f"[流程] 提交订单: 耗时 {time.time() - t5:.3f}s")
            else:
                print("if_commit_order=false，跳过提交订单")

            print(f"[流程] 抢票流程完成，总耗时: {time.time() - start_time:.3f}s")
            return True

        except Exception as e:
            print(f"抢票过程发生错误: {e}")
            return False
        finally:
            time.sleep(self.config.post_run_sleep_sec)

    def run_with_retry(self, max_retries=None):
        """带重试机制的抢票"""
        max_retries = self.config.max_retries if max_retries is None else max_retries
        total_start = time.time()
        try:
            for attempt in range(max_retries):
                attempt_start = time.time()
                print(f"[流程] 第 {attempt + 1}/{max_retries} 次尝试...")

                if not self.driver or not getattr(self.driver, "session_id", None):
                    t0 = time.time()
                    self._setup_driver()
                    print(f"[流程] 重新初始化驱动: 耗时 {time.time() - t0:.3f}s")

                if self.run_ticket_grabbing():
                    print(f"[流程] 抢票成功！本轮耗时 {time.time() - attempt_start:.3f}s，总耗时 {time.time() - total_start:.3f}s")
                    return True
                else:
                    print(f"[流程] 第 {attempt + 1} 次尝试失败，耗时 {time.time() - attempt_start:.3f}s")
                    if attempt < max_retries - 1:
                        print(f"{self.config.retry_interval_sec}秒后重试...")
                        time.sleep(self.config.retry_interval_sec)
                        if self.config.reinit_driver_on_retry:
                            self._safe_quit_driver()
                            self._setup_driver()

            print(f"[流程] 所有尝试均失败，总耗时 {time.time() - total_start:.3f}s")
            return False
        finally:
            self._safe_quit_driver()


if __name__ == "__main__":
    bot = DamaiBot()
    bot.run_with_retry()

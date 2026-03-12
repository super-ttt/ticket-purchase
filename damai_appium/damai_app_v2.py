# -*- coding: UTF-8 -*-
"""
__Author__ = "BlueCestbon"
__Version__ = "2.0.0"
__Description__ = "大麦app抢票自动化 - 优化版"
__Created__ = 2025/09/13 19:27
"""

import os
import time
from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import Config


class DamaiBot:
    def __init__(self):
        self.config = Config.load_config()
        self.driver = None
        self.wait = None
        self._setup_driver()

    def _safe_quit_driver(self):
        """安全关闭 driver，避免 InvalidSessionIdException 中断流程"""
        if not self.driver:
            return
        try:
            self.driver.quit()
        except Exception:
            pass
        finally:
            self.driver = None
            self.wait = None

    def _setup_driver(self):
        """初始化驱动配置"""
        capabilities = {
            "platformName": "Android",  # 操作系统
            "deviceName": "Android",  # 通用设备名（避免写死 emulator）
            "appPackage": "cn.damai",  # app 包名
            "appActivity": ".launcher.splash.SplashMainActivity",  # app 启动 Activity
            "unicodeKeyboard": True,  # 支持 Unicode 输入
            "resetKeyboard": True,  # 隐藏键盘
            "noReset": True,  # 不重置 app
            "newCommandTimeout": 6000,  # 超时时间
            "automationName": "UiAutomator2",  # 使用 uiautomator2
            "skipServerInstallation": False,  # 跳过服务器安装
            "ignoreHiddenApiPolicyError": True,  # 忽略隐藏 API 策略错误
            "disableWindowAnimation": True,  # 禁用窗口动画
            # 优化性能配置
            "mjpegServerFramerate": 1,  # 降低截图帧率
            "shouldTerminateApp": False,
            "adbExecTimeout": 20000,
        }

        # 可选：通过环境变量精确指定设备/系统版本（不设置则自动匹配当前可用设备）
        if os.getenv("ANDROID_UDID"):
            capabilities["udid"] = os.getenv("ANDROID_UDID")
            capabilities["deviceName"] = os.getenv("ANDROID_UDID")
        if os.getenv("ANDROID_PLATFORM_VERSION"):
            capabilities["platformVersion"] = os.getenv("ANDROID_PLATFORM_VERSION")

        device_app_info = AppiumOptions()
        device_app_info.load_capabilities(capabilities)
        self.driver = webdriver.Remote(self.config.server_url, options=device_app_info)

        # 更激进的性能优化设置
        self.driver.update_settings({
            "waitForIdleTimeout": 0,  # 空闲时间，0 表示不等待，让 UIAutomator2 不等页面“空闲”再返回
            "actionAcknowledgmentTimeout": 0,  # 禁止等待动作确认
            "keyInjectionDelay": 0,  # 禁止输入延迟
            "waitForSelectorTimeout": 300,  # 从500减少到300ms
            "ignoreUnimportantViews": False,  # 保持false避免元素丢失
            "allowInvisibleElements": True,
            "enableNotificationListener": False,  # 禁用通知监听
        })

        # 显式等待时长（可配置）
        self.wait = WebDriverWait(self.driver, self.config.default_wait_sec)

    def ultra_fast_click(self, by, value, timeout=None):
        """超快速点击 - 适合抢票场景"""
        timeout = self.config.fast_click_timeout_sec if timeout is None else timeout
        try:
            # 直接查找并点击，不等待可点击状态
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            # 使用坐标点击更快
            rect = el.rect
            x = rect['x'] + rect['width'] // 2
            y = rect['y'] + rect['height'] // 2
            self.driver.execute_script("mobile: clickGesture", {
                "x": x,
                "y": y,
                "duration": 50  # 极短点击时间
            })
            return True
        except TimeoutException:
            return False

    def batch_click(self, elements_info, delay=0.1):
        """批量点击操作"""
        for by, value in elements_info:
            if self.ultra_fast_click(by, value):
                if delay > 0:
                    time.sleep(delay)
            else:
                print(f"点击失败: {value}")

    def ultra_batch_click(self, users, timeout=None):
        """批量选择用户：仅当前页面匹配（不滚动）；返回成功选中人数"""
        timeout = self.config.user_find_timeout_sec if timeout is None else timeout
        selected = 0

        for user in users:
            el = None
            exact_selector = f'new UiSelector().text("{user}")'
            fuzzy_selector = f'new UiSelector().textContains("{user}")'

            # 1) 先尝试精确匹配
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, exact_selector))
                )
            except TimeoutException:
                # 2) 再尝试模糊匹配
                try:
                    el = WebDriverWait(self.driver, self.config.user_fuzzy_timeout_sec).until(
                        EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, fuzzy_selector))
                    )
                except TimeoutException:
                    pass

            if el is None:
                print(f"超时未找到用户: {user}")
                continue

            try:
                rect = el.rect
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 30})
                selected += 1
                print(f"点击用户: {user}")
                time.sleep(self.config.batch_click_delay_sec)
            except Exception as e:
                print(f"点击用户失败 {user}: {e}")

        print(f"成功选中 {selected}/{len(users)} 个用户")
        return selected

    def smart_wait_and_click(self, by, value, backup_selectors=None, timeout=None):
        """智能等待和点击 - 支持备用选择器"""
        timeout = self.config.smart_click_timeout_sec if timeout is None else timeout
        selectors = [(by, value)]
        if backup_selectors:
            selectors.extend(backup_selectors)

        for selector_by, selector_value in selectors:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((selector_by, selector_value))
                )
                rect = el.rect
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 50})
                return True
            except TimeoutException:
                continue
        return False

    def run_ticket_grabbing(self):
        """执行抢票主流程"""
        try:
            print("开始抢票流程...")
            start_time = time.time()

            # 1. 城市选择（可选跳过）
            if self.config.skip_city_selection:
                print("选择城市...（已配置跳过）")
            else:
                print("选择城市...")
                city_selectors = [
                    (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{self.config.city}")'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{self.config.city}")'),
                    (By.XPATH, f'//*[@text="{self.config.city}"]')
                ]
                if not self.smart_wait_and_click(*city_selectors[0], city_selectors[1:]):
                    print("城市选择失败")
                    return False

            # 2. 点击预约按钮 - 多种可能的按钮文本
            print("点击预约按钮...")
            book_selectors = [
                (By.ID, "cn.damai:id/trade_project_detail_purchase_status_bar_container_fl"),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*预约.*|.*购买.*|.*立即.*")'),
                (By.XPATH, '//*[contains(@text,"预约") or contains(@text,"购买")]')
            ]
            if not self.smart_wait_and_click(*book_selectors[0], book_selectors[1:]):
                print("预约按钮点击失败")
                return False

            # 3. 票价选择（优先直点，失败后兜底）
            print("选择票价...")
            try:
                # 极速路径：短超时等待容器，命中后按 index 直点
                price_container = WebDriverWait(self.driver, self.config.price_fast_timeout_sec).until(
                    EC.presence_of_element_located((By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout'))
                )
                target_price = price_container.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().className("android.widget.FrameLayout").index({self.config.price_index}).clickable(true)'
                )
                self.driver.execute_script('mobile: clickGesture', {'elementId': target_price.id})
            except Exception as e:
                print(f"票价直点失败，启动兜底方案: {e}")
                # 兜底路径：更长等待再重试一次
                try:
                    price_container = WebDriverWait(self.driver, self.config.price_fallback_timeout_sec).until(
                        EC.presence_of_element_located((By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout'))
                    )
                    target_price = price_container.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().className("android.widget.FrameLayout").index({self.config.price_index}).clickable(true)'
                    )
                    self.driver.execute_script('mobile: clickGesture', {'elementId': target_price.id})
                except Exception as e2:
                    print(f"票价兜底也失败: {e2}")
                    return False

            # 4. 数量选择
            print("选择数量...")
            if self.driver.find_elements(by=By.ID, value='layout_num'):
                clicks_needed = len(self.config.users) - 1
                if clicks_needed > 0:
                    try:
                        plus_button = self.driver.find_element(By.ID, 'img_jia')
                        for i in range(clicks_needed):
                            rect = plus_button.rect
                            x = rect['x'] + rect['width'] // 2
                            y = rect['y'] + rect['height'] // 2
                            self.driver.execute_script("mobile: clickGesture", {
                                "x": x,
                                "y": y,
                                "duration": 50
                            })
                            time.sleep(self.config.quantity_click_delay_sec)
                    except Exception as e:
                        print(f"快速点击加号失败: {e}")

            # if self.driver.find_elements(by=By.ID, value='layout_num') and self.config.users is not None:
            #     for i in range(len(self.config.users) - 1):
            #         self.driver.find_element(by=By.ID, value='img_jia').click()

            # 5. 确定购买
            print("确定购买...")
            if not self.ultra_fast_click(By.ID, "btn_buy_view"):
                # 备用按钮文本
                self.ultra_fast_click(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*确定.*|.*购买.*")')

            # 6. 批量选择用户
            print("选择用户...")
            selected_count = self.ultra_batch_click(self.config.users)
            expected_count = len(self.config.users)
            if selected_count != expected_count:
                print(f"用户选择校验失败：期望 {expected_count}，实际 {selected_count}，本次判定失败")
                return False

            # 7. 提交订单（可配置）
            if self.config.if_commit_order:
                print("提交订单...")
                submit_selectors = [
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("立即提交")'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*提交.*|.*确认.*")'),
                    (By.XPATH, '//*[contains(@text,"提交")]')
                ]
                self.smart_wait_and_click(*submit_selectors[0], submit_selectors[1:])
            else:
                print("if_commit_order=false，跳过提交订单")

            end_time = time.time()
            print(f"抢票流程完成，耗时: {end_time - start_time:.2f}秒")
            return True

        except Exception as e:
            print(f"抢票过程发生错误: {e}")
            return False
        finally:
            time.sleep(self.config.post_run_sleep_sec)

    def run_with_retry(self, max_retries=None):
        """带重试机制的抢票"""
        max_retries = self.config.max_retries if max_retries is None else max_retries
        try:
            for attempt in range(max_retries):
                print(f"第 {attempt + 1} 次尝试...")

                # 若 session 已失效，则先重建
                if not self.driver or not getattr(self.driver, "session_id", None):
                    self._setup_driver()

                if self.run_ticket_grabbing():
                    print("抢票成功！")
                    return True
                else:
                    print(f"第 {attempt + 1} 次尝试失败")
                    if attempt < max_retries - 1:
                        print(f"{self.config.retry_interval_sec}秒后重试...")
                        time.sleep(self.config.retry_interval_sec)
                        if self.config.reinit_driver_on_retry:
                            # 仅在配置开启时重建 driver（更稳但更慢）
                            self._safe_quit_driver()
                            self._setup_driver()

            print("所有尝试均失败")
            return False
        finally:
            self._safe_quit_driver()


# 使用示例
if __name__ == "__main__":
    bot = DamaiBot()
    bot.run_with_retry()

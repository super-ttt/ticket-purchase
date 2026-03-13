# -*- coding: UTF-8 -*-
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

    def _any_text_exists(self, patterns):
        """页面上是否存在任意匹配文案"""
        for p in patterns:
            selector = f'new UiSelector().textContains("{p}")'
            if self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector):
                return True
        return False

    def _try_click_booking_entry(self):
        """尝试点击预约/购买入口，返回状态: booked|no_start|listen|none"""
        if self._any_text_exists(["提交缺货登记"]):
            return "no_start"
        book_selectors = [
            (By.ID, "cn.damai:id/trade_project_detail_purchase_status_bar_container_fl"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*预约.*|.*购买.*|.*立即.*")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*不，立即预订.*|.*不，立即购买.*")'),
            (By.XPATH, '//*[contains(@text,"预约") or contains(@text,"购买") or contains(@text,"立即")]')
        ]
        if self.smart_wait_and_click(*book_selectors[0], book_selectors[1:], timeout=0.25):
            return "booked"
        return "none"

    def _poll_until_booking_clickable(self):
        """短轮询：等待抢票开始并点击入口"""
        poll_timeout_sec = getattr(self.config, "book_poll_timeout_sec", 8)
        poll_interval_sec = getattr(self.config, "book_poll_interval_sec", 0.05)
        deadline = time.time() + max(1, poll_timeout_sec)

        while time.time() < deadline:
            state = self._try_click_booking_entry()
            if state == "booked":
                return True
            if state == "listen":
                return True
            if state == "no_start":
                print("当前为提交缺货登记状态，等待开售...")
            time.sleep(max(0.05, poll_interval_sec))
            try:
                self.driver.refresh()
            except Exception:
                pass

        return False

    def _select_date_if_needed(self):
        """可选场次选择（兼容 date 为字符串或列表）"""
        date_conf = getattr(self.config, "date", None)
        if not date_conf:
            return True

        date_list = date_conf if isinstance(date_conf, list) else [str(date_conf)]
        for d in date_list:
            selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{d}")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{d}")'),
                (By.XPATH, f'//*[contains(@text,"{d}")]')
            ]
            if self.smart_wait_and_click(*selectors[0], selectors[1:], timeout=0.3):
                print(f"场次选择成功: {d}")
                return True
        print(f"未匹配到场次: {date_list}")
        return False

    def _handle_order_submit_modal(self):
        """处理「同一时间下单人数过多」弹窗：优先点击「继续尝试」，否则点击「返回重新选购」

        Returns:
            "retry": 已点击「继续尝试」，可重试提交
            "back": 已点击「返回重新选购」，本轮失败
            None: 未检测到弹窗
        """
        try:
            # 优先查找「继续尝试」
            for by, val in [
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("继续尝试")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("继续尝试")'),
                (By.XPATH, '//*[contains(@text,"继续尝试")]'),
            ]:
                els = self.driver.find_elements(by, val)
                if els:
                    try:
                        el = els[0]
                        rect = el.rect
                        x = rect["x"] + rect["width"] // 2
                        y = rect["y"] + rect["height"] // 2
                        self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 50})
                        print("已点击「继续尝试」，重试提交")
                        return "retry"
                    except Exception:
                        continue

            # 无「继续尝试」时查找「返回重新选购」
            for by, val in [
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("返回重新选购")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("返回重新选购")'),
                (By.XPATH, '//*[contains(@text,"返回重新选购")]'),
            ]:
                els = self.driver.find_elements(by, val)
                if els:
                    try:
                        el = els[0]
                        rect = el.rect
                        x = rect["x"] + rect["width"] // 2
                        y = rect["y"] + rect["height"] // 2
                        self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 50})
                        print("已点击「返回重新选购」")
                        return "back"
                    except Exception:
                        continue
        except Exception:
            pass
        return None

    def _submit_order_with_fallback(self):
        """提交订单，多选择器兜底；遇「同一时间下单人数过多」弹窗时自动处理"""
        submit_selectors = [
            (By.ID, "btn_submit"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("立即提交")'),
            (AppiumBy.ANDROID_UIAUTOMATOR,
             'new UiSelector().textMatches(".*提交订单.*|.*立即提交.*|.*提交.*|.*确认.*|.*去支付.*|.*支付.*")'),
            (By.XPATH, '//*[contains(@text,"提交") or contains(@text,"确认") or contains(@text,"支付")]')
        ]

        wait_sec = getattr(self.config, "order_modal_retry_wait_sec", 0.1)
        modal_retry_max = getattr(self.config, "order_modal_retry_max", 10)
        for _ in range(modal_retry_max):
            # 1. 先检测弹窗
            modal_result = self._handle_order_submit_modal()
            if modal_result == "back":
                return False
            if modal_result == "retry":
                time.sleep(wait_sec)
                # 弹窗已关闭，立即尝试提交订单
                if self.smart_wait_and_click(*submit_selectors[0], submit_selectors[1:], timeout=0.35):
                    time.sleep(0.15)
                    modal_result = self._handle_order_submit_modal()
                    if modal_result == "back":
                        return False
                    if modal_result == "retry":
                        time.sleep(wait_sec)
                        continue
                    return True
                continue

            # 2. 无弹窗，尝试点击提交
            if self.smart_wait_and_click(*submit_selectors[0], submit_selectors[1:], timeout=0.35):
                time.sleep(0.15)
                # 提交后可能弹出「人数过多」，再检测一次
                modal_result = self._handle_order_submit_modal()
                if modal_result == "back":
                    return False
                if modal_result == "retry":
                    time.sleep(wait_sec)
                    continue
                return True

            # 3. 提交按钮未命中，可能被弹窗遮挡，检测弹窗
            modal_result = self._handle_order_submit_modal()
            if modal_result == "back":
                return False
            if modal_result == "retry":
                time.sleep(wait_sec)
                # 弹窗已关闭，立即尝试提交订单
                if self.smart_wait_and_click(*submit_selectors[0], submit_selectors[1:], timeout=0.35):
                    time.sleep(0.15)
                    modal_result = self._handle_order_submit_modal()
                    if modal_result == "back":
                        return False
                    if modal_result == "retry":
                        time.sleep(wait_sec)
                        continue
                    return True
                continue

            # 额外 JS 兜底
            try:
                clicked = self.driver.execute_script(
                    """
                    const keys=['立即提交','提交订单','提交','确认','去支付','支付'];
                    const nodes=[...document.querySelectorAll('*')];
                    for (const n of nodes){
                        const t=(n.innerText||n.textContent||'').trim();
                        if (!t) continue;
                        if (keys.some(k=>t.includes(k))){ n.click(); return true; }
                    }
                    return false;
                    """
                )
                if clicked:
                    time.sleep(0.15)
                    modal_result = self._handle_order_submit_modal()
                    if modal_result == "back":
                        return False
                    if modal_result == "retry":
                        time.sleep(wait_sec)
                        continue
                    return True
            except Exception:
                pass
            break
        return False

    def _find_price_container(self):
        """查找票价容器（支持详情页、确认页等多种布局）。"""
        container_ids = [
            'cn.damai:id/project_detail_perform_price_flowlayout',
            'cn.damai:id/perform_price_flowlayout',
            'cn.damai:id/price_flowlayout',
            # 确认页/订单页可能使用的容器
            'cn.damai:id/project_detail_perform_flowlayout',
            'cn.damai:id/perform_flowlayout',
            'cn.damai:id/ll_price_container',
            'cn.damai:id/rl_price',
            'cn.damai:id/price_container',
        ]
        for cid in container_ids:
            try:
                els = self.driver.find_elements(By.ID, cid)
                if els:
                    return els[0]
            except Exception:
                continue
        return None

    def _get_element_full_text(self, el):
        """获取元素及其后代的 text + content-desc 拼接，用于判断缺货等标签"""
        parts = []
        try:
            parts.append(el.text or "")
            parts.append(el.get_attribute("content-desc") or "")
            for child in el.find_elements(By.XPATH, ".//*"):
                try:
                    parts.append(child.text or "")
                    parts.append(child.get_attribute("content-desc") or "")
                except Exception:
                    pass
        except Exception:
            pass
        return " ".join(p for p in parts if p)

    def _get_price_option_elements(self):
        """获取票价选项元素列表（可点击的每行）。"""
        container = self._find_price_container()
        if not container:
            return []
        element_list = []
        try:
            frames = container.find_elements(By.XPATH, ".//*[@clickable='true']")
            for f in frames:
                try:
                    if f.size.get("width", 0) > 30 and f.size.get("height", 0) > 20:
                        element_list.append(f)
                except Exception:
                    pass
        except Exception:
            pass
        if not element_list:
            rows = container.find_elements(By.XPATH, ".//*[@resource-id='cn.damai:id/ll_perform_item']")
            for row in rows:
                try:
                    target = row
                    for xp in ["./ancestor::*[@clickable='true'][1]", "./preceding-sibling::*[@clickable='true'][1]",
                               "./.."]:
                        try:
                            t = row.find_element(By.XPATH, xp)
                            if t and (t.get_attribute("clickable") == "true" or (t.size.get("width", 0) or 0) > 20):
                                target = t
                                break
                        except Exception:
                            pass
                    element_list.append(target)
                except Exception:
                    pass
        return element_list

    def _select_price_by_indices(self):
        """按索引数组选择票价：依次尝试配置的索引，命中即返回。"""
        indices = getattr(self.config, "price_indices", None)
        if not indices:
            return False
        if isinstance(indices, int):
            indices = [indices]
        indices = [int(i) for i in indices if isinstance(i, (int, float, str)) and str(i).strip() != ""]

        wait_sec = getattr(self.config, "price_candidate_wait_sec", 5)
        deadline = time.time() + wait_sec

        print("等待票价容器")
        while time.time() < deadline:
            if self._find_price_container() is not None:
                break
            if self.driver.find_elements(By.XPATH, '//*[contains(@text,"元") or contains(@content-desc,"元")]'):
                break
            time.sleep(0.03)

        print("获取票价页面")
        if not self._find_price_container():
            print("票价页面未就绪")
            return False

        print("票价页面已就绪")
        element_list = self._get_price_option_elements()
        if not element_list:
            print("未找到票价选项")
            return False

        print("票价选项已就绪")
        soldout_keywords = ("缺货登记", "缺货", "售罄", "无票", "不可选")
        fail_reasons = []
        for idx in indices:
            if idx < 0 or idx >= len(element_list):
                fail_reasons.append(f"索引{idx}: 越界（共{len(element_list)}个选项）")
                continue
            try:
                el = element_list[idx]
                full_txt = self._get_element_full_text(el)
                hit_soldout = [kw for kw in soldout_keywords if kw in full_txt]
                if hit_soldout:
                    fail_reasons.append(f"索引{idx}: 缺货/售罄（{', '.join(hit_soldout)}）")
                    continue
                rect = el.rect
                x = rect["x"] + rect["width"] // 2
                y = rect["y"] + rect["height"] // 2
                self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 25})
                print(f"票价选择成功（索引 {idx}）")
                return True
            except Exception as e:
                fail_reasons.append(f"索引{idx}: 点击失败（{type(e).__name__}）")
                continue
        print(f"所有票价索引均不可用: {'; '.join(fail_reasons)}")
        return False

    def _go_back_after_price_miss(self):
        """票价候选全部未命中时，返回上一页，交给外层重试"""
        try:
            self.driver.back()
            time.sleep(0.12)
            # 某些机型 back 可能没生效，补一次软返回
            if self._any_text_exists(["票价", "价格", "场次"]):
                self.driver.execute_script("mobile: pressKey", {"keycode": 4})
                time.sleep(0.1)
            print("票价未命中：已返回上一页")
        except Exception as e:
            print(f"票价未命中：返回上一页失败: {e}")

    def run_ticket_grabbing(self):
        """执行抢票主流程"""
        try:
            print("开始抢票流程...")
            start_time = time.time()

            # 1. 场次选择（可选）
            print("选择场次...")
            if not self._select_date_if_needed():
                print("场次选择失败")
                return False

            # 2. 点击预约按钮（含开售轮询/缺货登记分支）
            print("等待并点击预约/购买入口...")
            if not self._poll_until_booking_clickable():
                print("预约按钮点击失败（轮询超时）")
                return False

            # 3. 票价选择（按索引）
            print("选择票价...")
            if not self._select_price_by_indices():
                print("票价索引未命中，本轮失败")
                self._go_back_after_price_miss()
                return False

            # 4. 确定购买
            print("确定购买...")
            if not self.ultra_fast_click(By.ID, "btn_buy_view"):
                if not self.ultra_fast_click(AppiumBy.ANDROID_UIAUTOMATOR,
                                             'new UiSelector().textMatches(".*确定.*|.*购买.*")'):
                    print("确定购买按钮未命中，本轮失败")
                    return False
            time.sleep(0.15)

            # 5. 提交订单（可配置）
            if self.config.if_commit_order:
                print("提交订单...")
                if not self._submit_order_with_fallback():
                    print("提交按钮未命中，请手动确认")
                    return False
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

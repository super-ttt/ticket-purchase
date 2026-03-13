# -*- coding: UTF-8 -*-
"""工具方法：点击、查找、文案检测"""
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def click_element_center(driver, el, duration_ms):
    """点击元素中心，使用 mobile: clickGesture"""
    rect = el.rect
    x = rect["x"] + rect["width"] // 2
    y = rect["y"] + rect["height"] // 2
    driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": duration_ms})


def ultra_fast_click(driver, config, by, value, timeout=None):
    """超快速点击"""
    timeout = config.fast_click_timeout_sec if timeout is None else timeout
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        click_element_center(driver, el, config.click_gesture_duration_ms)
        return True
    except TimeoutException:
        return False


def smart_wait_and_click(driver, config, by, value, backup_selectors=None, timeout=None):
    """智能等待和点击 - 支持备用选择器"""
    timeout = config.smart_click_timeout_sec if timeout is None else timeout
    selectors = [(by, value)]
    if backup_selectors:
        selectors.extend(backup_selectors)

    for selector_by, selector_value in selectors:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((selector_by, selector_value))
            )
            click_element_center(driver, el, config.click_gesture_duration_ms)
            return True
        except TimeoutException:
            continue
    return False


def any_text_exists(driver, patterns):
    """页面上是否存在任意匹配文案"""
    for p in patterns:
        selector = f'new UiSelector().textContains("{p}")'
        if driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector):
            return True
    return False


def find_price_container(driver):
    """查找票价容器"""
    container_ids = [
        'cn.damai:id/project_detail_perform_price_flowlayout',
        'cn.damai:id/perform_price_flowlayout',
        'cn.damai:id/price_flowlayout',
        'cn.damai:id/project_detail_perform_flowlayout',
        'cn.damai:id/perform_flowlayout',
        'cn.damai:id/ll_price_container',
        'cn.damai:id/rl_price',
        'cn.damai:id/price_container',
    ]
    for cid in container_ids:
        try:
            els = driver.find_elements(By.ID, cid)
            if els:
                return els[0]
        except Exception:
            continue
    return None


def get_element_full_text(el, soldout_keywords=("缺货登记", "缺货", "售罄", "无票", "不可选")):
    """获取元素及其后代的 text + content-desc 拼接，优先快速路径"""
    try:
        t = (el.text or "").strip()
        d = (el.get_attribute("content-desc") or "").strip()
        top = f"{t} {d}".strip()
        if top and any(kw in top for kw in soldout_keywords):
            return top
        parts = [t, d]
        for child in el.find_elements(By.XPATH, ".//*"):
            try:
                parts.append(child.text or "")
                parts.append(child.get_attribute("content-desc") or "")
            except Exception:
                pass
        return " ".join(p for p in parts if p)
    except Exception:
        return ""


def get_price_option_elements(driver, container=None):
    """获取票价选项元素列表（可点击的每行），container 可选以复用已查到的容器"""
    if container is None:
        container = find_price_container(driver)
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
                for xp in ["./ancestor::*[@clickable='true'][1]", "./preceding-sibling::*[@clickable='true'][1]", "./.."]:
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

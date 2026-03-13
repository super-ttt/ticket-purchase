# -*- coding: UTF-8 -*-
"""流程方法：场次、预约、票价、提交订单"""
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By

from damai_app_utils import (
    any_text_exists,
    find_price_container,
    get_element_full_text,
    get_price_option_elements,
    smart_wait_and_click,
)


def try_click_booking_entry(driver, config):
    """尝试点击预约/购买入口，返回: booked|no_start|none"""
    if any_text_exists(driver, ["提交缺货登记"]):
        return "no_start"
    book_selectors = [
        (By.ID, "cn.damai:id/trade_project_detail_purchase_status_bar_container_fl"),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*预约.*|.*购买.*|.*立即.*")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*不，立即预订.*|.*不，立即购买.*")'),
        (By.XPATH, '//*[contains(@text,"预约") or contains(@text,"购买") or contains(@text,"立即")]')
    ]
    if smart_wait_and_click(driver, config, *book_selectors[0], book_selectors[1:], timeout=0.25):
        return "booked"
    return "none"


def poll_until_booking_clickable(driver, config):
    """短轮询：等待抢票开始并点击入口"""
    poll_timeout_sec = getattr(config, "book_poll_timeout_sec", 8)
    poll_interval_sec = getattr(config, "book_poll_interval_sec", 0.05)
    deadline = time.time() + max(1, poll_timeout_sec)

    while time.time() < deadline:
        state = try_click_booking_entry(driver, config)
        if state == "booked":
            return True
        if state == "listen":
            return True
        if state == "no_start":
            print("当前为提交缺货登记状态，等待开售...")
        time.sleep(max(0.05, poll_interval_sec))
        try:
            driver.refresh()
        except Exception:
            pass
    return False


def select_date_if_needed(driver, config):
    """可选场次选择"""
    date_conf = getattr(config, "date", None)
    if not date_conf:
        return True

    date_list = date_conf if isinstance(date_conf, list) else [str(date_conf)]
    for d in date_list:
        selectors = [
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{d}")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{d}")'),
            (By.XPATH, f'//*[contains(@text,"{d}")]')
        ]
        if smart_wait_and_click(driver, config, *selectors[0], selectors[1:], timeout=0.3):
            print(f"场次选择成功: {d}")
            return True
    print(f"未匹配到场次: {date_list}")
    return False


def select_price_by_indices(driver, config):
    """按索引数组选择票价"""
    t0 = time.time()

    indices = getattr(config, "price_indices", None)
    if not indices:
        print(f"[票价] 参数解析: 无 price_indices 配置，耗时 {time.time() - t0:.3f}s")
        return False
    if isinstance(indices, int):
        indices = [indices]
    indices = [int(i) for i in indices if isinstance(i, (int, float, str)) and str(i).strip() != ""]
    print(f"[票价] 参数解析: indices={indices}，耗时 {time.time() - t0:.3f}s")

    t1 = time.time()
    wait_sec = getattr(config, "price_candidate_wait_sec", 5)
    deadline = time.time() + wait_sec

    while time.time() < deadline:
        if find_price_container(driver) is not None:
            break
        if driver.find_elements(By.XPATH, '//*[contains(@text,"元") or contains(@content-desc,"元")]'):
            break
        time.sleep(0.03)

    elapsed_wait = time.time() - t1
    print(f"[票价] 等待票价容器就绪: 耗时 {elapsed_wait:.3f}s")

    t2 = time.time()
    if not find_price_container(driver):
        print(f"[票价] 查找票价容器: 未就绪，耗时 {time.time() - t2:.3f}s")
        return False
    print(f"[票价] 查找票价容器: 成功，耗时 {time.time() - t2:.3f}s")

    t3 = time.time()
    element_list = get_price_option_elements(driver)
    print(f"[票价] 获取票价选项: 共 {len(element_list)} 个，耗时 {time.time() - t3:.3f}s")
    if not element_list:
        return False

    soldout_keywords = ("缺货登记", "缺货", "售罄", "无票", "不可选")
    fail_reasons = []
    t4 = time.time()
    for idx in indices:
        ti = time.time()
        if idx < 0 or idx >= len(element_list):
            fail_reasons.append(f"索引{idx}: 越界（共{len(element_list)}个选项）")
            continue
        try:
            el = element_list[idx]
            full_txt = get_element_full_text(el)
            hit_soldout = [kw for kw in soldout_keywords if kw in full_txt]
            if hit_soldout:
                fail_reasons.append(f"索引{idx}: 缺货/售罄（{', '.join(hit_soldout)}）")
                continue
            rect = el.rect
            x = rect["x"] + rect["width"] // 2
            y = rect["y"] + rect["height"] // 2
            driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 25})
            print(f"[票价] 索引{idx} 点击成功: 本索引耗时 {time.time() - ti:.3f}s，总耗时 {time.time() - t0:.3f}s")
            return True
        except Exception as e:
            fail_reasons.append(f"索引{idx}: 点击失败（{type(e).__name__}）")
            continue
    print(f"[票价] 遍历索引: 耗时 {time.time() - t4:.3f}s，所有索引均不可用: {'; '.join(fail_reasons)}")
    return False


def go_back_after_price_miss(driver, config):
    """票价未命中时返回上一页"""
    try:
        driver.back()
        time.sleep(0.12)
        if any_text_exists(driver, ["票价", "价格", "场次"]):
            driver.execute_script("mobile: pressKey", {"keycode": 4})
            time.sleep(0.1)
        print("票价未命中：已返回上一页")
    except Exception as e:
        print(f"票价未命中：返回上一页失败: {e}")


def handle_order_submit_modal(driver):
    """处理「同一时间下单人数过多」弹窗，返回: retry|back|None"""
    try:
        for by, val in [
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("继续尝试")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("继续尝试")'),
            (By.XPATH, '//*[contains(@text,"继续尝试")]'),
        ]:
            els = driver.find_elements(by, val)
            if els:
                try:
                    el = els[0]
                    rect = el.rect
                    x = rect["x"] + rect["width"] // 2
                    y = rect["y"] + rect["height"] // 2
                    driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 50})
                    print("已点击「继续尝试」，重试提交")
                    return "retry"
                except Exception:
                    continue

        for by, val in [
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("返回重新选购")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("返回重新选购")'),
            (By.XPATH, '//*[contains(@text,"返回重新选购")]'),
        ]:
            els = driver.find_elements(by, val)
            if els:
                try:
                    el = els[0]
                    rect = el.rect
                    x = rect["x"] + rect["width"] // 2
                    y = rect["y"] + rect["height"] // 2
                    driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 50})
                    print("已点击「返回重新选购」")
                    return "back"
                except Exception:
                    continue
    except Exception:
        pass
    return None


def submit_order_with_fallback(driver, config):
    """提交订单，遇「人数过多」弹窗时自动处理"""
    submit_selectors = [
        (By.ID, "btn_submit"),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("立即提交")'),
        (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().textMatches(".*提交订单.*|.*立即提交.*|.*提交.*|.*确认.*|.*去支付.*|.*支付.*")'),
        (By.XPATH, '//*[contains(@text,"提交") or contains(@text,"确认") or contains(@text,"支付")]')
    ]

    wait_sec = getattr(config, "order_modal_retry_wait_sec", 0.1)
    modal_retry_max = getattr(config, "order_modal_retry_max", 10)

    for _ in range(modal_retry_max):
        modal_result = handle_order_submit_modal(driver)
        if modal_result == "back":
            return False
        if modal_result == "retry":
            time.sleep(wait_sec)
            if smart_wait_and_click(driver, config, *submit_selectors[0], submit_selectors[1:], timeout=0.35):
                time.sleep(0.15)
                modal_result = handle_order_submit_modal(driver)
                if modal_result == "back":
                    return False
                if modal_result == "retry":
                    time.sleep(wait_sec)
                    continue
                return True
            continue

        if smart_wait_and_click(driver, config, *submit_selectors[0], submit_selectors[1:], timeout=0.35):
            time.sleep(0.15)
            modal_result = handle_order_submit_modal(driver)
            if modal_result == "back":
                return False
            if modal_result == "retry":
                time.sleep(wait_sec)
                continue
            return True

        modal_result = handle_order_submit_modal(driver)
        if modal_result == "back":
            return False
        if modal_result == "retry":
            time.sleep(wait_sec)
            if smart_wait_and_click(driver, config, *submit_selectors[0], submit_selectors[1:], timeout=0.35):
                time.sleep(0.15)
                modal_result = handle_order_submit_modal(driver)
                if modal_result == "back":
                    return False
                if modal_result == "retry":
                    time.sleep(wait_sec)
                    continue
                return True
            continue

        try:
            clicked = driver.execute_script(
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
                modal_result = handle_order_submit_modal(driver)
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

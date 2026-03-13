# -*- coding: UTF-8 -*-
"""流程方法：场次、预约、票价、提交订单"""
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By

from damai_app_utils import (
    any_text_exists,
    click_element_center,
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
    if smart_wait_and_click(driver, config, *book_selectors[0], book_selectors[1:], timeout=config.book_entry_timeout_sec):
        return "booked"
    return "none"


def poll_until_booking_clickable(driver, config):
    """短轮询：等待抢票开始并点击入口"""
    poll_timeout_sec = config.book_poll_timeout_sec
    poll_interval_sec = config.book_poll_interval_sec
    deadline = time.time() + poll_timeout_sec

    while time.time() < deadline:
        state = try_click_booking_entry(driver, config)
        if state == "booked":
            return True
        if state == "listen":
            return True
        if state == "no_start":
            print("当前为提交缺货登记状态，等待开售...")
        time.sleep(poll_interval_sec)
        try:
            driver.refresh()
        except Exception:
            pass
    return False


def select_date_if_needed(driver, config):
    """可选场次选择"""
    t0 = time.time()
    date_conf = config.date
    if not date_conf:
        print(f"[场次] 跳过（无 date 配置），耗时 {time.time() - t0:.3f}s")
        return True

    date_list = date_conf if isinstance(date_conf, list) else [str(date_conf)]
    print(f"[场次] 参数解析: date_list={date_list}，耗时 {time.time() - t0:.3f}s")

    for d in date_list:
        ti = time.time()
        selectors = [
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{d}")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{d}")'),
            (By.XPATH, f'//*[contains(@text,"{d}")]')
        ]
        if smart_wait_and_click(driver, config, *selectors[0], selectors[1:], timeout=config.date_select_timeout_sec):
            print(f"[场次] 选择成功: {d}，耗时 {time.time() - ti:.3f}s，总耗时 {time.time() - t0:.3f}s")
            return True
    print(f"[场次] 未匹配到场次: {date_list}，总耗时 {time.time() - t0:.3f}s")
    return False


def select_price_by_indices(driver, config):
    """按索引数组选择票价"""
    t0 = time.time()

    indices = config.price_indices
    if not indices:
        print(f"[票价] 参数解析: 无 price_indices 配置，耗时 {time.time() - t0:.3f}s")
        return False
    if isinstance(indices, int):
        indices = [indices]
    indices = [int(i) for i in indices if isinstance(i, (int, float, str)) and str(i).strip() != ""]
    print(f"[票价] 参数解析: indices={indices}，耗时 {time.time() - t0:.3f}s")

    t1 = time.time()
    wait_sec = config.price_candidate_wait_sec
    deadline = time.time() + wait_sec
    container = None

    while time.time() < deadline:
        container = find_price_container(driver)
        if container is not None:
            break
        time.sleep(config.price_container_poll_interval_sec)

    elapsed = time.time() - t1
    if not container:
        print(f"[票价] 等待票价容器就绪: 未就绪，耗时 {elapsed:.3f}s")
        return False
    print(f"[票价] 等待票价容器就绪: 耗时 {elapsed:.3f}s")

    t3 = time.time()
    element_list = get_price_option_elements(driver, container)
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
            click_element_center(driver, el, config.price_click_duration_ms)
            print(f"[票价] 索引{idx} 点击成功: 本索引耗时 {time.time() - ti:.3f}s，总耗时 {time.time() - t0:.3f}s")
            return True
        except Exception as e:
            fail_reasons.append(f"索引{idx}: 点击失败（{type(e).__name__}）")
            continue
    print(f"[票价] 遍历索引: 耗时 {time.time() - t4:.3f}s，所有索引均不可用: {'; '.join(fail_reasons)}")
    return False


def select_price_with_soldout_poll(driver, config):
    """选择票价，缺货时原地刷新轮询，超时后返回 False 由调用方执行 go_back"""
    poll_max = config.price_soldout_poll_max
    poll_interval = config.price_soldout_poll_interval_sec

    for attempt in range(poll_max):
        if select_price_by_indices(driver, config):
            return True
        if attempt < poll_max - 1:
            print(f"[票价] 票价未命中，原地刷新重试 ({attempt + 1}/{poll_max})...")
            try:
                driver.refresh()
            except Exception:
                pass
            time.sleep(poll_interval)
    return False


def go_back_after_price_miss(driver, config):
    """票价未命中时返回上一页"""
    try:
        driver.back()
        time.sleep(config.go_back_wait_sec)
        if any_text_exists(driver, ["票价", "价格", "场次"]):
            driver.execute_script("mobile: pressKey", {"keycode": 4})
            time.sleep(config.go_back_key_wait_sec)
        print("票价未命中：已返回上一页")
    except Exception as e:
        print(f"票价未命中：返回上一页失败: {e}")


def _click_modal_button(driver, config, selectors, label):
    """尝试点击弹窗按钮，找到并点击返回 True"""
    for by, val in selectors:
        els = driver.find_elements(by, val)
        if els:
            try:
                click_element_center(driver, els[0], config.click_gesture_duration_ms)
                print(f"已点击「{label}」")
                return True
            except Exception:
                continue
    return False


def handle_order_submit_modal(driver, config):
    """处理「同一时间下单人数过多」弹窗，返回: retry|back|None"""
    try:
        retry_selectors = [
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("继续尝试")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("继续尝试")'),
            (By.XPATH, '//*[contains(@text,"继续尝试")]'),
        ]
        if _click_modal_button(driver, config, retry_selectors, "继续尝试"):
            return "retry"

        back_selectors = [
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("返回重新选购")'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("返回重新选购")'),
            (By.XPATH, '//*[contains(@text,"返回重新选购")]'),
        ]
        if _click_modal_button(driver, config, back_selectors, "返回重新选购"):
            return "back"
    except Exception:
        pass
    return None


def _try_submit_and_check_modal(driver, config, submit_selectors, wait_sec):
    """尝试点击提交按钮，成功后检查弹窗。返回 True/False/'retry'/None"""
    if not smart_wait_and_click(driver, config, *submit_selectors[0], submit_selectors[1:], timeout=config.order_submit_timeout_sec):
        return None
    time.sleep(config.order_submit_click_wait_sec)
    modal = handle_order_submit_modal(driver, config)
    if modal == "back":
        return False
    if modal == "retry":
        time.sleep(wait_sec)
        return "retry"
    return True


def submit_order_with_fallback(driver, config):
    """提交订单，遇「人数过多」弹窗时自动处理"""
    submit_selectors = [
        (By.ID, "btn_submit"),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("立即提交")'),
        (AppiumBy.ANDROID_UIAUTOMATOR,
         'new UiSelector().textMatches(".*提交订单.*|.*立即提交.*|.*提交.*|.*确认.*|.*去支付.*|.*支付.*")'),
        (By.XPATH, '//*[contains(@text,"提交") or contains(@text,"确认") or contains(@text,"支付")]')
    ]

    wait_sec = config.order_modal_retry_wait_sec
    modal_retry_max = config.order_modal_retry_max

    for _ in range(modal_retry_max):
        modal = handle_order_submit_modal(driver, config)
        if modal == "back":
            return False
        if modal == "retry":
            time.sleep(wait_sec)

        result = _try_submit_and_check_modal(driver, config, submit_selectors, wait_sec)
        if result is True:
            return True
        if result is False:
            return False
        if result == "retry":
            continue

        try:
            clicked = driver.execute_script(
                "const k=['立即提交','提交订单','提交','确认','去支付','支付'];"
                "for(const n of document.querySelectorAll('*')){"
                "const t=(n.innerText||n.textContent||'').trim();"
                "if(t&&k.some(x=>t.includes(x))){n.click();return true;}"
                "}return false;"
            )
            if clicked:
                time.sleep(config.order_submit_click_wait_sec)
                modal = handle_order_submit_modal(driver, config)
                if modal == "back":
                    return False
                if modal == "retry":
                    time.sleep(wait_sec)
                    continue
                return True
        except Exception:
            pass
        break
    return False

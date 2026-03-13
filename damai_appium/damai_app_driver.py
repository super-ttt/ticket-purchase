# -*- coding: UTF-8 -*-
"""驱动初始化与生命周期"""
import os
from appium import webdriver
from appium.options.common.base import AppiumOptions
from selenium.webdriver.support.ui import WebDriverWait


def setup_driver(config):
    """初始化 Appium 驱动"""
    capabilities = {
        "platformName": "Android",
        "deviceName": "Android",
        "appPackage": "cn.damai",
        "appActivity": ".launcher.splash.SplashMainActivity",
        "unicodeKeyboard": True,
        "resetKeyboard": True,
        "noReset": True,
        "newCommandTimeout": 6000,
        "automationName": "UiAutomator2",
        "skipServerInstallation": False,
        "ignoreHiddenApiPolicyError": True,
        "disableWindowAnimation": True,
        "mjpegServerFramerate": 1,
        "shouldTerminateApp": False,
        "adbExecTimeout": 20000,
    }
    if os.getenv("ANDROID_UDID"):
        capabilities["udid"] = os.getenv("ANDROID_UDID")
        capabilities["deviceName"] = os.getenv("ANDROID_UDID")
    if os.getenv("ANDROID_PLATFORM_VERSION"):
        capabilities["platformVersion"] = os.getenv("ANDROID_PLATFORM_VERSION")

    device_app_info = AppiumOptions()
    device_app_info.load_capabilities(capabilities)
    driver = webdriver.Remote(config.server_url, options=device_app_info)

    driver.update_settings({
        "waitForIdleTimeout": 0,
        "actionAcknowledgmentTimeout": 0,
        "keyInjectionDelay": 0,
        "waitForSelectorTimeout": 300,
        "ignoreUnimportantViews": False,
        "allowInvisibleElements": True,
        "enableNotificationListener": False,
    })

    wait = WebDriverWait(driver, config.default_wait_sec)
    return driver, wait


def safe_quit_driver(driver):
    """安全关闭 driver"""
    if not driver:
        return
    try:
        driver.quit()
    except Exception:
        pass

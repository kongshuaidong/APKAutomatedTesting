# ============================================================
# 【飞书 APK】helpers.py
# 本 APK 专用辅助：解锁屏幕、处理地理位置授权弹窗。
# ============================================================

import time
from typing import Tuple

import uiautomator2 as u2

from tasks.apk.lark import config as cfg
from utils.logger import logger


def _screen_size(d: u2.Device) -> Tuple[int, int]:
    w, h = d.window_size()
    return int(w), int(h)


def unlock_screen(d: u2.Device) -> None:
    """亮屏 + 全屏上滑解锁（无密码机型）。"""
    d.screen_on()
    time.sleep(1)
    w, h = _screen_size(d)
    d.swipe(w // 2, int(h * 0.98), w // 2, int(h * 0.02), duration=0.3)
    time.sleep(1.5)


def dismiss_location_permission(
    d: u2.Device, timeout: float = None
) -> bool:
    """
    在 timeout 秒内轮询是否出现地理位置授权弹窗，若出现则点击「确定」允许。
    先检测「地理位置授权」标题，避免误点页面其他位置的「确定」按钮。
    返回 True 表示已点击，False 表示未出现 / 未命中（正常）。
    """
    if timeout is None:
        timeout = cfg.LOCATION_POPUP_TIMEOUT_SEC
    deadline = time.time() + timeout

    while time.time() < deadline:
        title_visible = any(
            d(**loc).exists for loc in cfg.LOCATION_PERMISSION_TITLE_LOCATORS
        )
        if title_visible:
            for locator in cfg.LOCATION_CONFIRM_LOCATORS:
                el = d(**locator)
                if el.exists:
                    try:
                        el.click()
                        logger.info(f"地理位置授权弹窗已确认，点击 {locator}")
                        time.sleep(0.8)
                        return True
                    except Exception as exc:
                        logger.warning(f"点击确定失败：{exc}")
                        return False
        time.sleep(0.3)
    return False

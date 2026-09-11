# ============================================================
# 【AI 桌面 APK】helpers.py
# 本 APK 专用辅助：进入 AI 桌面、新建会话、发送查询、等待关键词。
# 供本目录下多个用例共用，避免重复解锁+找入口+发送+等待的样板代码。
# ============================================================

import time
from typing import List, Tuple

import uiautomator2 as u2

from tasks.apk.ailauncher import config as cfg
from tasks.framework.helpers import (
    click_first_match,
    click_first_match_or_coord,
    dismiss_common_dialogs,
)
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


def enter_ai_launcher(d: u2.Device, timeout: float = 10) -> bool:
    """
    从任意状态进入 AI 桌面：亮屏 → 上滑解锁 → 回主桌面 → 点击「Agent空间」→
    等待前台包名含 'launcher'。
    返回 True 表示已进入 AI 桌面。
    """
    unlock_screen(d)
    d.press("home")
    time.sleep(1)
    dismiss_common_dialogs(d)

    if not click_first_match(d, cfg.ENTRY_LOCATORS, timeout=5):
        logger.warning("主桌面未找到「Agent空间」入口")
        return False

    deadline = time.time() + timeout
    while time.time() < deadline:
        pkg = (d.app_current() or {}).get("package", "")
        if "launcher" in pkg:
            return True
        time.sleep(0.5)
    return False


def new_conversation(d: u2.Device) -> None:
    """
    点击右上角「+」新建会话。找不到语义按钮就用坐标兜底。
    确保后续 send_query 输入的是一条全新的对话，不带上下文。
    """
    w, h = _screen_size(d)
    rx, ry = cfg.NEW_CHAT_COORD_RATIO
    click_first_match_or_coord(
        d,
        cfg.NEW_CHAT_LOCATORS,
        coord=(int(w * rx), int(h * ry)),
        warn_message="新建会话「+」按钮语义定位失败，使用坐标兜底",
        timeout=2,
    )
    time.sleep(1.2)


def send_query(d: u2.Device, query: str) -> None:
    """
    在 AI 桌面输入 query 并点击发送按钮（上箭头图标）。
    定位失败会 raise AssertionError；发送按钮语义找不到则用坐标兜底。
    """
    if not click_first_match(d, cfg.INPUT_LOCATORS, timeout=8):
        raise AssertionError("AI 桌面未找到可点击的输入框")
    time.sleep(0.5)
    d.send_keys(query, clear=True)
    time.sleep(1)

    w, h = _screen_size(d)
    rx, ry = cfg.SEND_COORD_RATIO
    click_first_match_or_coord(
        d,
        cfg.SEND_LOCATORS,
        coord=(int(w * rx), int(h * ry)),
        warn_message="发送按钮语义定位失败，使用坐标兜底",
        timeout=3,
    )
    logger.info(f"已发送查询：{query}")


def wait_for_keywords(
    d: u2.Device, keywords: List[str], timeout: int
) -> List[str]:
    """
    轮询页面 dump_hierarchy，直到出现任一 keyword 或超时。
    返回命中的关键词列表（空 = 超时未命中）。
    """
    deadline = time.time() + timeout
    matched: List[str] = []
    while time.time() < deadline:
        hierarchy = d.dump_hierarchy()
        matched = [kw for kw in keywords if kw in hierarchy]
        if matched:
            return matched
        time.sleep(1)
    return matched


def dismiss_permission_popup(
    d: u2.Device, timeout: float = None
) -> bool:
    """
    在 timeout 秒内轮询是否出现授权弹窗（如位置访问），出现则优先点「始终允许」。
    每 0.5s 检查一次，命中并点击成功即返回 True；到点仍无弹窗返回 False（正常情况）。
    """
    if timeout is None:
        timeout = cfg.PERMISSION_CHECK_TIMEOUT_SEC
    deadline = time.time() + timeout

    while time.time() < deadline:
        for locator in cfg.PERMISSION_ALLOW_LOCATORS:
            el = d(**locator)
            if el.exists:
                try:
                    el.click()
                    logger.info(f"授权弹窗已处理，点击 {locator}")
                    time.sleep(0.8)
                    return True
                except Exception as exc:
                    logger.warning(f"点击授权按钮 {locator} 失败：{exc}")
                    return False
        time.sleep(0.5)
    return False

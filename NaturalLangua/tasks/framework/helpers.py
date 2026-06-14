# ============================================================
# 【框架层】helpers.py
# 跨 APK 复用的 UI 辅助函数，减少各用例文件中的重复定位逻辑。
# ============================================================

from typing import Iterable

import uiautomator2 as u2

from utils.logger import logger


def is_package_foreground(d: u2.Device, package_name: str) -> bool:
    """判断指定包名是否在前台运行。"""
    current = d.app_current() or {}
    return current.get("package", "") == package_name


def click_first_match(d: u2.Device, locators: Iterable[dict], timeout: float = 3) -> bool:
    """
    按顺序尝试多个定位器，点击第一个存在的元素。

    参数：
        locators: 定位器字典列表，如 [{"text": "搜索"}, {"description": "搜索"}]
        timeout : 每个定位器等待元素出现的秒数

    返回：
        True  — 成功点击
        False — 所有定位器均未找到元素
    """
    for locator in locators:
        el = d(**locator)
        if el.wait(timeout=timeout):
            el.click()
            return True
    return False


def click_first_match_or_coord(
    d: u2.Device,
    locators: Iterable[dict],
    coord: tuple[int, int],
    warn_message: str,
    timeout: float = 3,
) -> None:
    """先尝试语义定位，失败则用坐标兜底并记录警告。"""
    if click_first_match(d, locators, timeout=timeout):
        return
    logger.warning(warn_message)
    d.click(*coord)


def any_element_exists(d: u2.Device, locators: Iterable[dict]) -> bool:
    """任意一个定位器匹配到元素即返回 True。"""
    return any(d(**locator).exists for locator in locators)


def dismiss_common_dialogs(d: u2.Device) -> None:
    """
    关闭常见弹窗（权限、更新、广告等）。
    各 APK 可在 teardown 或步骤开始前调用，减少偶发遮挡。
    """
    for locator in [
        {"text": "允许"},
        {"text": "同意"},
        {"text": "我知道了"},
        {"text": "以后再说"},
        {"text": "取消"},
        {"textContains": "关闭"},
    ]:
        el = d(**locator)
        if el.exists:
            el.click()

# ============================================================
# 【抖音 APK】helpers.py
# 抖音业务专用 UI 辅助（仅本 APK 使用，不放 common.py）
# ============================================================

import uiautomator2 as u2

from core.ui_automator import UIAutomator
from utils.logger import logger


def switch_city_to_shenzhen(d: u2.Device, ui: UIAutomator, city: str = "深圳"):
    """
    切换抖音同城频道到指定城市。
    多种定位方式依次尝试，全部失败时记录警告但不抛异常。
    """
    if d(text="同城").exists:
        d(text="同城").click()
        ui.wait(1)

    for locator in [
        {"resourceId": "com.ss.android.ugc.aweme:id/btn_city"},
        {"description": "切换城市"},
        {"text": "切换城市"},
        {"text": "城市"},
    ]:
        el = d(**locator)
        if el.exists:
            el.click()
            ui.wait(1)
            break

    if d(text=city).exists:
        d(text=city).click()
        ui.wait(1)
        return

    search_box = d(focused=True) if d(focused=True).exists else None
    if not search_box:
        for rid in [
            "com.ss.android.ugc.aweme:id/search_input",
            "com.ss.android.ugc.aweme:id/et_search",
        ]:
            if d(resourceId=rid).exists:
                search_box = d(resourceId=rid)
                break

    if search_box:
        search_box.click()
        d.send_keys(city)
        ui.wait(1)
        if d(text=city).exists:
            d(text=city).click()
            ui.wait(1)
    else:
        logger.warning("未找到城市切换入口，跳过同城切换")


def open_search(d: u2.Device):
    """点击首页右上角搜索放大镜，找不到时用坐标兜底。"""
    candidates = [
        {"description": "搜索"},
        {"description": "search"},
        {"resourceId": "com.ss.android.ugc.aweme:id/search_entrance"},
        {"resourceId": "com.ss.android.ugc.aweme:id/iv_search"},
        {"resourceId": "com.ss.android.ugc.aweme:id/action_search"},
    ]
    for loc in candidates:
        el = d(**loc)
        if el.exists:
            el.click()
            return

    w, h = d.window_size()
    logger.warning("未找到搜索图标，点击右上角坐标兜底")
    d.click(int(w * 0.92), int(h * 0.05))


def click_search_button(d: u2.Device):
    """点击搜索确认按钮，找不到时用回车兜底。"""
    candidates = [
        {"text": "搜索"},
        {"text": "Search"},
        {"resourceId": "com.ss.android.ugc.aweme:id/search_button"},
        {"resourceId": "com.ss.android.ugc.aweme:id/btn_search"},
        {"description": "搜索"},
    ]
    for loc in candidates:
        el = d(**loc)
        if el.exists:
            el.click()
            return

    logger.warning("未找到搜索按钮，使用回车键兜底")
    d.press("enter")


def click_first_video(d: u2.Device):
    """点击搜索结果列表第一个视频，找不到时用坐标兜底。"""
    candidates = [
        {"resourceId": "com.ss.android.ugc.aweme:id/cover"},
        {"resourceId": "com.ss.android.ugc.aweme:id/video_cover_layout"},
        {"resourceId": "com.ss.android.ugc.aweme:id/thumbnail"},
        {"description": "视频封面"},
    ]
    for loc in candidates:
        els = d(**loc)
        if els.exists:
            els[0].click()
            return

    w, h = d.window_size()
    logger.warning("未找到视频元素，点击屏幕中央兜底")
    d.click(w // 2, int(h * 0.35))

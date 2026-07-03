# ============================================================
# 【浏览器 APK】case_add_favorite.py
# 用例：搜索关键词后，通过工具菜单添加收藏，并在我的收藏中校验
# ============================================================

# ── IDE 直接运行支持：把项目根 NaturalLangua/ 加入 sys.path ──────────
import os as _os
import sys as _sys
_ROOT = _os.path.abspath(_os.path.dirname(__file__))
while _ROOT and not _os.path.exists(_os.path.join(_ROOT, "run_apk_tests.py")):
    _parent = _os.path.dirname(_ROOT)
    if _parent == _ROOT:
        break
    _ROOT = _parent
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

from tasks.apk.browser import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import (
    click_first_match,
    dismiss_common_dialogs,
    is_package_foreground,
)


class CaseAddFavorite(ApkTestCase):
    case_id = "TC005_add_favorite"
    case_name = "TC005_添加收藏到收藏夹"
    case_desc = "搜索关键词后，通过工具菜单添加收藏，在我的收藏中校验记录存在"

    KEYWORD = "好看的视频"

    # 底部工具栏 “工具” 按钮（主页 & Web 页两套 id）
    TOOL_BTN_LOCATORS = [
        {"description": "工具"},
        {"resourceId": "com.android.browser:id/toolbar_fun2"},
        {"resourceId": "com.android.browser:id/toolbar_web_fun2"},
    ]

    # 我的收藏页顶部返回键
    FAV_BACK_LOCATORS = [
        {"resourceId": "com.android.browser:id/stepos_toolbar_nav_button"},
        {"descriptionContains": "转到上一层级"},
    ]

    # Web 页底部工具栏最右侧 “主页” 按钮
    HOME_BTN_LOCATORS = [
        {"resourceId": "com.android.browser:id/toolbar_web_fun4"},
        {"description": "主页"},
    ]

    # 工具菜单中的 “退出” 项
    EXIT_LOCATORS = [
        {"text": "退出"},
        {"description": "退出"},
    ]

    # 我的收藏 → 编辑面板底部 “删除” 按钮
    DELETE_BTN_LOCATORS = [
        {"resourceId": "com.android.browser:id/delete"},
        {"description": "删除"},
    ]

    # 二次确认 “删除 N 个收藏” 按钮（用 “个收藏” 兜底避免命中列表里的“删除”）
    CONFIRM_DELETE_LOCATORS = [
        {"textContains": "个收藏"},
        {"resourceId": "android:id/text1"},
    ]

    def _click_tool_button(self) -> bool:
        return click_first_match(self.d, self.TOOL_BTN_LOCATORS, timeout=3)

    def _dismiss_permission_dialog(self) -> None:
        """网站权限弹窗（如位置信息）— 精准点一次，不影响页面其他元素。"""
        for btn_text in ("下次询问", "拒绝"):
            btn = self.d(text=btn_text)
            if btn.exists:
                btn.click()
                self.wait(1)
                return

    def run_steps(self) -> None:
        # ── 1. 启动浏览器 ────────────────────────────────────────────────
        self.app.launch_app(cfg.PACKAGE)
        self.wait(3)
        dismiss_common_dialogs(self.d)

        # ── 2. 点击主页搜索框 ────────────────────────────────────────────
        url_bar_locators = (
            [{"resourceId": rid} for rid in cfg.URL_BAR_IDS]
            + [{"descriptionContains": d} for d in getattr(cfg, "URL_BAR_DESCRIPTIONS", [])]
            + [{"textContains": h} for h in cfg.SEARCH_INPUT_HINTS]
        )
        if not click_first_match(self.d, url_bar_locators):
            w, h = self.d.window_size()
            self.d.click(w // 2, int(h * 0.08))
        self.wait(1)

        # ── 3. 输入关键词并点击搜索 ─────────────────────────────────────
        self.ui.clear_and_input(self.KEYWORD)
        self.wait(0.5)
        search_btn_locators = [
            {"text": "搜索"},
            {"text": "Search"},
            {"description": "搜索"},
        ]
        if not click_first_match(self.d, search_btn_locators, timeout=2):
            self.d.press("enter")
        self.wait(5)
        self._dismiss_permission_dialog()

        # ── 4. 点击底部工具栏 “工具” 按钮，弹出菜单 ─────────────────────
        self.assert_step(self._click_tool_button(), "底部工具栏应存在 '工具' 按钮")
        self.wait(1.5)

        # ── 5. 菜单中点击 “添加收藏” ────────────────────────────────────
        add_fav_locators = [
            {"text": "添加收藏"},
            {"description": "添加收藏"},
            {"textContains": "添加收藏"},
        ]
        self.assert_step(
            click_first_match(self.d, add_fav_locators, timeout=3),
            "工具菜单中应存在 '添加收藏' 项",
        )
        self.wait(1.5)

        # ── 6. 弹出 “添加到…” 分享对话框，点击 “收藏” 卡片落到收藏夹 ─────
        confirm_locators = [
            {"resourceId": "com.android.browser:id/add_to_bookmark"},
            {"text": "收藏"},
            {"description": "收藏"},
        ]
        self.assert_step(
            click_first_match(self.d, confirm_locators, timeout=5),
            "‘添加到…’对话框中应存在 ‘收藏’ 选项",
        )
        self.wait(2)

        # ── 7. 再次点击 “工具” 按钮 ─────────────────────────────────────
        self.assert_step(self._click_tool_button(), "应能再次唤出工具菜单")
        self.wait(1.5)

        # ── 8. 菜单中点击 “我的收藏” ───────────────────────────────────
        my_fav_locators = [
            {"text": "我的收藏"},
            {"description": "我的收藏"},
            {"textContains": "我的收藏"},
            {"text": "收藏"},
        ]
        self.assert_step(
            click_first_match(self.d, my_fav_locators, timeout=3),
            "工具菜单中应存在 '我的收藏' 项",
        )
        self.wait(3)

        # ── 9. 断言：收藏夹中出现关键词记录 ─────────────────────────────
        found = (
            self.d(textContains=self.KEYWORD).exists
            or self.d(descriptionContains=self.KEYWORD).exists
        )
        self.assert_step(found, f"收藏夹中应包含关键词 '{self.KEYWORD}'")

        # ── 10. 长按目标条目进入编辑态 ─────────────────────────────────
        target = self.d(textContains=self.KEYWORD)
        self.assert_step(target.exists, f"应能定位到 '{self.KEYWORD}' 条目用于长按")
        target.long_click(duration=1.0)
        self.wait(1.5)

        # ── 11. 编辑面板底部点击 “删除” ────────────────────────────────
        self.assert_step(
            click_first_match(self.d, self.DELETE_BTN_LOCATORS, timeout=3),
            "编辑面板底部应存在 '删除' 按钮",
        )
        self.wait(1.5)

        # ── 12. 弹出确认框，点击 “删除 N 个收藏” ─────────────────────────
        self.assert_step(
            click_first_match(self.d, self.CONFIRM_DELETE_LOCATORS, timeout=3),
            "应弹出 '删除 N 个收藏' 确认按钮",
        )
        self.wait(2)

        # ── 13. 断言：收藏夹已不再包含关键词 ────────────────────────────
        still_there = (
            self.d(textContains=self.KEYWORD).exists
            or self.d(descriptionContains=self.KEYWORD).exists
        )
        self.assert_step(not still_there, f"删除后收藏夹应不再包含 '{self.KEYWORD}'")

        # ── 14. 我的收藏页点返回，回到之前的网页 ─────────────────────────
        self.assert_step(
            click_first_match(self.d, self.FAV_BACK_LOCATORS, timeout=3),
            "我的收藏页应存在返回按钮",
        )
        self.wait(2)

        # ── 15. Web 页右下角 “主页” 按钮，回到浏览器主页 ─────────────────
        self.assert_step(
            click_first_match(self.d, self.HOME_BTN_LOCATORS, timeout=3),
            "Web 页底部应存在 '主页' 按钮",
        )
        self.wait(2)

        # ── 16. 再次点工具栏 → 菜单点 “退出” 完全退出浏览器 ─────────────
        self.assert_step(self._click_tool_button(), "主页也应能唤出工具菜单")
        self.wait(1.5)
        self.assert_step(
            click_first_match(self.d, self.EXIT_LOCATORS, timeout=3),
            "工具菜单中应存在 '退出' 项",
        )
        self.wait(2)

        # ── 17. 断言：浏览器已退出前台 ──────────────────────────────────
        self.assert_step(
            not is_package_foreground(self.d, cfg.PACKAGE),
            f"退出后浏览器不应仍在前台，包名 {cfg.PACKAGE}",
        )

    def teardown(self) -> None:
        """保险：无论用例通过与否都强制关闭浏览器，避免残留状态影响后续用例。"""
        try:
            if self.app:
                self.app.stop_app(cfg.PACKAGE)
        except Exception:
            pass
        super().teardown()


if __name__ == "__main__":
    from tasks.framework.runner import TestRunner
    _report = TestRunner().run_apk("browser", case_ids=[CaseAddFavorite.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)

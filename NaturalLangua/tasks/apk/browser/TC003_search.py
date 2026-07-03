# ============================================================
# 【浏览器 APK】case_search.py
# 用例：在浏览器内搜索关键词
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


class CaseSearch(ApkTestCase):
    case_id = "TC003_search"
    case_name = "TC003_浏览器内搜索"
    case_desc = f"搜索「{cfg.TEST_SEARCH_KEYWORD}」，回主页后经工具菜单退出恢复初始状态"

    # 底部工具栏 “工具” 按钮（主页 & Web 页两套 id）
    TOOL_BTN_LOCATORS = [
        {"description": "工具"},
        {"resourceId": "com.android.browser:id/toolbar_fun2"},
        {"resourceId": "com.android.browser:id/toolbar_web_fun2"},
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

    def run_steps(self) -> None:
        self.app.launch_app(cfg.PACKAGE)
        self.wait(3)
        dismiss_common_dialogs(self.d)

        # ── 打开搜索/地址栏 ───────────────────────────────────────────────
        locators = (
            [{"resourceId": rid} for rid in cfg.URL_BAR_IDS]
            + [{"textContains": hint} for hint in cfg.SEARCH_INPUT_HINTS]
        )
        if not click_first_match(self.d, locators):
            w, h = self.d.window_size()
            self.d.click(w // 2, int(h * 0.08))

        self.wait(1)
        self.ui.clear_and_input(cfg.TEST_SEARCH_KEYWORD)
        self.wait(0.5)

        # ── 点击搜索按钮或回车 ────────────────────────────────────────────
        search_btn_locators = [
            {"text": "搜索"},
            {"text": "Search"},
            {"description": "搜索"},
        ]
        if not click_first_match(self.d, search_btn_locators, timeout=2):
            self.d.press("enter")

        self.wait(4)

        # ── 断言：出现搜索结果特征 ───────────────────────────────────────
        has_results = (
            self.d(className="android.webkit.WebView").exists
            or self.d(textContains=cfg.TEST_SEARCH_KEYWORD).exists
            or self.d(textContains="天气").exists
            or self.d(scrollable=True).exists
        )
        self.assert_step(has_results, "搜索后应出现结果页或相关内容")

        # ── 清理 1：点 Web 页右下角 “主页” 按钮，回到浏览器主页 ─────────
        self.assert_step(
            click_first_match(self.d, self.HOME_BTN_LOCATORS, timeout=3),
            "Web 页底部应存在 '主页' 按钮",
        )
        self.wait(2)

        # ── 清理 2：主页点工具栏 → 菜单点 '退出' 完全退出浏览器 ─────────
        self.assert_step(
            click_first_match(self.d, self.TOOL_BTN_LOCATORS, timeout=3),
            "主页也应能唤出工具菜单",
        )
        self.wait(1.5)
        self.assert_step(
            click_first_match(self.d, self.EXIT_LOCATORS, timeout=3),
            "工具菜单中应存在 '退出' 项",
        )
        self.wait(2)

        # ── 清理 3：断言浏览器已退出前台 ────────────────────────────────
        self.assert_step(
            not is_package_foreground(self.d, cfg.PACKAGE),
            f"退出后浏览器不应仍在前台，包名 {cfg.PACKAGE}",
        )

    def teardown(self) -> None:
        """兜底：无论断言结果如何都强制关闭浏览器，避免残留状态影响后续用例。"""
        try:
            if self.app:
                self.app.stop_app(cfg.PACKAGE)
        except Exception:
            pass
        super().teardown()


if __name__ == "__main__":
    from tasks.framework.runner import TestRunner
    _report = TestRunner().run_apk("browser", case_ids=[CaseSearch.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)

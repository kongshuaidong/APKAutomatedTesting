# ============================================================
# 【浏览器 APK】case_open_url.py
# 用例：在地址栏输入 URL 并打开网页
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


class CaseOpenUrl(ApkTestCase):
    case_id = "TC002_open_url"
    case_name = "TC002_打开指定网址"
    case_desc = f"启动浏览器打开 {cfg.TEST_URL}，回主页后经工具菜单退出恢复初始状态"

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

        # ── 点击地址栏 ───────────────────────────────────────────────────
        url_bar_locators = (
            [{"resourceId": rid} for rid in cfg.URL_BAR_IDS]
            + [{"descriptionContains": d} for d in getattr(cfg, "URL_BAR_DESCRIPTIONS", [])]
            + [{"textContains": hint} for hint in cfg.SEARCH_INPUT_HINTS]
            + [{"description": "地址栏"}, {"description": "搜索"}]
        )
        clicked = click_first_match(self.d, url_bar_locators)
        if not clicked:
            w, h = self.d.window_size()
            self.d.click(w // 2, int(h * 0.08))

        self.wait(1)
        self.ui.clear_and_input(cfg.TEST_URL)
        self.wait(0.5)
        self.d.press("enter")
        self.wait(4)

        # 网站权限弹窗（如位置信息）— 精准点一次，不影响页面其他元素
        for btn_text in ("下次询问", "拒绝"):
            btn = self.d(text=btn_text)
            if btn.exists:
                btn.click()
                self.wait(1)
                break

        # ── 断言：仍在浏览器内，且页面已加载（出现 WebView 或标题）──────
        still_in_browser = is_package_foreground(self.d, cfg.PACKAGE)
        page_loaded = (
            self.d(className="android.webkit.WebView").exists
            or self.d(textContains="百度").exists
            or self.d(descriptionContains="百度").exists
        )
        self.assert_step(still_in_browser, "访问网页后应仍在浏览器前台")
        self.assert_step(page_loaded, "网页应已加载（WebView 或页面标题可见）")

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
    _report = TestRunner().run_apk("browser", case_ids=[CaseOpenUrl.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)

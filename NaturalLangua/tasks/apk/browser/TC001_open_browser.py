# ============================================================
# 【浏览器 APK】case_open_browser.py
# 用例：启动浏览器并验证进入前台
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


class CaseOpenBrowser(ApkTestCase):
    case_id = "TC001_open_browser"
    case_name = "TC001_启动浏览器"
    case_desc = "通过包名启动浏览器，断言在前台后经工具菜单退出回到初始状态"

    # 主页底部工具栏 “工具” 按钮
    TOOL_BTN_LOCATORS = [
        {"description": "工具"},
        {"resourceId": "com.android.browser:id/toolbar_fun2"},
        {"resourceId": "com.android.browser:id/toolbar_web_fun2"},
    ]

    # 工具菜单中的 “退出” 项
    EXIT_LOCATORS = [
        {"text": "退出"},
        {"description": "退出"},
    ]

    def run_steps(self) -> None:
        # ── 1. 启动浏览器 ──────────────────────────────────────────────
        self.app.launch_app(cfg.PACKAGE)
        self.wait(3)
        dismiss_common_dialogs(self.d)

        # ── 2. 断言：浏览器在前台 ─────────────────────────────────────
        self.assert_step(
            is_package_foreground(self.d, cfg.PACKAGE),
            f"浏览器应在前台，期望包名 {cfg.PACKAGE}",
        )

        # ── 3. 点击底部工具栏 “工具” 按钮 ─────────────────────────────
        self.assert_step(
            click_first_match(self.d, self.TOOL_BTN_LOCATORS, timeout=3),
            "主页底部工具栏应存在 '工具' 按钮",
        )
        self.wait(1.5)

        # ── 4. 菜单中点击 “退出” ─────────────────────────────────────
        self.assert_step(
            click_first_match(self.d, self.EXIT_LOCATORS, timeout=3),
            "工具菜单中应存在 '退出' 项",
        )
        self.wait(2)

        # ── 5. 断言：浏览器已退出前台 ─────────────────────────────────
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
    _report = TestRunner().run_apk("browser", case_ids=[CaseOpenBrowser.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)
  
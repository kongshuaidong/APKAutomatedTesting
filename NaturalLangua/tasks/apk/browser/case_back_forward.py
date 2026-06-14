# ============================================================
# 【浏览器 APK】case_back_forward.py
# 用例：验证浏览器前进/后退基本导航
# ============================================================

from tasks.apk.browser import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import click_first_match, dismiss_common_dialogs


class CaseBackForward(ApkTestCase):
    case_id = "back_forward"
    case_name = "前进后退导航"
    case_desc = "打开网页后执行返回，验证导航可用"

    def run_steps(self) -> None:
        self.app.launch_app(cfg.PACKAGE)
        self.wait(3)
        dismiss_common_dialogs(self.d)

        # 先打开一个页面
        locators = [{"resourceId": rid} for rid in cfg.URL_BAR_IDS]
        click_first_match(self.d, locators) or self.d.click(
            *self._top_center_coord()
        )
        self.wait(1)
        self.ui.clear_and_input(cfg.TEST_URL)
        self.d.press("enter")
        self.wait(4)

        self.assert_step(
            self.d(className="android.webkit.WebView").exists
            or self.d(textContains="百度").exists,
            "应先成功打开测试网页",
        )

        # ── 返回 ─────────────────────────────────────────────────────────
        back_locators = [
            {"description": "返回"},
            {"description": "Back"},
            {"resourceId": "com.heytap.browser:id/back"},
            {"resourceId": "com.android.chrome:id/back_button"},
        ]
        if not click_first_match(self.d, back_locators, timeout=2):
            self.ui.back()

        self.wait(2)

        # 断言：返回后仍在浏览器（未退出 App）
        current_pkg = self.d.app_current().get("package", "")
        self.assert_step(
            current_pkg == cfg.PACKAGE,
            f"返回后应仍在浏览器内，实际包名：{current_pkg}",
        )

    def _top_center_coord(self) -> tuple[int, int]:
        w, h = self.d.window_size()
        return w // 2, int(h * 0.08)

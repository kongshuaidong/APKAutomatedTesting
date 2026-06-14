# ============================================================
# 【浏览器 APK】case_open_browser.py
# 用例：启动浏览器并验证进入前台
# ============================================================

from tasks.apk.browser import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import dismiss_common_dialogs, is_package_foreground


class CaseOpenBrowser(ApkTestCase):
    case_id = "open_browser"
    case_name = "启动浏览器"
    case_desc = "通过包名启动浏览器，断言 App 在前台运行"

    def run_steps(self) -> None:
        self.app.launch_app(cfg.PACKAGE)
        self.wait(3)
        dismiss_common_dialogs(self.d)

        self.assert_step(
            is_package_foreground(self.d, cfg.PACKAGE),
            f"浏览器应在前台，期望包名 {cfg.PACKAGE}",
        )

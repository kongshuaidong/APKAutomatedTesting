# ============================================================
# 【应用商店 APK】case_exit_store.py
# 用例：退出应用商店（清理环境，适合作为该 APK 最后一条用例）
# ============================================================

from tasks.apk.app_store import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import is_package_foreground


class CaseExitStore(ApkTestCase):
    case_id = "TC004_exit_store"
    case_name = "TC004_退出应用商店"
    case_desc = "强制停止应用商店，断言已不在前台"

    def run_steps(self) -> None:
        self.app.launch_app(cfg.PACKAGE)
        self.wait(2)
        self.assert_step(
            is_package_foreground(self.d, cfg.PACKAGE),
            "退出前应确认商店在前台",
        )

        self.app.stop_app(cfg.PACKAGE)
        self.wait(1)

        self.assert_step(
            not is_package_foreground(self.d, cfg.PACKAGE),
            f"退出后应用商店不应在前台",
        )

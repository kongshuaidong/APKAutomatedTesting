# ============================================================
# 【应用商店 APK】case_open_store.py
# 用例：启动应用商店并验证前台
# ============================================================

from tasks.apk.app_store import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import dismiss_common_dialogs, is_package_foreground


class CaseOpenStore(ApkTestCase):
    case_id = "open_store"
    case_name = "启动应用商店"
    case_desc = "通过包名启动应用商店，断言 App 在前台"

    def run_steps(self) -> None:
        self.app.launch_app(cfg.PACKAGE)
        self.wait(4)
        dismiss_common_dialogs(self.d)

        self.assert_step(
            is_package_foreground(self.d, cfg.PACKAGE),
            f"应用商店应在前台，期望包名 {cfg.PACKAGE}",
        )

        # 首页常见元素：搜索入口或推荐 Tab
        home_loaded = (
            self.d(text="首页").exists
            or self.d(textContains="搜索").exists
            or self.d(descriptionContains="搜索").exists
            or self.d(scrollable=True).exists
        )
        self.assert_step(home_loaded, "应用商店首页应已加载（搜索入口或列表可见）")

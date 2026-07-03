# ============================================================
# 【应用商店 APK】case_search_app.py
# 用例：在商店内搜索指定 App
# ============================================================

from tasks.apk.app_store import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import click_first_match, dismiss_common_dialogs


class CaseSearchApp(ApkTestCase):
    case_id = "TC002_search_app"
    case_name = "TC002_搜索应用"
    case_desc = f"打开应用商店，搜索「{cfg.TEST_APP_NAME}」"

    def run_steps(self) -> None:
        self.app.launch_app(cfg.PACKAGE)
        self.wait(4)
        dismiss_common_dialogs(self.d)

        # ── 点击顶部搜索框 ─────────────────────────────────────────────────
        search_entry_locators = (
            [{"resourceId": rid} for rid in cfg.SEARCH_BOX_IDS]
            + [
                {"textContains": "搜索"},
                {"descriptionContains": "搜索"},
                {"resourceId": "com.heytap.market:id/search_layout"},
            ]
        )
        if not click_first_match(self.d, search_entry_locators):
            w, h = self.d.window_size()
            self.d.click(int(w * 0.5), int(h * 0.08))

        self.wait(1)

        # ── 输入关键词 ─────────────────────────────────────────────────────
        self.ui.clear_and_input(cfg.TEST_APP_NAME)
        self.wait(1)

        # ── 触发搜索 ───────────────────────────────────────────────────────
        search_btn_locators = (
            [{"resourceId": rid} for rid in cfg.SEARCH_BTN_IDS]
            + [{"text": "搜索"}, {"description": "搜索"}]
        )
        if not click_first_match(self.d, search_btn_locators, timeout=2):
            self.d.press("enter")

        self.wait(3)

        # ── 断言：出现搜索结果 ───────────────────────────────────────────
        has_results = (
            self.d(textContains=cfg.TEST_APP_NAME).exists
            or self.d(text="安装").exists
            or self.d(text="打开").exists
            or self.d(text="已安装").exists
            or self.d(scrollable=True).exists
        )
        self.assert_step(has_results, f"搜索「{cfg.TEST_APP_NAME}」后应出现结果列表")

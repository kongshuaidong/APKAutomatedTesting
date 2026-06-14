# ============================================================
# 【应用商店 APK】case_open_detail.py
# 用例：搜索 App 并进入详情页
# ============================================================

from tasks.apk.app_store import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import click_first_match, dismiss_common_dialogs


class CaseOpenDetail(ApkTestCase):
    case_id = "open_detail"
    case_name = "打开应用详情"
    case_desc = f"搜索「{cfg.TEST_APP_NAME}」并点击第一条进入详情页"

    def run_steps(self) -> None:
        self.app.launch_app(cfg.PACKAGE)
        self.wait(4)
        dismiss_common_dialogs(self.d)

        # ── 搜索（与 search_app 类似，本用例侧重详情页）────────────────────
        search_entry = (
            [{"resourceId": rid} for rid in cfg.SEARCH_BOX_IDS]
            + [{"textContains": "搜索"}]
        )
        click_first_match(self.d, search_entry) or self.d.click(
            *self._top_search_coord()
        )
        self.wait(1)
        self.ui.clear_and_input(cfg.TEST_APP_NAME)
        self.wait(0.5)

        btn_locators = (
            [{"resourceId": rid} for rid in cfg.SEARCH_BTN_IDS]
            + [{"text": "搜索"}]
        )
        click_first_match(self.d, btn_locators, timeout=2) or self.d.press("enter")
        self.wait(3)

        # ── 点击第一条结果 ─────────────────────────────────────────────────
        result_locators = [
            {"textContains": cfg.TEST_APP_NAME},
            {"resourceId": "com.heytap.market:id/tv_name"},
            {"resourceId": "com.heytap.market:id/app_name"},
        ]
        clicked = click_first_match(self.d, result_locators, timeout=3)
        if not clicked:
            w, h = self.d.window_size()
            self.d.click(w // 2, int(h * 0.28))

        self.wait(3)

        # ── 断言：详情页特征（安装/打开按钮、应用名）──────────────────────
        detail_loaded = (
            self.d(text="安装").exists
            or self.d(text="打开").exists
            or self.d(text="已安装").exists
            or self.d(text="更新").exists
            or self.d(textContains=cfg.TEST_APP_NAME).exists
        )
        self.assert_step(detail_loaded, "进入详情页后应出现安装/打开按钮或应用名称")

    def _top_search_coord(self) -> tuple[int, int]:
        w, h = self.d.window_size()
        return int(w * 0.5), int(h * 0.08)

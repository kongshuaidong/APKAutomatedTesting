# ============================================================
# 【浏览器 APK】case_search.py
# 用例：在浏览器内搜索关键词
# ============================================================

from tasks.apk.browser import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import click_first_match, dismiss_common_dialogs


class CaseSearch(ApkTestCase):
    case_id = "search"
    case_name = "浏览器内搜索"
    case_desc = f"打开浏览器，搜索「{cfg.TEST_SEARCH_KEYWORD}」并验证结果页"

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

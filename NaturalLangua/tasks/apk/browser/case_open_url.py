# ============================================================
# 【浏览器 APK】case_open_url.py
# 用例：在地址栏输入 URL 并打开网页
# ============================================================

from tasks.apk.browser import config as cfg
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import (
    click_first_match,
    dismiss_common_dialogs,
    is_package_foreground,
)


class CaseOpenUrl(ApkTestCase):
    case_id = "open_url"
    case_name = "打开指定网址"
    case_desc = f"启动浏览器，在地址栏输入 {cfg.TEST_URL} 并访问"

    def run_steps(self) -> None:
        self.app.launch_app(cfg.PACKAGE)
        self.wait(3)
        dismiss_common_dialogs(self.d)

        # ── 点击地址栏 ───────────────────────────────────────────────────
        url_bar_locators = (
            [{"resourceId": rid} for rid in cfg.URL_BAR_IDS]
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

        # ── 断言：仍在浏览器内，且页面已加载（出现 WebView 或标题）──────
        still_in_browser = is_package_foreground(self.d, cfg.PACKAGE)
        page_loaded = (
            self.d(className="android.webkit.WebView").exists
            or self.d(textContains="百度").exists
            or self.d(descriptionContains="百度").exists
        )
        self.assert_step(still_in_browser, "访问网页后应仍在浏览器前台")
        self.assert_step(page_loaded, "网页应已加载（WebView 或页面标题可见）")

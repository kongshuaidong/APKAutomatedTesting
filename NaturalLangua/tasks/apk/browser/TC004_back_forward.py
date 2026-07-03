# ============================================================
# 【浏览器 APK】case_back_forward.py
# 用例：验证浏览器前进/后退基本导航
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


class CaseBackForward(ApkTestCase):
    case_id = "TC004_back_forward"
    case_name = "TC004_前进后退导航"
    case_desc = "打开百度 → 滑动点击结果进入详情页 → 后退 → 前进 → 主页 → 工具菜单退出"

    # 底部工具栏 “工具” 按钮（主页 & Web 页两套 id）
    TOOL_BTN_LOCATORS = [
        {"description": "工具"},
        {"resourceId": "com.android.browser:id/toolbar_fun2"},
        {"resourceId": "com.android.browser:id/toolbar_web_fun2"},
    ]

    # Web 页底部工具栏 “后退” 按钮（fun0 = 最左）
    BACK_BTN_LOCATORS = [
        {"resourceId": "com.android.browser:id/toolbar_web_fun0"},
        {"description": "后退"},
        {"description": "返回"},
        {"description": "Back"},
    ]

    # Web 页底部工具栏 “前进” 按钮（fun1 = 后退右侧）
    FORWARD_BTN_LOCATORS = [
        {"resourceId": "com.android.browser:id/toolbar_web_fun1"},
        {"description": "前进"},
        {"description": "Forward"},
    ]

    # Web 页底部工具栏 “主页” 按钮（fun4 = 最右）
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

        # ── 1. 打开百度 ──────────────────────────────────────────────────
        url_bar_locators = (
            [{"resourceId": rid} for rid in cfg.URL_BAR_IDS]
            + [{"descriptionContains": d} for d in getattr(cfg, "URL_BAR_DESCRIPTIONS", [])]
            + [{"textContains": h} for h in cfg.SEARCH_INPUT_HINTS]
        )
        if not click_first_match(self.d, url_bar_locators):
            w, h = self.d.window_size()
            self.d.click(w // 2, int(h * 0.08))
        self.wait(1)
        self.ui.clear_and_input(cfg.TEST_URL)
        self.d.press("enter")
        self.wait(4)

        # 网站权限弹窗（如位置信息）— 精准点一次
        for btn_text in ("下次询问", "拒绝"):
            btn = self.d(text=btn_text)
            if btn.exists:
                btn.click()
                self.wait(1)
                break

        self.assert_step(
            self.d(className="android.webkit.WebView").exists
            or self.d(textContains="百度").exists,
            "应先成功打开百度首页",
        )

        # ── 2. 上滑 + 点击内容，进入详情页（最多重试 3 次，兜底 flakiness）─
        # 首次点击可能落在广告 / 空白 / 未加载完的位置，导航失败页面不变
        # 用 “百度一下” 按钮是否仍在作为 “还在百度首页” 的信号，失败换坐标重试
        w, h = self.d.window_size()
        navigated = False
        for attempt in range(3):
            # 每次上滑距离略微不同，避免同一位置反复失败
            self.d.swipe(
                w // 2,
                int(h * 0.75),
                w // 2,
                int(h * (0.30 - attempt * 0.05)),
                duration=0.3,
            )
            self.wait(1.5)
            # 每次点击 y 坐标微调，扩大命中真实内容的概率
            self.d.click(w // 2, int(h * (0.40 + attempt * 0.05)))
            self.wait(5)
            still_on_home = self.d(text="百度一下").exists
            if not still_on_home and is_package_foreground(self.d, cfg.PACKAGE):
                navigated = True
                break

        self.assert_step(navigated, "点击内容后应进入详情页（'百度一下' 应不再可见）")

        # ── 4. 点后退按钮，回到搜索结果页 ───────────────────────────────
        self.assert_step(
            click_first_match(self.d, self.BACK_BTN_LOCATORS, timeout=3),
            "详情页底部应存在 '后退' 按钮",
        )
        self.wait(3)
        self.assert_step(
            is_package_foreground(self.d, cfg.PACKAGE),
            f"后退后应仍在浏览器内，包名 {cfg.PACKAGE}",
        )

        # ── 5. 点前进按钮，回到详情页 ───────────────────────────────────
        self.assert_step(
            click_first_match(self.d, self.FORWARD_BTN_LOCATORS, timeout=3),
            "结果页底部应存在 '前进' 按钮",
        )
        self.wait(3)
        self.assert_step(
            is_package_foreground(self.d, cfg.PACKAGE),
            f"前进后应仍在浏览器内，包名 {cfg.PACKAGE}",
        )

        # ── 6. 清理：点右下角 “主页” 按钮回浏览器主页 ────────────────────
        self.assert_step(
            click_first_match(self.d, self.HOME_BTN_LOCATORS, timeout=3),
            "Web 页底部应存在 '主页' 按钮",
        )
        self.wait(2)

        # ── 7. 清理：主页点工具栏 → 菜单点 '退出' ────────────────────────
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

        # ── 8. 断言：浏览器已退出前台 ───────────────────────────────────
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
    _report = TestRunner().run_apk("browser", case_ids=[CaseBackForward.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)

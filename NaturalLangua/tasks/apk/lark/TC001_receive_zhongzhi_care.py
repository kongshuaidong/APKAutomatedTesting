# ============================================================
# 【飞书 APK】TC001_receive_zhongzhi_care.py
# 用例：领取中智关爱 · 奋斗食代
#   1. 上滑解锁手机
#   2. 打开飞书
#   3. 点击底部「工作台」
#   4. 点击「中智关爱」
#   5. 中智关爱页面点击「奋斗食代」
#   6. 奋斗食代页面点击「立即领取」
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

from tasks.apk.lark import config as cfg
from tasks.apk.lark.helpers import dismiss_location_permission, unlock_screen
from tasks.framework.base_case import ApkTestCase
from tasks.framework.helpers import (
    any_element_exists,
    click_first_match,
    dismiss_common_dialogs,
    is_package_foreground,
)
from utils.logger import logger


class CaseReceiveZhongzhiCare(ApkTestCase):
    case_id = "TC001_receive_zhongzhi_care"
    case_name = "TC001_领取中智关爱"
    case_desc = "解锁 → 打开飞书 → 工作台 → 中智关爱 → 奋斗食代 → 立即领取"

    def run_steps(self) -> None:
        # ── 1. 上滑解锁 ──────────────────────────────────────────────
        unlock_screen(self.d)

        # ── 2. 打开飞书 ──────────────────────────────────────────────
        self.app.launch_app(cfg.PACKAGE)
        self.wait(cfg.LARK_LAUNCH_WAIT_SEC)
        dismiss_common_dialogs(self.d)
        self.assert_step(
            is_package_foreground(self.d, cfg.PACKAGE),
            f"飞书应在前台，期望包名 {cfg.PACKAGE}",
        )

        # ── 3. 点击底部「工作台」──────────────────────────────────────
        self.assert_step(
            click_first_match(self.d, cfg.WORKBENCH_LOCATORS, timeout=8),
            "飞书底部导航应存在「工作台」入口",
        )
        self.wait(3)

        # ── 4. 点击「中智关爱」──────────────────────────────────────
        self.assert_step(
            click_first_match(self.d, cfg.ZHONGZHI_CARE_LOCATORS, timeout=8),
            "工作台应存在「中智关爱」入口（若不存在请先在飞书「我的常用」中添加）",
        )
        self.wait(cfg.H5_LOAD_WAIT_SEC)
        # 中智关爱 H5 加载后可能弹出「地理位置授权」，2s 内轮询到就点「确定」
        dismiss_location_permission(self.d)
        dismiss_common_dialogs(self.d)

        # ── 5. 点击「奋斗食代」──────────────────────────────────────
        self.assert_step(
            click_first_match(self.d, cfg.FENDOU_SHIDAI_LOCATORS, timeout=8),
            "中智关爱首页应存在「奋斗食代」入口",
        )
        self.wait(cfg.H5_LOAD_WAIT_SEC)

        # ── 6. 点击「立即领取」──────────────────────────────────────
        # 未出现时优先给出可读的原因（当前按钮实际状态）
        if not click_first_match(self.d, cfg.RECEIVE_NOW_LOCATORS, timeout=8):
            current_states = [
                t for t in cfg.ALTERNATIVE_STATE_TEXTS
                if any_element_exists(self.d, [{"text": t}])
            ]
            logger.warning(
                f"未找到「立即领取」，页面上实际可见的状态文案: {current_states or '无匹配'}"
            )
            self.assert_step(
                False,
                (
                    "奋斗食代页面未出现「立即领取」按钮。"
                    f" 页面实际状态: {current_states or '未知'}。"
                    " 请在领取时间窗口（工作日/休息日 20:30-23:59）内运行。"
                ),
            )
        self.wait(2)
        logger.info("已点击「立即领取」")


if __name__ == "__main__":
    from tasks.framework.runner import TestRunner
    _report = TestRunner().run_apk("lark", case_ids=[CaseReceiveZhongzhiCare.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)

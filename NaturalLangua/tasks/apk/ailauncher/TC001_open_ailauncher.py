# ============================================================
# 【AI 桌面 APK】TC001_open_ailauncher.py
# 用例：解锁手机 → 主桌面点击「Agent空间」→ 断言进入 AI 桌面
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

from tasks.apk.ailauncher import config as cfg
from tasks.apk.ailauncher.helpers import enter_ai_launcher
from tasks.framework.base_case import ApkTestCase
from utils.logger import logger


class CaseOpenAILauncher(ApkTestCase):
    case_id = "TC001_open_ailauncher"
    case_name = "TC001_启动AI桌面"
    case_desc = "解锁手机后从主桌面点击「Agent空间」入口，断言 AI 桌面在前台"

    def run_steps(self) -> None:
        entered = enter_ai_launcher(self.d)
        current = self.d.app_current()
        logger.info(f"进入后前台应用: package={current.get('package')} activity={current.get('activity')}")
        self.assert_step(
            entered,
            f"应能通过桌面「Agent空间」进入 AI 桌面，实际前台包名 {current.get('package')}",
        )

    def teardown(self) -> None:
        """兜底：无论断言结果如何都强制关闭，避免残留状态影响后续用例。"""
        try:
            if self.app:
                self.app.stop_app(cfg.PACKAGE)
        except Exception:
            pass
        super().teardown()


if __name__ == "__main__":
    from tasks.framework.runner import TestRunner
    _report = TestRunner().run_apk("ailauncher", case_ids=[CaseOpenAILauncher.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)

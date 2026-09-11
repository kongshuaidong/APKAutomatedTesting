# ============================================================
# 【AI 桌面 APK】TC003_recommend_iced_americano.py
# 用例：输入「我要点一杯冰美式」，验证回复中包含三方 APP 推荐理由
# ============================================================

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

from tasks.apk.ailauncher._recommend_base import RecommendReasonCase


class CaseRecommendIcedAmericano(RecommendReasonCase):
    case_id = "TC003_recommend_iced_americano"
    case_name = "TC003_点一杯瑞幸冰美式_推荐理由"
    case_desc = "输入「我要点一杯瑞幸冰美式，配送到彩讯大厦，电话18598032222」，验证回复中包含具体 APP 推荐理由"
    QUERY = "我要点一杯冰美式"


if __name__ == "__main__":
    from tasks.framework.runner import TestRunner
    _report = TestRunner().run_apk("ailauncher", case_ids=[CaseRecommendIcedAmericano.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)

# ============================================================
# 【AI 桌面 APK】__init__.py
# 注册本 APK 的元信息与用例列表（供 framework/registry 加载）
# ============================================================

from tasks.apk.ailauncher.TC001_open_ailauncher import CaseOpenAILauncher
from tasks.apk.ailauncher.TC002_recommend_reasons import CaseRecommendReasons
from tasks.apk.ailauncher.config import PACKAGE

APK_INFO = {
    "apk_id": "ailauncher",
    "apk_name": "AI 桌面",
    "package_name": PACKAGE,
    "description": "AI 桌面/启动器核心能力 + 三方 APP 推荐理由批量验证",
}

# 用例执行顺序（run_apk 无 filter 时按此顺序）
CASES = [
    CaseOpenAILauncher,
    CaseRecommendReasons,
]

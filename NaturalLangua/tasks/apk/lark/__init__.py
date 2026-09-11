# ============================================================
# 【飞书 APK】__init__.py
# 注册本 APK 的元信息与用例列表（供 framework/registry 加载）
# ============================================================

from tasks.apk.lark.TC001_receive_zhongzhi_care import CaseReceiveZhongzhiCare
from tasks.apk.lark.config import PACKAGE

APK_INFO = {
    "apk_id": "lark",
    "apk_name": "飞书",
    "package_name": PACKAGE,
    "description": "飞书工作台自动化：中智关爱 · 奋斗食代领取",
}

CASES = [
    CaseReceiveZhongzhiCare,
]

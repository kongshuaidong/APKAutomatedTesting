# ============================================================
# 【抖音 APK】__init__.py
# ============================================================

from tasks.apk.douyin.TC001_daily import CaseDaily
from tasks.apk.douyin.config import PACKAGE

APK_INFO = {
    "apk_id": "douyin",
    "apk_name": "抖音",
    "package_name": PACKAGE,
    "description": "抖音自动化：每日搜索播放任务",
}

CASES = [
    CaseDaily,
]

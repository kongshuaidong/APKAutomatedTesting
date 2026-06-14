# ============================================================
# 【应用商店 APK】__init__.py
# ============================================================

from tasks.apk.app_store.case_exit_store import CaseExitStore
from tasks.apk.app_store.case_open_detail import CaseOpenDetail
from tasks.apk.app_store.case_open_store import CaseOpenStore
from tasks.apk.app_store.case_search_app import CaseSearchApp
from tasks.apk.app_store.config import PACKAGE

APK_INFO = {
    "apk_id": "app_store",
    "apk_name": "应用商店",
    "package_name": PACKAGE,
    "description": "应用商店核心能力：启动、搜索、详情页、退出",
}

CASES = [
    CaseOpenStore,
    CaseSearchApp,
    CaseOpenDetail,
    CaseExitStore,
]

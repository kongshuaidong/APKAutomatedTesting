# ============================================================
# 【浏览器 APK】__init__.py
# 注册本 APK 的元信息与用例列表（供 framework/registry 加载）
# ============================================================

from tasks.apk.browser.TC001_open_browser import CaseOpenBrowser
from tasks.apk.browser.TC002_open_url import CaseOpenUrl
from tasks.apk.browser.TC003_search import CaseSearch
from tasks.apk.browser.TC004_back_forward import CaseBackForward
from tasks.apk.browser.TC005_add_favorite import CaseAddFavorite
from tasks.apk.browser.config import PACKAGE

APK_INFO = {
    "apk_id": "browser",
    "apk_name": "手机浏览器",
    "package_name": "com.android.browser",
    "description": "浏览器核心能力：启动、打开网址、搜索、前进后退",
}

# 用例执行顺序（run_apk 无 filter 时按此顺序）
CASES = [
    CaseOpenBrowser,
    CaseOpenUrl,
    CaseSearch,
    CaseBackForward,
    CaseAddFavorite,
]

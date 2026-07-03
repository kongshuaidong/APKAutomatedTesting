# ============================================================
# 【浏览器 APK】config.py
# 包名与常量配置 — 换品牌/机型时优先修改本文件。
#
# OPPO/ColorOS 默认浏览器：com.heytap.browser
# 若使用 Chrome，将 PACKAGE 改为 com.android.chrome
# ============================================================

# 当前使用的浏览器包名（按优先级注释，改 PACKAGE 即可切换）
PACKAGE = "com.android.browser"
# PACKAGE = "com.android.chrome"
# PACKAGE = "com.coloros.browser"

# 测试用 URL / 关键词（各用例共用，方便统一修改）
TEST_URL = "https://www.baidu.com"
TEST_SEARCH_KEYWORD = "天气预报"

# 常见控件 resourceId（不同浏览器版本可能不同，用例中会配合 text 兜底）
URL_BAR_IDS = [
    "com.android.browser:id/search_bar_url_container",
    "com.android.browser:id/search_bar",
    "com.android.browser:id/search_hint",
    "com.heytap.browser:id/url_bar",
    "com.heytap.browser:id/search_box",
    "com.android.chrome:id/url_bar",
    "com.android.chrome:id/search_box_text",
]

SEARCH_INPUT_HINTS = ["搜索", "输入网址", "Search or type URL"]

URL_BAR_DESCRIPTIONS = ["搜索或输入网址", "地址栏"]

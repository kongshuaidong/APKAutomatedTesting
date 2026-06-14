# ============================================================
# 【应用商店 APK】config.py
# 包名与常量 — OPPO/一加/Realme 通常为 HeyTap 商店
# ============================================================

# 当前使用的应用商店包名
PACKAGE = "com.heytap.market"
# PACKAGE = "com.oppo.market"
# PACKAGE = "com.xiaomi.market"   # 小米
# PACKAGE = "com.huawei.appmarket" # 华为

# 搜索测试用的 App 名称（需确保商店内能搜到）
TEST_APP_NAME = "微信"

# 常见控件 ID（版本差异大，用例中会配合 text 兜底）
SEARCH_BOX_IDS = [
    "com.heytap.market:id/search_src_text",
    "com.heytap.market:id/search_edit",
    "com.heytap.market:id/et_search",
]

SEARCH_BTN_IDS = [
    "com.heytap.market:id/search_go_btn",
    "com.heytap.market:id/btn_search",
]

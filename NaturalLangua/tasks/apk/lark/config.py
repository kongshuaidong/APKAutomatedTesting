# ============================================================
# 【飞书 APK】config.py
# 包名与常量配置 — 换机型/版本时优先修改本文件。
# ============================================================

# 飞书包名
PACKAGE = "com.ss.android.lark"

# ── 底部导航「工作台」入口 ───────────────────────────────────────
WORKBENCH_LOCATORS = [
    {"text": "工作台"},
    {"description": "工作台"},
    {"resourceIdMatches": r".*(tab|nav).*work.*"},
]

# ── 工作台「我的常用」中的「中智关爱」入口 ────────────────────
ZHONGZHI_CARE_LOCATORS = [
    {"text": "中智关爱"},
    {"description": "中智关爱"},
    {"textContains": "中智"},
]

# ── 中智关爱首页的「奋斗食代」入口 ────────────────────────────
FENDOU_SHIDAI_LOCATORS = [
    {"text": "奋斗食代"},
    {"description": "奋斗食代"},
    {"textContains": "奋斗食代"},
]

# ── 奋斗食代页面的「立即领取」按钮 ────────────────────────────
# 注：仅在领取时间窗口内（工作日/休息日 20:30-23:59）才显示为「立即领取」；
# 其他时段为「尚未开始」/「明天再来」/「去使用」，用例会报可读的失败信息。
RECEIVE_NOW_LOCATORS = [
    {"text": "立即领取"},
    {"description": "立即领取"},
    {"textContains": "立即领取"},
]

# 若「立即领取」未出现，这些替代文案能辅助排查真实按钮状态
ALTERNATIVE_STATE_TEXTS = [
    "尚未开始",
    "明天再来",
    "去使用",
    "已领取",
]

# ── 地理位置授权弹窗（进入中智关爱 H5 后可能弹出）─────────────
# 弹窗标题「地理位置授权」，按钮「取消 / 确定」，用例点击「确定」允许
LOCATION_PERMISSION_TITLE_LOCATORS = [
    {"textContains": "地理位置授权"},
    {"textContains": "地理位置"},
]
LOCATION_CONFIRM_LOCATORS = [
    {"text": "确定"},
    {"description": "确定"},
]

# 检测地理位置弹窗的轮询上限（秒）
LOCATION_POPUP_TIMEOUT_SEC = 2

# 飞书启动等待时长（首页需要预加载 IM 列表，比一般 App 慢）
LARK_LAUNCH_WAIT_SEC = 5

# H5 页面加载等待时长（中智关爱、奋斗食代是嵌 H5，需要留时间加载）
H5_LOAD_WAIT_SEC = 5

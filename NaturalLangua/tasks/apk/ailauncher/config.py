# ============================================================
# 【AI 桌面 APK】config.py
# 包名与常量配置 — 换机型/版本时优先修改本文件。
# ============================================================

# 当前使用的 AI 桌面包名
PACKAGE = "com.stepos.ailauncher"

# 主桌面进入 AI 桌面的入口图标（文案/描述），按顺序匹配
ENTRY_LOCATORS = [
    {"text": "Agent空间"},
    {"description": "Agent空间"},
    {"textContains": "Agent"},
    {"text": "agent空间"},
    {"textContains": "agent"},
]

# 输入框定位器（按顺序匹配，抓到实际 resourceId 后前置）
INPUT_LOCATORS = [
    {"description": "输入框"},
    {"description": "输入"},
    {"className": "android.widget.EditText"},
]

# 发送按钮定位器（按顺序匹配；实际 App 上是「上箭头」图标）
SEND_LOCATORS = [
    {"description": "发送"},
    {"description": "send"},
    {"description": "Send"},
    {"text": "发送"},
    {"textContains": "发送"},
    {"resourceIdMatches": ".*(send|submit).*"},
]

# 发送按钮语义定位失败时的坐标兜底（按屏幕宽/高比例，1.0 = 100%）
SEND_COORD_RATIO = (0.87, 0.64)

# 右上角「+ 新建会话」按钮定位器
NEW_CHAT_LOCATORS = [
    {"description": "新建对话"},
    {"description": "新对话"},
    {"description": "新建会话"},
    {"description": "新会话"},
    {"description": "+"},
    {"descriptionContains": "新"},
    {"text": "+"},
]

# 新建会话按钮语义定位失败时的坐标兜底（截图里 + 大约在右上角）
NEW_CHAT_COORD_RATIO = (0.77, 0.09)

# 回复气泡下方的「应用」胶囊按钮定位器（点击可跳转推荐应用）
APP_BUTTON_LOCATORS = [
    {"text": "应用"},
    {"description": "应用"},
    {"textContains": "应用"},
]

# 系统/应用授权弹窗中的「允许」按钮定位器
# 顺序：优先「始终允许」（一次授权后续免打扰），其次「本次允许」，最后通用「允许」兜底
PERMISSION_ALLOW_LOCATORS = [
    {"text": "始终允许"},
    {"description": "始终允许"},
    {"textContains": "始终"},
    {"text": "本次允许"},
    {"description": "本次允许"},
    {"text": "仅本次允许"},
    {"textContains": "本次"},
    {"text": "允许"},
    {"description": "允许"},
]

# 授权弹窗轮询最长秒数（在特定 query 发送后检查是否弹出）
PERMISSION_CHECK_TIMEOUT_SEC = 5

# 需要在发送后检查授权弹窗的 query（首次触发权限的，如位置类）
# 命中列表中的 query 会在发送后轮询 PERMISSION_CHECK_TIMEOUT_SEC 秒找授权弹窗
PERMISSION_CHECK_QUERIES = [
    "搜索附近美食",
]

# 等待 AI 回复完成的最长秒数
REPLY_WAIT_SEC = 20

# 三方 APP 推荐理由批量测试的 query 列表（TC002 顺序发送、逐条断言、+ 切换会话）
RECOMMEND_QUERIES = [
    "搜索附近美食",
    "我想点一杯蜜雪冰城柠檬水，送到彩讯大厦，电话18598032267",
    "我要送合同到公司，地址彩讯大厦到深圳大学，电话18598032266",
    "我要打车到深圳北",
    "我想看下深圳到上海的飞机，请把本周六的机票列出来，找出一个最便宜的，我要乘坐最便宜的那班",
    "查询下明天下午深圳北到上海下午3点的火车票",
    "我感觉风雨无阻这首歌特别好听，我想播放这首音乐",
    "我想看短视频",
    "我想打开软件看下热搜"
]

# 三方 APP 推荐理由关键词 —— 回复中命中任一即视为出现「推荐理由」
# 参考：地图信息更准确 / 只有它能处理 / 信息覆盖面很全 / 功能服务足够便捷全面
RECOMMEND_KEYWORDS = [
    "更准确",
    "更全面",
    "更专业",
    "更便捷",
    "只有它",
    "覆盖面",
    "信息覆盖",
    "功能服务",
    "便捷全面",
    "足够便捷",
    "服务足够",
    "信息更",
    "推荐使用",
    "推荐它",
    "很能打",
    "只有它接入了推荐能力",
    "较为丰富",
    "余量合适"
]

# 常见控件 resourceId（占位，实际抓包后补齐）
COMMON_IDS: list[str] = []

# 常见控件 text / description 兜底
COMMON_TEXTS: list[str] = []

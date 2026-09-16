# APK 脚本框架说明

本项目将各 APK 的自动化脚本封装为统一框架，支持按 APK 运行全部用例，或一键按顺序执行浏览器与应用商店核心回归。

---

## 目录结构

```
NaturalLangua/
├── run_apk_tests.py          # 主入口（命令行）
├── run_core.bat              # 双击一键跑：浏览器 → 应用商店
├── tasks/
│   ├── framework/            # 框架层（基类、运行器、注册表）
│   │   ├── base_case.py      # 用例基类 ApkTestCase
│   │   ├── runner.py         # TestRunner 执行器
│   │   ├── registry.py       # APK / 套件注册
│   │   └── helpers.py        # 跨 APK 公共 UI 辅助
│   └── apk/                  # 每个 APK 一个目录
│       ├── browser/          # 手机浏览器
│       ├── app_store/        # 应用商店
│       └── douyin/           # 抖音
├── scheduler.py              # 定时任务（调用框架跑 douyin）
└── main.py                   # 自然语言交互模式（独立入口，与 APK 脚本无关）
```

每个 APK 目录内：

| 文件 | 说明 |
|------|------|
| `config.py` | 包名、测试 URL / 关键词（**换机型优先改这里**） |
| `case_*.py` | **一个文件一条用例** |
| `__init__.py` | 导出 `APK_INFO` + `CASES` 供框架注册 |
| `helpers.py` | （可选）该 APK 专用 UI 辅助函数 |

---

## 常用命令

在 `NaturalLangua` 目录下执行：

```bash
# 查看所有 APK 和用例
python run_apk_tests.py --list

# 跑单个 APK 的全部用例,cd 进 NaturalLangua 
python run_apk_tests.py --apk browser
python run_apk_tests.py --apk app_store
python run_apk_tests.py --apk douyin
python run_apk_tests.py --apk ailauncher

# 一键核心回归：浏览器 → 应用商店（按顺序）
python run_apk_tests.py --suite core

# 或双击 run_core.bat

# 跑全部已注册 APK
python run_apk_tests.py --suite all

# 只跑指定用例
python run_apk_tests.py --apk browser --case TC002_open_url TC003_search

# 指定设备序列号
python run_apk_tests.py --suite core -s 设备序列号

# 某条用例失败后停止后续用例
python run_apk_tests.py --suite core --stop-on-fail
```

### 预定义套件

| 套件名 | 执行顺序 |
|--------|----------|
| `core` | 浏览器 → 应用商店 |
| `all` | 浏览器 → 应用商店 → 抖音 → AI 桌面 |

---

## 已内置用例

### browser（手机浏览器）

| 用例 ID | 名称 | 说明 |
|---------|------|------|
| `open_browser` | 启动浏览器 | 通过包名启动，断言 App 在前台 |
| `open_url` | 打开指定网址 | 在地址栏输入测试 URL 并访问 |
| `search` | 浏览器内搜索 | 搜索关键词并验证结果页 |
| `back_forward` | 前进后退导航 | 打开网页后执行返回，验证仍在浏览器内 |

默认包名：`com.heytap.browser`

### app_store（应用商店）

| 用例 ID | 名称 | 说明 |
|---------|------|------|
| `open_store` | 启动应用商店 | 启动并验证首页已加载 |
| `search_app` | 搜索应用 | 搜索指定 App 并验证结果列表 |
| `open_detail` | 打开应用详情 | 点击第一条结果进入详情页 |
| `exit_store` | 退出应用商店 | 强制停止，断言已不在前台 |

默认包名：`com.heytap.market`  
默认搜索词：`微信`（可在 `config.py` 修改）

### douyin（抖音）

| 用例 ID | 名称 | 说明 |
|---------|------|------|
| `daily` | 抖音每日任务 | 打开 → 切换深圳同城 → 搜索 → 播放 → 退出 |

默认包名：`com.ss.android.ugc.aweme`

### ailauncher（AI 桌面）

| 用例 ID | 名称 | 说明 |
|---------|------|------|
| `TC001_open_ailauncher` | 启动 AI 桌面 | 通过包名启动，断言应用在前台 |

默认包名：`com.stepos.ailauncher`

---

## 如何新增 APK 或改包名

### 改现有 APK 包名

编辑对应目录下的 `config.py`，修改 `PACKAGE` 即可。文件中已注释常见备选包名，例如：

```python
# browser/config.py
PACKAGE = "com.heytap.browser"
# PACKAGE = "com.android.chrome"

# app_store/config.py
PACKAGE = "com.heytap.market"
# PACKAGE = "com.xiaomi.market"
```

若控件 ID 与默认不同，同步修改 `config.py` 中的 ID 列表，或在 `case_*.py` 中补充 `text` / `description` 定位兜底。

### 新增一个 APK

1. 在 `tasks/apk/` 下新建目录，例如 `tasks/apk/wechat/`
2. 创建 `config.py`（包名、常量）
3. 创建 `case_xxx.py`（每条用例一个文件，继承 `ApkTestCase`）
4. 创建 `__init__.py`，导出 `APK_INFO` 和 `CASES`：

```python
from tasks.apk.wechat.TC001_xxx import CaseXxx
from tasks.apk.wechat.config import PACKAGE

APK_INFO = {
    "apk_id": "wechat",
    "apk_name": "微信",
    "package_name": PACKAGE,
    "description": "微信核心能力说明",
}

CASES = [CaseXxx]
```

5. 在 `tasks/framework/registry.py` 的 `_load_apk_modules()` 中 import 并 append 新模块
6. （可选）在 `SUITES` 字典里把新 APK 加入某个套件

6. 运行 `python run_apk_tests.py --list` 确认注册成功

---

## 用例模板要点

每个 `case_*.py` 建议包含文件头注释（说明步骤与断言策略），用例类结构如下：

```python
# ============================================================
# 【微信 APK】case_open_chat.py
# 用例：打开指定聊天窗口
# ============================================================

from tasks.apk.wechat import config as cfg
from tasks.framework.base_case import ApkTestCase


class CaseOpenChat(ApkTestCase):
    case_id = "open_chat"       # 命令行 --case 使用的 ID，需唯一
    case_name = "打开聊天"       # 日志与报告中显示的名称
    case_desc = "从首页进入指定会话"  # --list 时展示的说明

    def run_steps(self) -> None:
        # 1. 启动 App
        self.app.launch_app(cfg.PACKAGE)
        self.wait(3)

        # 2. 执行步骤 + 断言（失败会自动截图并终止本条用例）
        self.assert_step(
            self.is_foreground(cfg.PACKAGE),
            "微信应在前台运行",
        )

        # 3. 更多步骤 …
        self.ui.click(text="文件传输助手")
        self.wait(2)
        self.assert_step(
            self.d(textContains="文件传输助手").exists,
            "应进入文件传输助手聊天页",
        )

    # 可选：用例结束清理（默认不关闭 App，便于同 APK 多条用例串联）
    def teardown(self) -> None:
        super().teardown()
        # self.app.stop_app(cfg.PACKAGE)
```

### 基类提供的便捷方法

| 方法 | 说明 |
|------|------|
| `self.setup()` | 连接设备（Runner 内 `execute()` 已自动调用） |
| `self.assert_step(条件, 消息)` | 断言，失败截图 + 日志 + 终止用例 |
| `self.wait(秒数)` | 等待页面加载 |
| `self.is_foreground(包名)` | 检查指定包是否在前台 |
| `self.d` / `self.app` / `self.ui` | u2 设备、App 控制、UI 操作 |

跨 APK 可复用 `tasks/framework/helpers.py` 中的 `click_first_match`、`dismiss_common_dialogs` 等函数。

---

## 注意事项

1. **默认包名按 OPPO / HeyTap 配置**  
   浏览器 `com.heytap.browser`，应用商店 `com.heytap.market`。vivo、小米、华为等机型请改对应 `config.py` 中的 `PACKAGE` 和控件 ID。

2. **运行前准备**  
   - 手机开启 USB 调试并连接电脑  
   - 已安装依赖：`pip install -r requirements.txt`  
   - 建议先执行：`python -m uiautomator2 init`  
   - 一键自检：`python check_env.py`（或 `python check_env.py --quiet` 只看异常）

3. **首次使用建议**  
   先 `python run_apk_tests.py --list` 确认用例列表，再 `python run_apk_tests.py --suite core` 做整体验证。

4. **多设备**  
   使用 `-s 设备序列号` 指定 ADB serial；不指定时自动连接第一台设备。

5. **断言与截图**  
   断言失败会自动截图到 `screenshots/`，日志写入 `logs/`。

6. **定时任务**  
   - `python scheduler.py --apk <APK_ID> --at HH:MM` 每天在指定时间自动跑该 APK 用例（可传多次 `--at` 支持多时间点）  
     示例：`python scheduler.py --apk lark --at 20:35`（每天 20:35 领取中智关爱）  
     示例：`python scheduler.py --apk ailauncher --at 09:00 --at 21:00`（早晚各跑一次）  
   - 可加 `--case <ID>` 只跑指定用例、`-s <SERIAL>` 指定设备  
   - 手动执行统一使用 `run_apk_tests.py`

7. **套件顺序**  
   `core` 套件先跑浏览器再跑应用商店；如需调整顺序，修改 `tasks/framework/registry.py` 中 `SUITES["core"]` 的 APK ID 列表。

8. **Windows 控制台**  
   若中文乱码，可在终端执行 `chcp 65001` 切换 UTF-8，或使用 Cursor / VS Code 集成终端。

---

## Allure 测试报告

框架已内置 Allure 集成，每次运行会把结果写到 `allure-results/`，可生成美观的可视化报告（含步骤、截图、失败堆栈、历史趋势）。

> **allure-results 里为什么是 JSON？** JSON 是中间格式，需要工具把它渲染成 HTML。
> 项目提供两种渲染方式，任选其一：
> - **内置 Python 渲染器（推荐）**：零依赖，一条命令出 HTML，见下方"简易 HTML 报告"
> - **官方 Allure CLI（功能全）**：需装 Java 版工具，见"官方 Allure 报告"

### 简易 HTML 报告（推荐，无需装任何东西）

**默认行为**：`run_apk_tests.py` / `scheduler.py` 每次跑完会自动生成一份 HTML 报告：

- 输出目录：`allure-results/report/`（跟随结果目录，方便整体归档）
- 文件名规则：`report_<应用标识>_<YYYYMMDD_HHMM>.html`
- 例如：`allure-results/report/report_ailauncher_20260916_1608.html`、
  `allure-results/report/report_suite-core_20260916_1608.html`
- 每次运行都是**独立文件**，不覆盖历史，方便回看不同批次的对比
- 定时任务同理，每次触发生成新文件

**飞书通知**：若配置了 `.env` 里的 FEISHU_*，跑完发的卡片底部会带上这份 HTML 的绝对路径 + `file://` 链接，接收方若与执行机同机（或能访问该路径），可以直接复制到浏览器打开报告。

`gen_report.py` 把 `allure-results/*.json` 直接渲染成一个自包含的 HTML：

```bash
# 跑完自动生成（默认行为，什么都不用加）
python run_apk_tests.py --apk ailauncher
# → 生成 allure-results/report/report_ailauncher_<时间>.html

python run_apk_tests.py --suite core
# → 生成 allure-results/report/report_suite-core_<时间>.html

# 跑完顺便打开浏览器
python run_apk_tests.py --apk ailauncher --open-report

# 不想要 HTML 报告（比如 CI 里）
python run_apk_tests.py --apk ailauncher --no-report

# 手动只生成报告（不跑用例）
python gen_report.py --label ailauncher --open   # 带标识 + 时间戳 + 打开
python gen_report.py --out custom.html           # 完全指定输出路径
python gen_report.py                             # 不带 label 时输出到 allure-results/report/report.html
python gen_report.py --no-embed                  # 不嵌入图片（HTML 更小但需保留 allure-results/）

# 双击一键出报告 + 打开
NaturalLangua\gen_report.bat
```

HTML 里可以看到：汇总卡片（点击可过滤 通过/失败/异常）、按 APK 分组的用例、每条用例展开看步骤/截图/错误堆栈、环境信息。图片默认 base64 内嵌，一个 HTML 文件即可分享给别人。

局限：**没有**历史趋势、分类统计图、复杂过滤。想要这些请装官方 CLI。

### 官方 Allure 报告（功能完整）

一次性准备：

1. 到 https://github.com/allure-framework/allure2/releases 下载最新的 `allure-x.x.x.zip`
2. 解压到任意目录，例如 `D:\tools\allure-2.30.0`
3. 把 `D:\tools\allure-2.30.0\bin` 加入系统 `PATH`
4. 打开新终端验证：`allure --version` 输出版本号即可（需 Java 8+）

生成 & 查看：

```bash
python run_apk_tests.py --suite core --allure-serve       # 跑完自动 serve
python run_apk_tests.py --suite core --allure-generate    # 生成 allure-report/ 静态目录
# 双击：allure_serve.bat / allure_report.bat
```

### CLI 选项一览

| 选项 | 说明 |
|------|------|
| `--allure-dir <DIR>` | 自定义结果目录，默认 `<项目>/allure-results` |
| `--allure-append` | 追加模式，不清空结果目录（可累积多次运行） |
| `--no-allure` | 关闭 Allure 结果输出 |
| `--no-report` | 不生成 `report.html`（默认每次跑完都会生成） |
| `--open-report` | 生成 `report.html` 后自动打开浏览器 |
| `--allure-serve` | 结束后自动 `allure serve`（需 Allure CLI） |
| `--allure-generate` | 结束后自动生成 `allure-report/` 静态目录（需 Allure CLI） |

### 用例侧可选增强

现有用例**无需改动**，Allure 会自动记录每条用例、每次 `self.assert_step` 和失败截图。若想让报告步骤更清晰，可在用例里显式包裹步骤：

```python
def run_steps(self) -> None:
    with self.step("启动 App"):
        self.app.launch_app(cfg.PACKAGE)
        self.wait(3)

    with self.step("打开首页并断言"):
        self.assert_step(self.is_foreground(cfg.PACKAGE), "App 应在前台")

    with self.step("附加运行时数据"):
        self.attach_text("响应内容示例\n...", name="LLM 回复")
        # 主动截图并挂到 Allure（不涉及断言）
        self.snapshot(name="推荐结果页")
```

- `self.step(name)` — 显式步骤区块，报告里可展开
- `self.attach(path, name=...)` — 挂文件（截图、日志片段等）
- `self.attach_text(text, name=...)` — 挂一段纯文本
- `self.snapshot(name=...)` — 主动截图并挂到 Allure

### 定时任务的 Allure

`scheduler.py` 也支持 Allure，默认**追加模式**（每次触发不清空，累积历史）：

```bash
python scheduler.py --apk lark --at 20:35
# 想关掉 Allure：
python scheduler.py --apk lark --at 20:35 --no-allure
```

跑一段时间后执行 `allure_report.bat`，即可看到定时任务的历史趋势曲线。

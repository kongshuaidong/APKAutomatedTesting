#!/usr/bin/env python3
# ============================================================
# 【环境自检】check_env.py
# 一键检测运行 APK 自动化测试所需的全部环境。
#
# 用法：
#   cd NaturalLangua
#   python check_env.py                 # 打印所有检查结果
#   python check_env.py --quiet         # 只打印异常项
#   python check_env.py --json          # 机器可读输出
#
# 退出码：
#   0 = 全部 OK / 只有 WARN
#   1 = 存在 FAIL（缺关键依赖或设备）
# ============================================================

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Callable, List, Optional

from rich.console import Console
from rich.table import Table


ROOT = os.path.dirname(os.path.abspath(__file__))
console = Console()


# ── 检查结果模型 ─────────────────────────────────────────────
@dataclass
class CheckResult:
    name: str
    status: str          # "OK" / "WARN" / "FAIL"
    detail: str = ""
    fix: str = ""        # 修复建议

    @property
    def emoji(self) -> str:
        return {"OK": "✅", "WARN": "⚠️ ", "FAIL": "❌"}.get(self.status, "?")

    @property
    def color(self) -> str:
        return {"OK": "green", "WARN": "yellow", "FAIL": "red"}.get(self.status, "white")


# ── 单项检查函数 ─────────────────────────────────────────────
REQUIRED_PY = (3, 9)


def check_python() -> CheckResult:
    v = sys.version_info
    detail = f"{v.major}.{v.minor}.{v.micro} ({platform.python_implementation()})"
    if (v.major, v.minor) < REQUIRED_PY:
        return CheckResult(
            "Python 版本",
            "FAIL",
            detail,
            f"框架需要 Python {REQUIRED_PY[0]}.{REQUIRED_PY[1]}+，请升级",
        )
    return CheckResult("Python 版本", "OK", detail)


REQUIRED_PKGS = [
    ("uiautomator2", "uiautomator2"),
    ("adbutils", "adbutils"),
    ("openai", "openai"),
    ("dotenv", "python-dotenv"),
    ("loguru", "loguru"),
    ("PIL", "Pillow"),
    ("rich", "rich"),
    ("schedule", "schedule"),
    ("requests", "requests"),
]


def check_python_packages() -> List[CheckResult]:
    results: List[CheckResult] = []
    missing: List[str] = []
    for mod, pip_name in REQUIRED_PKGS:
        try:
            importlib.import_module(mod)
            results.append(CheckResult(f"pip: {pip_name}", "OK", "已安装"))
        except ImportError:
            missing.append(pip_name)
            results.append(
                CheckResult(
                    f"pip: {pip_name}",
                    "FAIL",
                    "未安装",
                    f"执行：pip install {pip_name}",
                )
            )
    if missing:
        results.append(
            CheckResult(
                "pip: 一键补齐",
                "WARN",
                f"缺少 {len(missing)} 个包",
                "执行：pip install -r requirements.txt",
            )
        )
    return results


def _run_cmd(cmd: List[str], timeout: int = 8) -> tuple[int, str]:
    """执行命令，返回 (returncode, output)。失败/超时返回 (-1, error_msg)。"""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except FileNotFoundError:
        return -1, f"未找到命令: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -1, f"命令超时: {' '.join(cmd)}"
    except Exception as e:  # noqa: BLE001
        return -1, f"执行失败: {e}"


def check_adb() -> List[CheckResult]:
    results: List[CheckResult] = []
    exe = shutil.which("adb")
    if not exe:
        results.append(
            CheckResult(
                "adb 命令",
                "FAIL",
                "未在 PATH 中找到 adb",
                "安装 Android Platform-Tools 并把 platform-tools/ 加入 PATH",
            )
        )
        return results

    rc, out = _run_cmd([exe, "version"])
    ver_line = out.strip().splitlines()[0] if out.strip() else ""
    results.append(CheckResult("adb 命令", "OK", ver_line or exe))

    rc, out = _run_cmd([exe, "devices"])
    if rc != 0:
        results.append(
            CheckResult("adb 设备", "FAIL", out.strip(), "检查 USB 线 / 授权 / 驱动")
        )
        return results

    devices = []
    for line in out.splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append((parts[0], parts[1]))

    ready = [d for d in devices if d[1] == "device"]
    unauthorized = [d for d in devices if d[1] == "unauthorized"]
    offline = [d for d in devices if d[1] == "offline"]

    if ready:
        detail = ", ".join(f"{s}" for s, _ in ready)
        results.append(CheckResult("adb 设备", "OK", f"已连接 {len(ready)} 台：{detail}"))
    elif unauthorized:
        results.append(
            CheckResult(
                "adb 设备",
                "FAIL",
                f"设备未授权：{[s for s, _ in unauthorized]}",
                "在手机上勾选「始终允许」USB 调试授权",
            )
        )
    elif offline:
        results.append(
            CheckResult(
                "adb 设备",
                "FAIL",
                f"设备离线：{[s for s, _ in offline]}",
                "拔掉重插 USB，或执行 `adb kill-server && adb start-server`",
            )
        )
    else:
        results.append(
            CheckResult(
                "adb 设备",
                "FAIL",
                "无已连接设备",
                "手机开启 USB 调试并连接电脑，执行 `adb devices` 应看到设备",
            )
        )
    return results


def check_uiautomator2() -> Optional[CheckResult]:
    """检查已连接设备上 atx-agent 是否 init 过。仅在能 import uiautomator2 且有设备时才跑。"""
    try:
        import uiautomator2 as u2  # noqa: F401
    except ImportError:
        return None

    adb = shutil.which("adb")
    if not adb:
        return None
    rc, out = _run_cmd([adb, "shell", "pm", "path", "com.github.uiautomator"], timeout=5)
    if rc == 0 and "package:" in out:
        return CheckResult("uiautomator2 初始化", "OK", "atx-agent 已安装")
    if rc == 0:  # 命令成功但无输出，说明未装
        return CheckResult(
            "uiautomator2 初始化",
            "WARN",
            "atx-agent 未安装",
            "执行：python -m uiautomator2 init",
        )
    # 没设备时命令会失败，跳过
    return None


def check_java() -> CheckResult:
    exe = shutil.which("java")
    if not exe:
        return CheckResult(
            "Java 运行时",
            "WARN",
            "未找到 java（Allure CLI 依赖）",
            "只跑用例可忽略；要看报告需装 JRE 8+",
        )
    rc, out = _run_cmd([exe, "-version"])
    ver_line = out.strip().splitlines()[0] if out.strip() else ""
    return CheckResult("Java 运行时", "OK", ver_line)


def check_allure_cli() -> CheckResult:
    exe = shutil.which("allure") or shutil.which("allure.bat")
    if not exe:
        return CheckResult(
            "Allure CLI",
            "WARN",
            "未找到 allure 命令",
            "只跑用例可忽略；要看报告到 "
            "https://github.com/allure-framework/allure2/releases 下载并加入 PATH",
        )
    rc, out = _run_cmd([exe, "--version"])
    ver = out.strip().splitlines()[0] if out.strip() else "?"
    return CheckResult("Allure CLI", "OK", f"v{ver}")


def check_project_dirs() -> List[CheckResult]:
    results: List[CheckResult] = []
    for sub in ("logs", "screenshots", "allure-results"):
        path = os.path.join(ROOT, sub)
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_probe")
        try:
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            results.append(CheckResult(f"目录: {sub}/", "OK", path))
        except OSError as e:
            results.append(
                CheckResult(
                    f"目录: {sub}/",
                    "FAIL",
                    f"不可写：{e}",
                    "检查磁盘权限或手动创建目录",
                )
            )
    return results


def check_env_file() -> CheckResult:
    """检查 .env 里的飞书 / OpenAI 配置。全都缺不算 FAIL，只提示。"""
    env_path = os.path.join(ROOT, ".env")
    keys = [
        "OPENAI_API_KEY",
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_RECEIVE_ID",
    ]
    have: List[str] = []
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        for k in keys:
            for line in content.splitlines():
                line = line.strip()
                if line.startswith(k + "=") and line.split("=", 1)[1].strip():
                    have.append(k)
                    break
    # 再从环境变量兜底
    for k in keys:
        if k not in have and os.getenv(k):
            have.append(k)

    if not have:
        return CheckResult(
            ".env 配置",
            "WARN",
            "OPENAI / FEISHU 变量均未配置",
            "非必需；要用 LLM 或飞书通知则参考 config.py 头部注释配置 .env",
        )
    missing = [k for k in keys if k not in have]
    if missing:
        return CheckResult(
            ".env 配置",
            "WARN",
            f"已配置 {have}，缺 {missing}",
            "按需配置，未使用的功能可忽略",
        )
    return CheckResult(".env 配置", "OK", f"已配置 {have}")


def check_framework_import() -> CheckResult:
    """真的能 import 框架吗？"""
    sys.path.insert(0, ROOT)
    try:
        from tasks.framework.registry import get_apk_modules  # noqa
        from tasks.framework.runner import TestRunner  # noqa
        from utils.allure_reporter import AllureReporter  # noqa

        modules = get_apk_modules()
        return CheckResult(
            "框架自检",
            "OK",
            f"已注册 {len(modules)} 个 APK, "
            f"{sum(len(m.case_classes) for m in modules)} 条用例",
        )
    except Exception as e:  # noqa: BLE001
        return CheckResult(
            "框架自检",
            "FAIL",
            f"import 失败：{type(e).__name__}: {e}",
            "先解决 pip 依赖缺失，再重试",
        )


def check_platform() -> CheckResult:
    return CheckResult(
        "操作系统",
        "OK",
        f"{platform.system()} {platform.release()} ({platform.machine()}) · host={socket.gethostname()}",
    )


# ── 汇总入口 ─────────────────────────────────────────────────
def run_all_checks() -> List[CheckResult]:
    results: List[CheckResult] = []
    results.append(check_platform())
    results.append(check_python())
    results.extend(check_python_packages())
    results.append(check_framework_import())
    results.extend(check_adb())
    ua = check_uiautomator2()
    if ua is not None:
        results.append(ua)
    results.append(check_java())
    results.append(check_allure_cli())
    results.extend(check_project_dirs())
    results.append(check_env_file())
    return results


def print_table(results: List[CheckResult], quiet: bool) -> None:
    table = Table(
        title="APK 自动化 · 环境自检",
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("", width=2)
    table.add_column("检查项", style="bold")
    table.add_column("状态", justify="center")
    table.add_column("详情", overflow="fold")
    table.add_column("修复建议", overflow="fold", style="dim")

    for r in results:
        if quiet and r.status == "OK":
            continue
        table.add_row(
            r.emoji,
            r.name,
            f"[{r.color}]{r.status}[/{r.color}]",
            r.detail,
            r.fix,
        )
    console.print(table)


def print_summary(results: List[CheckResult]) -> int:
    ok = sum(1 for r in results if r.status == "OK")
    warn = sum(1 for r in results if r.status == "WARN")
    fail = sum(1 for r in results if r.status == "FAIL")

    if fail:
        color = "red"
        headline = "存在关键问题，无法正常跑用例"
    elif warn:
        color = "yellow"
        headline = "基础功能可用，部分能力受限（见 WARN 项）"
    else:
        color = "green"
        headline = "全部通过，环境就绪！"

    console.print()
    console.print(
        f"[{color}]{headline}[/{color}]  ·  "
        f"OK={ok}  WARN={warn}  FAIL={fail}"
    )
    if fail == 0:
        console.print("[dim]下一步：python run_apk_tests.py --list[/dim]")
    return 1 if fail > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="APK 自动化框架环境自检",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="只显示 WARN/FAIL 项")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出（供脚本消费）")
    args = parser.parse_args()

    results = run_all_checks()

    if args.json:
        payload = {
            "results": [asdict(r) for r in results],
            "summary": {
                "ok": sum(1 for r in results if r.status == "OK"),
                "warn": sum(1 for r in results if r.status == "WARN"),
                "fail": sum(1 for r in results if r.status == "FAIL"),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if payload["summary"]["fail"] > 0 else 0

    print_table(results, quiet=args.quiet)
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())

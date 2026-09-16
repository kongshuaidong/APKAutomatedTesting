#!/usr/bin/env python3
# ============================================================
# 【CLI 入口】run_apk_tests.py
# APK 自动化脚本框架 — 一键运行用例（含 Allure 报告）
#
# 常用命令：
#   python run_apk_tests.py --list                     # 列出 APK 与用例
#   python run_apk_tests.py --apk browser              # 跑浏览器全部用例
#   python run_apk_tests.py --apk app_store            # 跑应用商店全部用例
#   python run_apk_tests.py --suite core               # 浏览器 → 应用商店（核心回归）
#   python run_apk_tests.py --suite all                # 全部 APK
#   python run_apk_tests.py --apk browser --case TC002_open_url TC003_search
#   python run_apk_tests.py --suite core -s ABC123     # 指定设备序列号
#   python run_apk_tests.py --suite core --stop-on-fail
#
# Allure 相关：
#   默认结果写到 <project>/allure-results，每次跑之前会自动清空
#   --allure-dir <path>    自定义结果目录
#   --allure-append        追加模式，不清空结果目录（用于合并多次运行）
#   --no-allure            关闭 Allure（不写任何结果）
#   --allure-serve         结束后自动执行 `allure serve`（需先装 allure CLI）
#   --allure-generate      结束后自动生成静态报告到 allure-report/
#
# 目录结构：
#   tasks/framework/     框架（基类、运行器、注册表）
#   tasks/apk/browser/   浏览器用例（每文件一条）
#   tasks/apk/app_store/ 应用商店用例
#   tasks/apk/douyin/    抖音用例
# ============================================================

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time

# 保证从 NaturalLangua 根目录可导入
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tasks.framework.registry import SUITES, get_apk_module, get_apk_modules, list_suite_names
from tasks.framework.runner import TestRunner
from utils.allure_reporter import AllureReporter
from utils.feishu_notifier import notify_report
from utils.logger import logger

# 复用 gen_report 的路径规则，避免两处推算
from gen_report import default_report_path


DEFAULT_ALLURE_DIR = os.path.join(ROOT, "allure-results")
DEFAULT_REPORT_DIR = os.path.join(ROOT, "allure-report")


def _print_list() -> None:
    print("\n=== 已注册 APK ===")
    for module in get_apk_modules():
        print(f"\n  [{module.apk_id}] {module.apk_name}")
        print(f"    包名: {module.package_name}")
        if module.description:
            print(f"    说明: {module.description}")
        print("    用例:")
        for cls in module.case_classes:
            desc = f" — {cls.case_desc}" if cls.case_desc else ""
            print(f"      - {cls.case_id:16} {cls.case_name}{desc}")

    print("\n=== 预定义套件 ===")
    for name, apk_ids in SUITES.items():
        labels = []
        for aid in apk_ids:
            try:
                labels.append(get_apk_module(aid).apk_name)
            except KeyError:
                labels.append(aid)
        print(f"  [{name}] {' -> '.join(labels)}")

    print("\n示例:")
    print("  python run_apk_tests.py --suite core")
    print("  python run_apk_tests.py --apk browser")
    print("  python run_apk_tests.py --apk browser --allure-serve")
    print()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="APK 自动化脚本框架 — 按 APK 或套件运行用例",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="修改包名/关键词请编辑 tasks/apk/<apk_id>/config.py",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有 APK、用例与套件",
    )
    group.add_argument(
        "--apk", "-a",
        metavar="APK_ID",
        help="运行指定 APK 的全部用例，如 browser / app_store / douyin",
    )
    group.add_argument(
        "--suite", "-S",
        metavar="SUITE",
        choices=list_suite_names(),
        help=f"按套件顺序运行，可选: {', '.join(list_suite_names())}",
    )

    parser.add_argument(
        "--case", "-c",
        nargs="+",
        metavar="CASE_ID",
        help="只运行指定用例 ID（与 --apk 或 --suite 配合）",
    )
    parser.add_argument(
        "--device", "-s",
        metavar="SERIAL",
        default=None,
        help="ADB 设备序列号，默认自动选第一台",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="某条用例失败后停止后续用例",
    )

    # ── Allure 选项 ─────────────────────────────────────────
    allure_group = parser.add_argument_group("Allure 报告选项")
    allure_group.add_argument(
        "--allure-dir",
        metavar="DIR",
        default=DEFAULT_ALLURE_DIR,
        help=f"Allure 结果目录（默认 {DEFAULT_ALLURE_DIR}）",
    )
    allure_group.add_argument(
        "--allure-append",
        action="store_true",
        help="追加模式：本次运行不清空 --allure-dir",
    )
    allure_group.add_argument(
        "--no-allure",
        action="store_true",
        help="关闭 Allure 结果输出（此次运行完全不写 allure-results）",
    )
    allure_group.add_argument(
        "--allure-serve",
        action="store_true",
        help="结束后自动运行 `allure serve` 打开浏览器预览（需已安装 allure CLI）",
    )
    allure_group.add_argument(
        "--allure-generate",
        action="store_true",
        help=f"结束后生成静态 HTML 报告到 {DEFAULT_REPORT_DIR}",
    )
    allure_group.add_argument(
        "--no-report",
        action="store_true",
        help="不生成 report.html（默认每次跑完都会生成）",
    )
    allure_group.add_argument(
        "--open-report",
        action="store_true",
        help="生成 report.html 后自动用默认浏览器打开",
    )
    return parser


def _build_reporter(args, device_serial: str) -> AllureReporter | None:
    """构造 Allure reporter，写环境信息与分类。"""
    if args.no_allure:
        return None

    reporter = AllureReporter(args.allure_dir)
    if not args.allure_append:
        reporter.clean()

    reporter.write_environment(
        {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "device": device_serial or "(auto)",
            "framework": "APKAutomatedTesting",
            "run_mode": ("suite:" + args.suite) if args.suite else ("apk:" + args.apk),
        }
    )
    reporter.write_categories()
    reporter.write_executor(
        {
            "name": "APK Runner",
            "type": "custom",
            "reportName": "APK 自动化测试报告",
        }
    )
    return reporter


def _run_allure_cli(sub_cmd: list[str]) -> int:
    """
    调用 allure CLI，找不到时给出提示并返回非零码。
    Windows 下常见路径：pip 装的是 allure-python-commons，不带 CLI；
    需要额外安装 https://github.com/allure-framework/allure2/releases 并加入 PATH。
    """
    exe = shutil.which("allure") or shutil.which("allure.bat")
    if not exe:
        logger.warning(
            "未在 PATH 中找到 `allure` 命令。"
            "请从 https://github.com/allure-framework/allure2/releases 下载并加入 PATH。"
        )
        return 1
    logger.info(f"执行：{exe} {' '.join(sub_cmd)}")
    try:
        return subprocess.call([exe] + sub_cmd)
    except OSError as e:
        logger.warning(f"调用 allure 失败：{e}")
        return 1


def _post_allure_actions(args, html_report_path: str = "") -> None:
    """
    HTML 报告已由 main() 提前生成（因为路径要给飞书通知用），这里只处理
    Allure CLI 相关的可选步骤：generate 静态目录 / serve 预览。
    """
    if args.no_allure:
        return
    if args.allure_generate:
        _run_allure_cli(
            [
                "generate",
                args.allure_dir,
                "-o",
                DEFAULT_REPORT_DIR,
                "--clean",
            ]
        )
        logger.info(f"报告已生成：{DEFAULT_REPORT_DIR} — 双击 index.html 可离线查看")
    if args.allure_serve:
        _run_allure_cli(["serve", args.allure_dir])


def _run_simple_report(args, out_path: str) -> bool:
    """
    调内置 gen_report.py 生成自包含 HTML。
    out_path 由调用方预先算好并传入，方便同一路径同时给飞书通知使用。
    """
    cmd = [
        sys.executable,
        os.path.join(ROOT, "gen_report.py"),
        "--results",
        args.allure_dir,
        "--out",
        out_path,
    ]
    if args.open_report:
        cmd.append("--open")
    try:
        rc = subprocess.call(cmd)
    except OSError as e:
        logger.warning(f"生成 HTML 报告失败：{e}")
        return False
    if rc != 0:
        logger.warning(f"HTML 报告生成失败，退出码 {rc}")
        return False
    return True


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list:
        _print_list()
        return 0

    reporter = _build_reporter(args, device_serial=args.device or "")

    runner = TestRunner(
        device_serial=args.device,
        stop_on_fail=args.stop_on_fail,
        reporter=reporter,
    )

    start_time = time.time()
    if args.apk:
        logger.info(f"开始执行 APK：{args.apk}")
        report = runner.run_apk(args.apk, case_ids=args.case)
        report.print_summary()
        title = f"APK 自动化 · {args.apk}"
    elif args.suite:
        logger.info(f"开始执行套件：{args.suite}")
        report = runner.run_suite(args.suite, case_ids=args.case)
        title = f"APK 自动化 · 套件 {args.suite}"
    else:
        parser.print_help()
        return 1

    elapsed = time.time() - start_time

    if reporter is not None:
        logger.info(f"Allure 结果目录：{reporter.results_dir}")

    # 先生成 HTML 报告，这样飞书通知里可以带上其绝对路径
    html_report_path = ""
    if not args.no_allure and not args.no_report:
        label = ("suite-" + args.suite) if args.suite else args.apk
        html_report_path = default_report_path(label)
        if not _run_simple_report(args, html_report_path):
            html_report_path = ""  # 生成失败就不给飞书传路径

    # 飞书通知：未配置 env 时静默跳过，发送失败不影响返回码
    notify_report(
        title=title,
        results=report.results,
        elapsed_sec=elapsed,
        device_serial=args.device or "",
        report_path=html_report_path,
    )

    # 结束后按需生成/预览报告（Allure CLI 静态/serve 分支）
    _post_allure_actions(args, html_report_path=html_report_path)

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# ============================================================
# 【CLI 入口】run_apk_tests.py
# APK 自动化脚本框架 — 一键运行用例
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
# 目录结构：
#   tasks/framework/     框架（基类、运行器、注册表）
#   tasks/apk/browser/   浏览器用例（每文件一条）
#   tasks/apk/app_store/ 应用商店用例
#   tasks/apk/douyin/    抖音用例
# ============================================================

import argparse
import os
import sys
import time

# 保证从 NaturalLangua 根目录可导入
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tasks.framework.registry import SUITES, get_apk_module, get_apk_modules, list_suite_names
from tasks.framework.runner import TestRunner
from utils.feishu_notifier import notify_report
from utils.logger import logger


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
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list:
        _print_list()
        return 0

    runner = TestRunner(
        device_serial=args.device,
        stop_on_fail=args.stop_on_fail,
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

    # 飞书通知：未配置 env 时静默跳过，发送失败不影响返回码
    notify_report(
        title=title,
        results=report.results,
        elapsed_sec=elapsed,
        device_serial=args.device or "",
    )

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

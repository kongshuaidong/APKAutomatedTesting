"""
定时任务调度器：按 APK 每天定时跑用例。

运行方式：
    cd NaturalLangua

    # 每天 20:35 跑飞书全部用例（领取中智关爱）
    python scheduler.py --apk lark --at 20:35

    # 每天 09:00 跑抖音（相当于旧版行为）
    python scheduler.py --apk douyin --at 09:00

    # 多个时间点：早晚各跑一次 AI 桌面
    python scheduler.py --apk ailauncher --at 09:00 --at 21:00

    # 只跑指定用例
    python scheduler.py --apk lark --at 20:35 --case TC001_receive_zhongzhi_care

    # 指定设备
    python scheduler.py --apk lark --at 20:35 -s ABC123

保持终端开着即可，程序会在后台等待并按时触发任务；按 Ctrl+C 停止。
"""

import argparse
import os
import re
import subprocess
import sys
import time

import platform

import schedule

sys.path.insert(0, os.path.dirname(__file__))

from tasks.framework.registry import list_apk_ids
from tasks.framework.runner import TestRunner
from utils.allure_reporter import AllureReporter
from utils.feishu_notifier import notify_report
from utils.logger import logger

from gen_report import default_report_path


DEFAULT_ALLURE_DIR = os.path.join(os.path.dirname(__file__), "allure-results")


TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _valid_time(s: str) -> str:
    if not TIME_RE.match(s):
        raise argparse.ArgumentTypeError(
            f"时间格式无效: {s}（需要 24 小时制 HH:MM，如 09:30 / 20:35）"
        )
    return s


def _build_parser() -> argparse.ArgumentParser:
    apk_ids = list_apk_ids()
    parser = argparse.ArgumentParser(
        description="APK 用例定时调度器（每天固定时间自动执行）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--apk", "-a",
        required=True,
        metavar="APK_ID",
        choices=apk_ids,
        help=f"要定时执行的 APK ID，可选：{', '.join(apk_ids)}",
    )
    parser.add_argument(
        "--at",
        required=True,
        action="append",
        type=_valid_time,
        metavar="HH:MM",
        help="每天执行时间（24 小时制），可重复传入以支持多个时间点",
    )
    parser.add_argument(
        "--case", "-c",
        nargs="+",
        metavar="CASE_ID",
        help="只运行指定用例 ID（可选，多个用空格分隔）",
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
    parser.add_argument(
        "--allure-dir",
        metavar="DIR",
        default=DEFAULT_ALLURE_DIR,
        help=f"Allure 结果目录（默认 {DEFAULT_ALLURE_DIR}）；定时任务采用追加模式",
    )
    parser.add_argument(
        "--no-allure",
        action="store_true",
        help="关闭 Allure 结果输出",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="定时任务触发后不生成 report.html（默认生成）",
    )
    return parser


def _build_reporter(args) -> AllureReporter | None:
    if args.no_allure:
        return None
    reporter = AllureReporter(args.allure_dir)
    # 定时任务多次触发同一 apk，累积结果更有意义，因此不清空目录
    reporter.write_environment(
        {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "device": args.device or "(auto)",
            "framework": "APKAutomatedTesting-Scheduler",
            "apk": args.apk,
            "schedule": ",".join(sorted(set(args.at))),
        }
    )
    reporter.write_categories()
    reporter.write_executor(
        {
            "name": "APK Scheduler",
            "type": "custom",
            "reportName": f"APK 定时任务报告 · {args.apk}",
        }
    )
    return reporter


def _make_job(apk_id, case_ids, device, stop_on_fail, at, reporter, gen_report):
    def job():
        logger.info(f"定时任务触发：apk={apk_id} at={at}")
        try:
            runner = TestRunner(
                device_serial=device,
                stop_on_fail=stop_on_fail,
                reporter=reporter,
            )
            start = time.time()
            report = runner.run_apk(apk_id, case_ids=case_ids)
            report.print_summary()
            elapsed = time.time() - start

            # 先生成 HTML，让飞书通知带上路径
            html_report_path = ""
            if gen_report and reporter is not None:
                html_report_path = default_report_path(apk_id)
                if not _generate_html_report(reporter.results_dir, html_report_path):
                    html_report_path = ""

            notify_report(
                title=f"APK 定时任务 · {apk_id} @ {at}",
                results=report.results,
                elapsed_sec=elapsed,
                device_serial=device or "",
                report_path=html_report_path,
            )
            if not report.all_passed:
                logger.error(f"[{apk_id}] 定时任务未全部通过")
        except Exception as exc:
            logger.error(f"[{apk_id}] 定时任务执行异常：{exc}")
    return job


def _generate_html_report(results_dir: str, out_path: str) -> bool:
    """调 gen_report.py 出 HTML；out_path 由调用方预先算好并传入。"""
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "gen_report.py"),
        "--results",
        results_dir,
        "--out",
        out_path,
    ]
    try:
        rc = subprocess.call(cmd)
        return rc == 0
    except OSError as e:
        logger.warning(f"生成 HTML 报告失败：{e}")
        return False


def main() -> int:
    args = _build_parser().parse_args()
    times = sorted(set(args.at))

    filter_note = f"（用例过滤：{args.case}）" if args.case else ""
    device_note = f"（设备：{args.device}）" if args.device else ""
    logger.info(
        f"调度器启动：apk={args.apk} 每天在 {', '.join(times)} 执行"
        f"{filter_note}{device_note}"
    )
    logger.info("保持此窗口运行，按 Ctrl+C 可停止调度器")

    reporter = _build_reporter(args)
    if reporter is not None:
        logger.info(f"Allure 结果目录：{reporter.results_dir}（追加模式）")

    for t in times:
        job = _make_job(
            args.apk, args.case, args.device, args.stop_on_fail, t,
            reporter, gen_report=not args.no_report,
        )
        schedule.every().day.at(t).do(job)

    logger.info(f"下次执行时间：{schedule.next_run()}")

    try:
        while True:
            schedule.run_pending()
            time.sleep(20)
    except KeyboardInterrupt:
        logger.info("调度器已停止")
        return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

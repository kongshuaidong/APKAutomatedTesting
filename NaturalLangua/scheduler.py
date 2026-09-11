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
import sys
import time

import schedule

sys.path.insert(0, os.path.dirname(__file__))

from tasks.framework.registry import list_apk_ids
from tasks.framework.runner import TestRunner
from utils.feishu_notifier import notify_report
from utils.logger import logger


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
    return parser


def _make_job(apk_id, case_ids, device, stop_on_fail, at):
    def job():
        logger.info(f"定时任务触发：apk={apk_id} at={at}")
        try:
            runner = TestRunner(device_serial=device, stop_on_fail=stop_on_fail)
            start = time.time()
            report = runner.run_apk(apk_id, case_ids=case_ids)
            report.print_summary()
            elapsed = time.time() - start
            notify_report(
                title=f"APK 定时任务 · {apk_id} @ {at}",
                results=report.results,
                elapsed_sec=elapsed,
                device_serial=device or "",
            )
            if not report.all_passed:
                logger.error(f"[{apk_id}] 定时任务未全部通过")
        except Exception as exc:
            logger.error(f"[{apk_id}] 定时任务执行异常：{exc}")
    return job


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

    for t in times:
        job = _make_job(args.apk, args.case, args.device, args.stop_on_fail, t)
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

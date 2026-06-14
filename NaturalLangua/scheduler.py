"""
定时任务调度器
每天固定时间自动执行抖音 APK 用例（通过框架 runner 调用）。

运行方式：
    cd NaturalLangua
    python scheduler.py
保持终端开着即可，程序会在后台等待并按时触发任务。
"""

import os
import sys
import schedule
import time

sys.path.insert(0, os.path.dirname(__file__))

from tasks.framework.runner import TestRunner
from utils.logger import logger

RUN_TIME = "16:50"  # 每天执行时间（24小时制）
DOUYIN_APK_ID = "douyin"


def job():
    logger.info(f"定时任务触发（{RUN_TIME}）")
    try:
        runner = TestRunner()
        report = runner.run_apk(DOUYIN_APK_ID)
        report.print_summary()
        if not report.all_passed:
            logger.error("抖音定时任务未全部通过")
    except Exception as e:
        logger.error(f"定时任务执行异常：{e}")


def main():
    logger.info(f"定时调度器已启动，任务将在每天 {RUN_TIME} 执行")
    logger.info("保持此窗口运行，按 Ctrl+C 可停止调度器")

    schedule.every().day.at(RUN_TIME).do(job)

    next_run = schedule.next_run()
    logger.info(f"下次执行时间：{next_run}")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()

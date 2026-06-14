# ============================================================
# 【设备层】exception_handler.py
# 职责：统一处理自动化执行过程中的异常
#   1. 用 Loguru 记录完整错误信息和堆栈到日志文件
#   2. 自动截图保存现场，方便事后排查问题
# ============================================================

import os
import traceback
from datetime import datetime

from utils.logger import logger
from config import SCREENSHOT_DIR


class ExceptionHandler:
    """异常处理器：出错时自动截图 + 记录日志"""

    def __init__(self, ui_automator=None):
        # 传入 UIAutomator 实例才能截图；不传则只记录日志
        self.ui_automator = ui_automator

    def handle(self, exc: Exception, context: str = "") -> dict:
        """
        处理一个异常：
        1. 用 logger.error 记录错误类型和消息（写入日志文件）
        2. 用 logger.debug 记录完整堆栈信息（仅写文件，不打印到控制台）
        3. 如果 UIAutomator 可用，立刻截图保存到 screenshots/ 目录

        返回包含错误详情的字典，供调用方判断是否需要重试或上报。
        """
        tb = traceback.format_exc()         # 获取完整的错误堆栈字符串
        label = f" [{context}]" if context else ""

        # 错误日志：同时输出到控制台（红色）和日志文件
        logger.error(f"Exception{label}: {type(exc).__name__}: {exc}")
        logger.debug(tb)                    # 详细堆栈只写文件，不打印到控制台

        # 异常截图：保存当前手机屏幕画面，文件名带时间戳便于区分
        screenshot_path = None
        if self.ui_automator:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"error_{timestamp}.png")
            try:
                self.ui_automator.screenshot(screenshot_path)
                logger.info(f"Error screenshot saved: {screenshot_path}")
            except Exception as snap_err:
                # 截图本身也失败时（如设备断连），降级为仅记录日志
                logger.warning(f"Could not take error screenshot: {snap_err}")
                screenshot_path = None

        # 返回结构化错误信息，供上层（ActionExecutor）回传给 LLM 或展示给用户
        return {
            "error":      str(exc),
            "type":       type(exc).__name__,
            "context":    context,
            "screenshot": screenshot_path,  # None 表示截图失败
            "traceback":  tb,
        }

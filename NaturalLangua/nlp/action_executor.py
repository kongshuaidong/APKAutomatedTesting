# ============================================================
# 【NLP 层】action_executor.py
# 职责：接收 CommandParser 解析出的动作列表，逐条调用 UIAutomator 执行
#
# 设计要点：
#   - 动作名称（字符串）→ 处理函数（方法）的映射通过字典实现，易于扩展
#   - 每条动作独立 try/except，单步失败不影响后续步骤
#   - 执行结果（成功/失败消息）回传给 CommandParser，形成多轮对话闭环
# ============================================================

import os
from datetime import datetime

from utils.logger import logger
from config import SCREENSHOT_DIR
from core.exception_handler import ExceptionHandler


class ActionExecutor:
    """动作执行器：将 LLM 解析出的动作列表翻译成实际的手机操作"""

    def __init__(self, app_controller, ui_automator):
        self.app = app_controller           # App 启停控制
        self.ui = ui_automator              # UI 操作（点击/输入/滑动等）
        self.exc_handler = ExceptionHandler(ui_automator)   # 异常处理（截图+日志）

    def execute(self, actions: list[dict]) -> list[dict]:
        """
        顺序执行动作列表，收集每步的执行结果。
        返回结果列表会被回传给 LLM，让模型了解执行情况。
        """
        results = []
        for action in actions:
            results.append(self._execute_one(action))
        return results

    def _execute_one(self, action: dict) -> dict:
        """
        执行单个动作并捕获异常。
        - 成功：返回 "OK: <描述>"
        - 失败：调用 ExceptionHandler 截图+记录日志，返回 "ERROR: <原因>"
        """
        func_name = action["function"]
        args = action.get("args", {})
        tool_call_id = action.get("tool_call_id", "")

        logger.info(f"Executing: {func_name}({args})")
        try:
            message = self._dispatch(func_name, args)
            return {"tool_call_id": tool_call_id, "content": f"OK: {message}"}
        except Exception as exc:
            info = self.exc_handler.handle(exc, context=func_name)
            return {
                "tool_call_id": tool_call_id,
                "content": f"ERROR [{func_name}]: {info['error']}",
            }

    def _dispatch(self, func_name: str, args: dict) -> str:
        """
        根据动作名称找到对应的处理方法并调用（策略模式）。
        新增动作只需在 handlers 字典里加一行，无需修改其他逻辑。
        """
        handlers = {
            "launch_app":       self._launch_app,
            "stop_app":         self._stop_app,
            "click":            self._click,
            "long_click":       self._long_click,
            "input_text":       self._input_text,
            "swipe":            self._swipe,
            "scroll":           self._scroll,
            "back":             self._back,
            "home":             self._home,
            "screenshot":       self._screenshot,
            "wait":             self._wait,
            "wait_for_element": self._wait_for_element,
        }
        handler = handlers.get(func_name)
        if handler is None:
            raise ValueError(f"Unknown action: {func_name!r}")
        return handler(**args)   # 将 LLM 生成的参数字典解包传入

    # ------------------------------------------------------------------ #
    #  各动作的具体实现（薄封装，直接转发给 app/ui 层）
    # ------------------------------------------------------------------ #

    def _launch_app(self, package_name: str, activity: str = None) -> str:
        self.app.launch_app(package_name, activity=activity)
        return f"Launched {package_name}"

    def _stop_app(self, package_name: str) -> str:
        self.app.stop_app(package_name)
        return f"Stopped {package_name}"

    def _click(
        self,
        x: float = None,
        y: float = None,
        text: str = None,
        resource_id: str = None,
        description: str = None,
        timeout: float = 10,
    ) -> str:
        self.ui.click(
            x=x, y=y, text=text,
            resource_id=resource_id,
            description=description,
            timeout=timeout,
        )
        locator = text or resource_id or description or f"({x},{y})"
        return f"Clicked {locator!r}"

    def _long_click(
        self,
        x: float = None,
        y: float = None,
        text: str = None,
        duration: float = 0.5,
    ) -> str:
        self.ui.long_click(x=x, y=y, text=text, duration=duration)
        return "Long-clicked"

    def _input_text(self, text: str, clear_first: bool = False) -> str:
        if clear_first:
            self.ui.clear_and_input(text)
        else:
            self.ui.input_text(text)
        return f"Typed {text!r}"

    def _swipe(self, direction: str, duration: float = 0.5) -> str:
        self.ui.swipe(direction, duration=duration)
        return f"Swiped {direction}"

    def _scroll(self, direction: str = "down") -> str:
        self.ui.scroll(direction)
        return f"Scrolled {direction}"

    def _back(self) -> str:
        self.ui.back()
        return "Back button pressed"

    def _home(self) -> str:
        self.ui.home()
        return "Home button pressed"

    def _screenshot(self) -> str:
        # 文件名带时间戳，避免同名覆盖
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOT_DIR, f"screenshot_{timestamp}.png")
        self.ui.screenshot(path)
        return f"Screenshot saved to {path}"

    def _wait(self, seconds: float) -> str:
        self.ui.wait(seconds)
        return f"Waited {seconds}s"

    def _wait_for_element(
        self,
        text: str = None,
        resource_id: str = None,
        description: str = None,
        timeout: float = 10,
    ) -> str:
        found = self.ui.wait_for_element(
            text=text,
            resource_id=resource_id,
            description=description,
            timeout=timeout,
        )
        locator = text or resource_id or description or "?"
        status = "appeared" if found else "NOT found (timed out)"
        return f"Element {locator!r} {status}"

    def take_screenshot(self) -> str:
        """供主程序手动调用的截图快捷方法"""
        return self._screenshot()

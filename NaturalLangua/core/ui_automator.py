# ============================================================
# 【自动化层】ui_automator.py
# 职责：封装所有手机屏幕操作（点击、滑动、输入、截图等）
# 依赖库：uiautomator2
#   - 底层原理：在手机上部署 UIAutomator2 服务（一个 APK），
#     PC 通过 HTTP/ADB 向该服务发送操作指令
#   - 元素定位方式：text（文字）/ resourceId（控件ID）/
#     description（无障碍描述）/ 坐标(x,y)
# ============================================================

import time
import uiautomator2 as u2
from utils.logger import logger


class UIAutomator:
    """手机屏幕 UI 操作封装类"""

    def __init__(self, device: u2.Device):
        self.d = device  # uiautomator2 设备实例

    # ------------------------------------------------------------------ #
    #  点击操作
    # ------------------------------------------------------------------ #

    def click(
        self,
        x: float = None,
        y: float = None,
        text: str = None,
        resource_id: str = None,
        description: str = None,
        timeout: float = 10,
    ):
        """
        点击 UI 元素，支持多种定位方式（优先用语义定位，坐标作为兜底）：
        - (x, y)：绝对坐标点击，最直接但脆弱（换手机分辨率就失效）
        - text：按控件显示文字定位，最常用、最稳定
        - resource_id：按控件 ID 定位，适合文字可能变化的场景
        - description：按无障碍描述定位，适合图标按钮（无文字）
        timeout：等待元素出现的最长时间（秒）
        """
        if x is not None and y is not None:
            logger.info(f"Clicking at ({x}, {y})")
            self.d.click(x, y)
        elif text:
            logger.info(f"Clicking element with text='{text}'")
            self.d(text=text).click(timeout=timeout)
        elif resource_id:
            logger.info(f"Clicking element with resourceId='{resource_id}'")
            self.d(resourceId=resource_id).click(timeout=timeout)
        elif description:
            logger.info(f"Clicking element with description='{description}'")
            self.d(description=description).click(timeout=timeout)
        else:
            raise ValueError("Must provide either coordinates or a locator (text/resource_id/description).")

    def long_click(
        self,
        x: float = None,
        y: float = None,
        text: str = None,
        duration: float = 0.5,
    ):
        """长按操作，duration 控制按住的时长（秒），常用于触发上下文菜单"""
        if x is not None and y is not None:
            logger.info(f"Long-clicking at ({x}, {y})")
            self.d.long_click(x, y, duration=duration)
        elif text:
            logger.info(f"Long-clicking element with text='{text}'")
            self.d(text=text).long_click()

    def double_click(self, x: float, y: float, duration: float = 0.1):
        """双击坐标点，duration 为两次点击的间隔时间"""
        logger.info(f"Double-clicking at ({x}, {y})")
        self.d.double_click(x, y, duration=duration)

    # ------------------------------------------------------------------ #
    #  滑动操作
    # ------------------------------------------------------------------ #

    def swipe(self, direction: str, duration: float = 0.5):
        """
        向指定方向滑动屏幕（模拟手指划过屏幕的动作）。
        - 起止坐标按屏幕尺寸的比例计算，适配任意分辨率
        - duration：滑动持续时间，越小越快，过快可能被识别为误触
        - 用途：切换页面、下拉刷新、上滑加载更多等
        """
        logger.info(f"Swiping {direction}")
        width, height = self.d.window_size()
        cx, cy = width // 2, height // 2

        # 各方向的起点→终点坐标（用屏幕尺寸比例表示，保证多分辨率兼容）
        vectors = {
            "up":    (cx, int(height * 0.65), cx, int(height * 0.35)),   # 手指从下往上
            "down":  (cx, int(height * 0.35), cx, int(height * 0.65)),   # 手指从上往下
            "left":  (int(width * 0.65), cy, int(width * 0.35), cy),     # 手指从右往左
            "right": (int(width * 0.35), cy, int(width * 0.65), cy),     # 手指从左往右
        }
        if direction not in vectors:
            raise ValueError(f"Unknown swipe direction: {direction}")
        self.d.swipe(*vectors[direction], duration=duration)

    def scroll(self, direction: str = "down", steps: int = 5):
        """
        滚动页面中可滚动的视图（ListView、ScrollView 等）。
        - toEnd / toBeginning：滚动到底部/顶部
        - 与 swipe 的区别：scroll 针对控件滚动，swipe 是模拟手指滑动手势
        """
        logger.info(f"Scrolling {direction}")
        if direction == "down":
            self.d(scrollable=True).scroll.toEnd()
        elif direction == "up":
            self.d(scrollable=True).scroll.toBeginning()
        else:
            raise ValueError(f"Unknown scroll direction: {direction}")

    # ------------------------------------------------------------------ #
    #  文字输入
    # ------------------------------------------------------------------ #

    def input_text(self, text: str):
        """
        向当前焦点输入框输入文字。
        底层使用 uiautomator2 的 send_keys，支持中文（通过 ADB 键盘输入法）
        """
        logger.info(f"Inputting text: {text!r}")
        self.d.send_keys(text, clear=False)  # clear=False 追加文字，不清空原有内容

    def clear_and_input(self, text: str):
        """先清空输入框再输入，适用于修改已有内容的场景"""
        logger.info(f"Clearing and inputting text: {text!r}")
        self.d.send_keys(text, clear=True)

    # ------------------------------------------------------------------ #
    #  硬件按键
    # ------------------------------------------------------------------ #

    def back(self):
        """模拟按下 Android 返回键（等价于手机底部的 ← 按钮）"""
        logger.info("Press: Back")
        self.d.press("back")

    def home(self):
        """模拟按下 Android Home 键（等价于手机底部的 ○ 按钮），回到桌面"""
        logger.info("Press: Home")
        self.d.press("home")

    def recent_apps(self):
        """模拟按下最近任务键（等价于手机底部的 □ 按钮），打开多任务界面"""
        logger.info("Press: Recent apps")
        self.d.press("recent")

    # ------------------------------------------------------------------ #
    #  截图与元素查找
    # ------------------------------------------------------------------ #

    def screenshot(self, path: str = None):
        """
        截取当前屏幕。
        - path 不为空：保存为 PNG 文件，返回文件路径
        - path 为空：返回 PIL Image 对象（可在内存中继续处理）
        """
        logger.info(f"Taking screenshot{' -> ' + path if path else ''}")
        if path:
            self.d.screenshot(path)
            return path
        return self.d.screenshot()

    def get_screen_size(self) -> tuple:
        """返回屏幕分辨率 (width, height)，单位像素"""
        return self.d.window_size()

    def dump_hierarchy(self) -> str:
        """
        导出当前页面的 UI 控件树（XML 格式）。
        用于调试：了解页面有哪些控件、它们的 resourceId 和 text 是什么
        """
        return self.d.dump_hierarchy()

    def find_element(self, text: str = None, resource_id: str = None, description: str = None):
        """返回匹配的 uiautomator2 Selector 对象，可进一步操作（点击、获取文字等）"""
        if text:
            return self.d(text=text)
        elif resource_id:
            return self.d(resourceId=resource_id)
        elif description:
            return self.d(description=description)
        raise ValueError("Provide at least one locator: text, resource_id, or description.")

    def wait_for_element(
        self,
        text: str = None,
        resource_id: str = None,
        description: str = None,
        timeout: float = 10,
    ) -> bool:
        """
        等待某个元素出现在屏幕上（常用于等待页面加载完成）。
        返回 True 表示元素已出现，False 表示超时未出现。
        """
        logger.info(f"Waiting for element (timeout={timeout}s)")
        element = self.find_element(text=text, resource_id=resource_id, description=description)
        return element.wait(timeout=timeout)

    def element_exists(self, text: str = None, resource_id: str = None, description: str = None) -> bool:
        """立即检查某元素是否存在于当前屏幕（不等待）"""
        element = self.find_element(text=text, resource_id=resource_id, description=description)
        return element.exists

    # ------------------------------------------------------------------ #
    #  等待
    # ------------------------------------------------------------------ #

    def wait(self, seconds: float):
        """等待指定秒数（用于给 App 留出加载/动画时间）"""
        logger.info(f"Waiting {seconds}s")
        time.sleep(seconds)

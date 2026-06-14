# ============================================================
# 【工具层公共模块】utils/common.py
# 职责：提供所有任务脚本共用的工具函数，避免重复代码
#
# 包含：
#   - setup_device()  设备连接 + 各层控制器初始化
#   - assert_step()   自动化专用断言（失败自动截图+记录日志）
# ============================================================

import uiautomator2 as u2
from utils.logger import logger
from core.device_manager import DeviceManager
from core.app_controller import AppController
from core.ui_automator import UIAutomator
from core.exception_handler import ExceptionHandler


def setup_device(device_serial: str = None) -> tuple:
    """
    统一的设备连接 + 控制器初始化工厂函数。
    所有任务脚本调用此函数完成设备准备，无需重复编写连接代码。

    参数：
        device_serial: 设备序列号，为 None 时自动选第一台已连接设备

    返回：
        (d, app, ui, exc) 四元组
        - d   : uiautomator2.Device  核心设备对象，所有操作的基础
        - app : AppController        App 启停控制（launch / stop）
        - ui  : UIAutomator          UI 操作封装（点击 / 输入 / 滑动）
        - exc : ExceptionHandler     异常处理（截图 + 日志）
    """
    dm = DeviceManager()
    adb_dev = dm.connect(device_serial)     # ADB 层连接
    serial = adb_dev.serial
    logger.info(f"已连接设备：{serial}")

    d = u2.connect(serial)                  # UIAutomator2 层连接
    app = AppController(d)
    ui = UIAutomator(d)
    exc = ExceptionHandler(ui)

    return d, app, ui, exc


def assert_step(condition: bool, message: str, ui: UIAutomator):
    """
    自动化专用断言，供所有任务脚本使用。

    - condition 为 True  → ✅ 断言通过，记录 INFO 日志，继续执行
    - condition 为 False → ❌ 断言失败，执行以下操作后抛出 AssertionError：
        1. 记录 ERROR 日志（打印到控制台 + 写入日志文件）
        2. 调用 ExceptionHandler 自动截图保存失败现场
        3. 抛出 AssertionError 终止当前任务流程

    优于裸 assert 的原因：
        裸 assert 失败只有一行异常信息，无截图无上下文；
        本函数失败时留下截图，配合日志可快速定位问题。

    参数：
        condition : 要断言的布尔表达式
        message   : 期望描述，失败时打印，建议写"期望…应…"格式
        ui        : UIAutomator 实例，用于截图
    """
    if condition:
        logger.info(f"✅ 断言通过：{message}")
    else:
        logger.error(f"❌ 断言失败：{message}")
        ExceptionHandler(ui).handle(AssertionError(message), context="assertion")
        raise AssertionError(message)

# ============================================================
# 【框架层】base_case.py
# 所有 APK 用例的基类，统一设备初始化、断言、日志与生命周期。
#
# 编写新用例的步骤：
#   1. 继承 ApkTestCase
#   2. 设置 case_id / case_name / case_desc 类属性
#   3. 实现 run_steps()，在步骤间调用 self.assert_step()
#   4. 将用例类注册到对应 APK 目录的 __init__.py
# ============================================================

from abc import ABC, abstractmethod
from typing import Optional

import uiautomator2 as u2

from core.app_controller import AppController
from core.exception_handler import ExceptionHandler
from core.ui_automator import UIAutomator
from utils.common import assert_step, setup_device
from utils.logger import logger


class ApkTestCase(ABC):
    """
    APK 自动化用例基类。

    子类必须实现 run_steps()；setup / teardown 可按需 override。
    """

    # ── 用例元信息（子类必须覆盖 case_id / case_name）────────────────────
    case_id: str = "unnamed_case"
    case_name: str = "未命名用例"
    case_desc: str = ""

    # ── APK 元信息（由 APK 包 __init__.py 在注册时注入，子类一般不用改）──
    apk_id: str = ""
    apk_name: str = ""
    package_name: str = ""

    def __init__(self, device_serial: Optional[str] = None):
        self.device_serial = device_serial
        self.d: Optional[u2.Device] = None
        self.app: Optional[AppController] = None
        self.ui: Optional[UIAutomator] = None
        self.exc: Optional[ExceptionHandler] = None
        self._failed = False

    # ------------------------------------------------------------------ #
    #  生命周期（子类通常只改 run_steps）
    # ------------------------------------------------------------------ #

    def setup(self) -> None:
        """连接设备并初始化控制器，子类可 super().setup() 后继续自定义。"""
        self.d, self.app, self.ui, self.exc = setup_device(self.device_serial)
        logger.info(
            f">> 用例开始 [{self.apk_name}/{self.case_id}] {self.case_name}"
        )

    @abstractmethod
    def run_steps(self) -> None:
        """用例核心步骤，子类必须实现。"""

    def teardown(self) -> None:
        """
        用例结束清理。默认不强制关闭 App，避免影响后续串联用例。
        若需每个用例独立退出 App，在子类 teardown 中调用 self.app.stop_app()。
        """
        status = "失败" if self._failed else "成功"
        logger.info(
            f"<< 用例结束 [{self.apk_name}/{self.case_id}] {self.case_name} — {status}"
        )

    # ------------------------------------------------------------------ #
    #  对外执行入口（由 Runner 调用，勿在子类 override）
    # ------------------------------------------------------------------ #

    def execute(self) -> bool:
        """
        执行完整用例生命周期。

        返回：
            True  — 用例通过
            False — 断言失败或其他异常
        """
        try:
            self.setup()
            self.run_steps()
            return True
        except AssertionError:
            self._failed = True
            logger.error(f"用例断言失败：{self.case_name}")
            return False
        except Exception as exc:
            self._failed = True
            if self.exc:
                self.exc.handle(exc, context=f"{self.apk_id}/{self.case_id}")
            else:
                logger.error(f"用例执行异常：{exc}")
            return False
        finally:
            self.teardown()

    # ------------------------------------------------------------------ #
    #  子类便捷方法
    # ------------------------------------------------------------------ #

    def assert_step(self, condition: bool, message: str) -> None:
        """封装 common.assert_step，自动传入 self.ui。"""
        assert_step(condition, message, self.ui)

    def wait(self, seconds: float) -> None:
        """等待页面加载或动画完成。"""
        self.ui.wait(seconds)

    def is_foreground(self, package_name: str = None) -> bool:
        """检查指定包名（默认当前 APK 包名）是否在前台。"""
        pkg = package_name or self.package_name
        current = self.d.app_current().get("package", "")
        return current == pkg

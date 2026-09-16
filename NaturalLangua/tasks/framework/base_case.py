# ============================================================
# 【框架层】base_case.py
# 所有 APK 用例的基类，统一设备初始化、断言、日志与生命周期。
#
# 编写新用例的步骤：
#   1. 继承 ApkTestCase
#   2. 设置 case_id / case_name / case_desc 类属性
#   3. 实现 run_steps()，在步骤间调用 self.assert_step()
#   4. 将用例类注册到对应 APK 目录的 __init__.py
#
# Allure 集成要点（由框架自动完成，用例侧一般不用管）：
#   - Runner 会给用例注入 reporter，execute() 自动包一层 Allure case
#   - self.assert_step() 每次调用会输出一个 Allure step
#   - self.step("描述") 可显式包一段步骤，报告更好看
#   - self.attach(path, name) 手动挂附件（截图、日志片段等）
#   - 断言失败 / 异常会自动截图并挂到 Allure
# ============================================================

import os
import traceback
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import uiautomator2 as u2

from config import SCREENSHOT_DIR
from core.app_controller import AppController
from core.exception_handler import ExceptionHandler
from core.ui_automator import UIAutomator
from utils.common import setup_device
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

        # Allure：由 Runner 注入 reporter；用例内通过 self._allure_case 访问当前上下文
        self.reporter = None
        self._allure_case = None

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
        if self.reporter is None:
            return self._execute_inner()

        with self.reporter.case(
            apk_id=self.apk_id,
            apk_name=self.apk_name,
            case_id=self.case_id,
            case_name=self.case_name,
            case_desc=self.case_desc,
        ) as allure_case:
            self._allure_case = allure_case
            try:
                return self._execute_inner()
            finally:
                self._allure_case = None

    def _execute_inner(self) -> bool:
        try:
            self.setup()
            self.run_steps()
            return True
        except AssertionError as exc:
            self._failed = True
            logger.error(f"用例断言失败：{self.case_name}")
            if self._allure_case:
                self._allure_case.mark_failed(
                    f"AssertionError: {exc}",
                    traceback.format_exc(),
                )
            return False
        except Exception as exc:  # noqa: BLE001
            self._failed = True
            info = None
            if self.exc:
                info = self.exc.handle(exc, context=f"{self.apk_id}/{self.case_id}")
            else:
                logger.error(f"用例执行异常：{exc}")
            if self._allure_case:
                self._allure_case.mark_broken(
                    f"{type(exc).__name__}: {exc}",
                    traceback.format_exc(),
                )
                if info and info.get("screenshot"):
                    self._allure_case.attach_file(
                        info["screenshot"],
                        name="异常截图",
                    )
            return False
        finally:
            self.teardown()

    # ------------------------------------------------------------------ #
    #  子类便捷方法
    # ------------------------------------------------------------------ #

    def assert_step(self, condition: bool, message: str) -> None:
        """
        断言步骤：失败时自动截图 + 日志 + 抛 AssertionError。
        同时输出一个 Allure step，便于报告定位失败点。
        """
        with self._allure_step(f"断言: {message}"):
            if condition:
                logger.info(f"✅ 断言通过：{message}")
                return
            logger.error(f"❌ 断言失败：{message}")
            self._capture_failure("assert_fail", label="断言失败截图")
            raise AssertionError(message)

    @contextmanager
    def step(self, name: str):
        """
        显式步骤上下文，仅用于让 Allure 报告更清晰。

        用例侧写法：
            with self.step("点击搜索按钮"):
                self.ui.click(...)
        """
        with self._allure_step(name):
            yield

    def attach(
        self,
        source_path: str,
        name: Optional[str] = None,
        mime: Optional[str] = None,
    ) -> None:
        """把一个磁盘文件挂到 Allure 当前 step / case（无 reporter 时静默跳过）。"""
        if self._allure_case is not None:
            self._allure_case.attach_file(source_path, name=name, mime=mime)

    def attach_text(self, text: str, name: str = "log") -> None:
        """把一段文本挂到 Allure 当前 step / case。"""
        if self._allure_case is not None:
            self._allure_case.attach_text(text, name=name)

    def snapshot(self, name: str = "截图") -> Optional[str]:
        """
        主动截图并挂到 Allure（不涉及断言）。
        返回截图路径，失败返回 None。
        """
        return self._capture_failure("snapshot", label=name, level="info")

    def wait(self, seconds: float) -> None:
        """等待页面加载或动画完成。"""
        self.ui.wait(seconds)

    def is_foreground(self, package_name: str = None) -> bool:
        """检查指定包名（默认当前 APK 包名）是否在前台。"""
        pkg = package_name or self.package_name
        current = self.d.app_current().get("package", "")
        return current == pkg

    # ------------------------------------------------------------------ #
    #  内部辅助
    # ------------------------------------------------------------------ #

    @contextmanager
    def _allure_step(self, name: str):
        if self._allure_case is not None:
            with self._allure_case.step(name):
                yield
        else:
            yield

    def _capture_failure(
        self,
        prefix: str,
        label: str = "截图",
        level: str = "warning",
    ) -> Optional[str]:
        """
        截图并挂到 Allure 当前 step / case。
        断言失败 / 主动截图都走这里；无 UI 时静默跳过。
        """
        if not self.ui:
            return None
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = os.path.join(
                SCREENSHOT_DIR,
                f"{prefix}_{self.apk_id}_{self.case_id}_{ts}.png",
            )
            self.ui.screenshot(path)
            if level == "info":
                logger.info(f"截图已保存：{path}")
            else:
                logger.warning(f"失败截图：{path}")
            if self._allure_case is not None:
                self._allure_case.attach_file(path, name=label)
            return path
        except Exception as snap_err:  # noqa: BLE001
            logger.warning(f"截图失败：{snap_err}")
            return None

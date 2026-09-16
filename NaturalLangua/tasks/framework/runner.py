# ============================================================
# 【框架层】runner.py
# 测试执行器：按 APK 或套件顺序运行用例，汇总结果。
#
# 典型用法：
#   runner = TestRunner(device_serial="xxxx")
#   runner.run_apk("browser")              # 跑浏览器全部用例
#   runner.run_apk("browser", ["open_url"]) # 只跑指定用例
#   runner.run_suite("core")               # 浏览器 → 应用商店
#
# 若传入 reporter=AllureReporter(...)，每条用例会自动写 Allure 结果。
# ============================================================

from dataclasses import dataclass, field
from typing import List, Optional, Type

from tasks.framework.base_case import ApkTestCase
from tasks.framework.registry import ApkModule, SUITES, get_apk_module
from utils.logger import logger


@dataclass
class CaseResult:
    """单条用例执行结果。"""

    apk_id: str
    case_id: str
    case_name: str
    passed: bool
    error: str = ""


@dataclass
class RunReport:
    """一次运行的汇总报告。"""

    results: List[CaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and self.total > 0

    def print_summary(self) -> None:
        logger.info("=" * 50)
        logger.info(f"执行汇总：共 {self.total} 条，通过 {self.passed}，失败 {self.failed}")
        for r in self.results:
            mark = "[PASS]" if r.passed else "[FAIL]"
            logger.info(f"  {mark} [{r.apk_id}/{r.case_id}] {r.case_name}")
        logger.info("=" * 50)


class TestRunner:
    """APK 自动化测试执行器。"""

    def __init__(
        self,
        device_serial: Optional[str] = None,
        stop_on_fail: bool = False,
        reporter=None,
    ):
        """
        参数：
            device_serial : ADB 序列号，None 则自动选第一台设备
            stop_on_fail  : True 时某条用例失败后停止后续用例（默认继续跑完）
            reporter      : Allure reporter 实例（可选），传入后每条用例会写 Allure 结果
        """
        self.device_serial = device_serial
        self.stop_on_fail = stop_on_fail
        self.reporter = reporter

    def run_apk(
        self,
        apk_id: str,
        case_ids: Optional[List[str]] = None,
    ) -> RunReport:
        """运行单个 APK 下的全部或指定用例。"""
        module = get_apk_module(apk_id)
        cases = self._filter_cases(module, case_ids)
        report = RunReport()

        logger.info(f"--- APK 开始: {module.apk_name} ({module.apk_id}) ---")
        if module.description:
            logger.info(f"    说明：{module.description}")

        for case_cls in cases:
            result = self._run_one_case(module, case_cls)
            report.results.append(result)
            if not result.passed and self.stop_on_fail:
                logger.warning("stop_on_fail=True，后续用例已跳过")
                break

        logger.info(f"--- APK 结束: {module.apk_name} - 通过 {report.passed}/{report.total} ---")
        return report

    def run_suite(self, suite_name: str, case_ids: Optional[List[str]] = None) -> RunReport:
        """
        按套件顺序执行多个 APK 的全部用例。

        case_ids 若指定，则每个 APK 只跑这些 ID（需该 APK 下存在对应用例）。
        """
        if suite_name not in SUITES:
            known = ", ".join(SUITES.keys())
            raise KeyError(f"未找到套件「{suite_name}」，可用：{known}")

        apk_ids = SUITES[suite_name]
        logger.info(f"[套件] 「{suite_name}」开始，顺序：{' -> '.join(apk_ids)}")

        merged = RunReport()
        for apk_id in apk_ids:
            sub = self.run_apk(apk_id, case_ids=case_ids)
            merged.results.extend(sub.results)
            if self.stop_on_fail and not sub.all_passed:
                break

        merged.print_summary()
        return merged

    def run_all(self) -> RunReport:
        """运行所有已注册 APK 的全部用例。"""
        return self.run_suite("all")

    def _filter_cases(
        self,
        module: ApkModule,
        case_ids: Optional[List[str]],
    ) -> List[Type[ApkTestCase]]:
        if not case_ids:
            return list(module.case_classes)

        id_set = set(case_ids)
        selected = [cls for cls in module.case_classes if cls.case_id in id_set]
        missing = id_set - {cls.case_id for cls in selected}
        if missing:
            known = ", ".join(c.case_id for c in module.case_classes)
            raise KeyError(f"APK「{module.apk_id}」中未找到用例 {missing}，可用：{known}")
        return selected

    def _run_one_case(
        self,
        module: ApkModule,
        case_cls: Type[ApkTestCase],
    ) -> CaseResult:
        case = case_cls(device_serial=self.device_serial)
        case.apk_id = module.apk_id
        case.apk_name = module.apk_name
        case.package_name = module.package_name
        case.reporter = self.reporter

        passed = case.execute()
        return CaseResult(
            apk_id=module.apk_id,
            case_id=case_cls.case_id,
            case_name=case_cls.case_name,
            passed=passed,
        )

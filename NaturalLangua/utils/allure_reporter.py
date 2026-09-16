# ============================================================
# 【工具层】allure_reporter.py
# 直接写 Allure 2 结果 JSON，不依赖 allure-pytest。
#
# 用法（框架已集成，用例侧一般无需直接调用）：
#   reporter = AllureReporter("allure-results")
#   reporter.clean()
#   reporter.write_environment({"device": "xxx", "python": "3.13"})
#   reporter.write_categories()
#   with reporter.case(apk_id=..., case_id=..., case_name=...) as case:
#       with case.step("启动 App"):
#           ...
#       case.attach_file("screenshots/xxx.png", name="首页")
#
# 生成/查看报告（需先安装 allure CLI，见 README）：
#   allure serve allure-results         # 临时预览
#   allure generate allure-results -o allure-report --clean
# ============================================================

from __future__ import annotations

import json
import os
import shutil
import socket
import time
import traceback
import uuid
from contextlib import contextmanager
from typing import Dict, List, Optional


_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "txt": "text/plain",
    "log": "text/plain",
    "json": "application/json",
    "xml": "application/xml",
    "html": "text/html",
    "mp4": "video/mp4",
    "webm": "video/webm",
}


def _guess_mime(ext: str) -> str:
    return _MIME.get(ext.lower().lstrip("."), "application/octet-stream")


def _now_ms() -> int:
    return int(time.time() * 1000)


class AllureReporter:
    """Allure 结果目录写入器。线程/进程内单例即可。"""

    def __init__(self, results_dir: str):
        self.results_dir = os.path.abspath(results_dir)
        os.makedirs(self.results_dir, exist_ok=True)
        self._current: Optional["_CaseCtx"] = None

    # ── 结果目录清理 ─────────────────────────────────────────
    # 清理时**保留**的子目录：HTML 报告放这里，用户期望累积历史，不要被清掉
    _PRESERVE_SUBDIRS = frozenset({"report"})

    def clean(self) -> None:
        """
        清空结果目录（仅清内容，不删目录本身）。
        `report/` 子目录会被保留 —— 那里放的是历史 HTML 报告，属于用户资产。
        """
        if not os.path.isdir(self.results_dir):
            return
        for name in os.listdir(self.results_dir):
            if name in self._PRESERVE_SUBDIRS:
                continue
            p = os.path.join(self.results_dir, name)
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)
            except OSError:
                pass

    # ── 环境信息 / 分类 / executor ──────────────────────────
    def write_environment(self, props: Dict[str, str]) -> None:
        """写 environment.properties，展示在 Allure 报告首页。"""
        path = os.path.join(self.results_dir, "environment.properties")
        with open(path, "w", encoding="utf-8") as f:
            for k, v in props.items():
                if v is None:
                    continue
                f.write(f"{k}={v}\n")

    def write_categories(self, categories: Optional[List[dict]] = None) -> None:
        """写 categories.json，把常见失败归类。"""
        if categories is None:
            categories = _default_categories()
        path = os.path.join(self.results_dir, "categories.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

    def write_executor(self, executor: Optional[dict] = None) -> None:
        """写 executor.json，展示"由谁触发"的信息。"""
        if executor is None:
            executor = {
                "name": "APK Automated Testing",
                "type": "custom",
                "reportName": "APK 自动化测试报告",
            }
        path = os.path.join(self.results_dir, "executor.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(executor, f, ensure_ascii=False, indent=2)

    # ── 用例上下文 ───────────────────────────────────────────
    @contextmanager
    def case(
        self,
        *,
        apk_id: str,
        apk_name: str,
        case_id: str,
        case_name: str,
        case_desc: str = "",
    ):
        ctx = _CaseCtx(
            reporter=self,
            apk_id=apk_id,
            apk_name=apk_name,
            case_id=case_id,
            case_name=case_name,
            case_desc=case_desc,
        )
        prev = self._current
        self._current = ctx
        ctx.start()
        try:
            yield ctx
        finally:
            ctx.finish()
            self._current = prev

    @property
    def current(self) -> Optional["_CaseCtx"]:
        return self._current


class _CaseCtx:
    """单条用例的运行时上下文，收集步骤 / 附件 / 状态。"""

    def __init__(
        self,
        *,
        reporter: AllureReporter,
        apk_id: str,
        apk_name: str,
        case_id: str,
        case_name: str,
        case_desc: str,
    ):
        self.reporter = reporter
        self.uuid = str(uuid.uuid4())
        self.apk_id = apk_id
        self.apk_name = apk_name
        self.case_id = case_id
        self.case_name = case_name
        self.case_desc = case_desc
        self.status = "passed"
        self.status_details: Optional[dict] = None
        self.steps: List[dict] = []
        self.attachments: List[dict] = []
        self.parameters: List[dict] = []
        self.start_ts = 0
        self.stop_ts = 0
        self._step_stack: List[dict] = []

    # ── 状态标记 ────────────────────────────────────────────
    def mark_failed(self, message: str, trace: str = "") -> None:
        self.status = "failed"
        self.status_details = {"message": message, "trace": trace}

    def mark_broken(self, message: str, trace: str = "") -> None:
        self.status = "broken"
        self.status_details = {"message": message, "trace": trace}

    def add_parameter(self, name: str, value: str) -> None:
        self.parameters.append({"name": name, "value": str(value)})

    # ── 生命周期 ────────────────────────────────────────────
    def start(self) -> None:
        self.start_ts = _now_ms()

    def finish(self) -> None:
        self.stop_ts = _now_ms()
        while self._step_stack:
            self._pop_step("broken", status_details={"message": "步骤未正常结束"})
        self._write_result()

    # ── 步骤 ────────────────────────────────────────────────
    @contextmanager
    def step(self, name: str):
        entry = {
            "name": name,
            "status": "passed",
            "stage": "running",
            "start": _now_ms(),
            "steps": [],
            "attachments": [],
            "parameters": [],
        }
        parent = self._step_stack[-1]["steps"] if self._step_stack else self.steps
        parent.append(entry)
        self._step_stack.append(entry)
        try:
            yield
        except AssertionError as exc:
            self._pop_step(
                "failed",
                status_details={
                    "message": f"AssertionError: {exc}",
                    "trace": traceback.format_exc(),
                },
            )
            raise
        except Exception as exc:
            self._pop_step(
                "broken",
                status_details={
                    "message": f"{type(exc).__name__}: {exc}",
                    "trace": traceback.format_exc(),
                },
            )
            raise
        else:
            self._pop_step("passed")

    def _pop_step(
        self,
        status: str,
        status_details: Optional[dict] = None,
    ) -> None:
        if not self._step_stack:
            return
        s = self._step_stack.pop()
        s["status"] = status
        s["stage"] = "finished"
        s["stop"] = _now_ms()
        if status_details:
            s["statusDetails"] = status_details

    # ── 附件 ────────────────────────────────────────────────
    def attach_file(
        self,
        source_path: str,
        name: Optional[str] = None,
        mime: Optional[str] = None,
    ) -> None:
        """把磁盘上的文件复制进 results 目录并挂到当前 step / case。"""
        if not source_path or not os.path.isfile(source_path):
            return
        ext = os.path.splitext(source_path)[1].lstrip(".") or "bin"
        att_id = f"{uuid.uuid4()}-attachment.{ext}"
        dest = os.path.join(self.reporter.results_dir, att_id)
        try:
            shutil.copyfile(source_path, dest)
        except OSError:
            return
        self._register_attachment(
            {
                "name": name or os.path.basename(source_path),
                "source": att_id,
                "type": mime or _guess_mime(ext),
            }
        )

    def attach_text(
        self,
        text: str,
        name: str = "log",
        ext: str = "txt",
        mime: str = "text/plain",
    ) -> None:
        att_id = f"{uuid.uuid4()}-attachment.{ext}"
        dest = os.path.join(self.reporter.results_dir, att_id)
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError:
            return
        self._register_attachment({"name": name, "source": att_id, "type": mime})

    def _register_attachment(self, entry: dict) -> None:
        target = self._step_stack[-1]["attachments"] if self._step_stack else self.attachments
        target.append(entry)

    # ── 落盘 ────────────────────────────────────────────────
    def _write_result(self) -> None:
        result = {
            "uuid": self.uuid,
            "historyId": f"{self.apk_id}.{self.case_id}",
            "testCaseId": f"{self.apk_id}.{self.case_id}",
            "name": self.case_name,
            "fullName": f"tasks.apk.{self.apk_id}.{self.case_id}",
            "status": self.status,
            "stage": "finished",
            "start": self.start_ts,
            "stop": self.stop_ts,
            "description": self.case_desc or "",
            "labels": [
                {"name": "epic", "value": "APK 自动化"},
                {"name": "feature", "value": self.apk_name or self.apk_id},
                {"name": "story", "value": self.case_name},
                {"name": "suite", "value": self.apk_name or self.apk_id},
                {"name": "subSuite", "value": self.apk_id},
                {"name": "severity", "value": "normal"},
                {"name": "package", "value": f"tasks.apk.{self.apk_id}"},
                {"name": "testClass", "value": self.case_id},
                {"name": "testMethod", "value": "run_steps"},
                {"name": "framework", "value": "APKAutomatedTesting"},
                {"name": "language", "value": "python"},
                {"name": "host", "value": socket.gethostname()},
                {"name": "thread", "value": "main"},
            ],
            "links": [],
            "steps": self.steps,
            "attachments": self.attachments,
            "parameters": self.parameters,
        }
        if self.status_details:
            result["statusDetails"] = self.status_details

        out = os.path.join(self.reporter.results_dir, f"{self.uuid}-result.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


def _default_categories() -> List[dict]:
    return [
        {
            "name": "断言失败",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*(AssertionError|断言).*",
        },
        {
            "name": "元素未找到",
            "matchedStatuses": ["broken", "failed"],
            "messageRegex": ".*(UiObjectNotFound|ElementNotFound|NoSuchElement).*",
        },
        {
            "name": "设备/ADB 异常",
            "matchedStatuses": ["broken"],
            "messageRegex": ".*(adb|Device|uiautomator2|ConnectionRefused).*",
        },
        {
            "name": "超时",
            "matchedStatuses": ["broken", "failed"],
            "messageRegex": ".*(Timeout|超时).*",
        },
    ]

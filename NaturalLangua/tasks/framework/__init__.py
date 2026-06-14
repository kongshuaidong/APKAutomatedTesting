# ============================================================
# 【框架层】tasks/framework
# APK 自动化脚本框架的公共入口。
#
# 目录职责：
#   base_case.py  — 所有用例的基类（统一 setup / run / teardown）
#   helpers.py    — 跨 APK 复用的 UI 辅助函数
#   registry.py   — 注册 APK 模块、用例列表、测试套件
#   runner.py     — 按 APK 或套件顺序执行用例
# ============================================================

from tasks.framework.base_case import ApkTestCase
from tasks.framework.runner import TestRunner

__all__ = ["ApkTestCase", "TestRunner"]

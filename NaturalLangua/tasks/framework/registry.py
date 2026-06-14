# ============================================================
# 【框架层】registry.py
# 注册所有 APK 模块、用例类、测试套件。
#
# 新增 APK 时：
#   1. 在 tasks/apk/<apk_id>/ 下创建用例文件
#   2. 在 tasks/apk/<apk_id>/__init__.py 导出 APK_INFO 和 CASES
#   3. 在本文件 APK_MODULES 列表中 import 并 append
#
# 新增套件时：
#   在 SUITES 字典中添加 {套件名: [apk_id 列表]}，按顺序执行。
# ============================================================

from dataclasses import dataclass, field
from typing import List, Type

from tasks.framework.base_case import ApkTestCase


@dataclass
class ApkModule:
    """单个 APK 的注册信息。"""

    apk_id: str                          # 命令行 --apk 使用的短 ID，如 browser
    apk_name: str                        # 中文展示名
    package_name: str                    # Android 包名
    case_classes: List[Type[ApkTestCase]] = field(default_factory=list)
    description: str = ""                # APK 说明，方便维护者理解用途


# ── 延迟 import，避免循环依赖 ────────────────────────────────────────────
def _load_apk_modules() -> List[ApkModule]:
    from tasks.apk.browser import APK_INFO as BROWSER_INFO, CASES as BROWSER_CASES
    from tasks.apk.app_store import APK_INFO as STORE_INFO, CASES as STORE_CASES
    from tasks.apk.douyin import APK_INFO as DOUYIN_INFO, CASES as DOUYIN_CASES

    modules = [
        ApkModule(
            apk_id=BROWSER_INFO["apk_id"],
            apk_name=BROWSER_INFO["apk_name"],
            package_name=BROWSER_INFO["package_name"],
            case_classes=BROWSER_CASES,
            description=BROWSER_INFO.get("description", ""),
        ),
        ApkModule(
            apk_id=STORE_INFO["apk_id"],
            apk_name=STORE_INFO["apk_name"],
            package_name=STORE_INFO["package_name"],
            case_classes=STORE_CASES,
            description=STORE_INFO.get("description", ""),
        ),
        ApkModule(
            apk_id=DOUYIN_INFO["apk_id"],
            apk_name=DOUYIN_INFO["apk_name"],
            package_name=DOUYIN_INFO["package_name"],
            case_classes=DOUYIN_CASES,
            description=DOUYIN_INFO.get("description", ""),
        ),
    ]
    return modules


# 套件：按 apk_id 顺序执行各 APK 下的全部用例
SUITES = {
    # 核心回归：浏览器 + 应用商店（用户最常一键跑的顺序）
    "core": ["browser", "app_store"],
    # 全量：所有已注册 APK
    "all": ["browser", "app_store", "douyin"],
}


def get_apk_modules() -> List[ApkModule]:
    return _load_apk_modules()


def get_apk_module(apk_id: str) -> ApkModule:
    for module in get_apk_modules():
        if module.apk_id == apk_id:
            return module
    known = ", ".join(m.apk_id for m in get_apk_modules())
    raise KeyError(f"未找到 APK「{apk_id}」，可用：{known}")


def list_apk_ids() -> List[str]:
    return [m.apk_id for m in get_apk_modules()]


def list_suite_names() -> List[str]:
    return list(SUITES.keys())

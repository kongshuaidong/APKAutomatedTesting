# ============================================================
# 【AI 桌面 APK】TC002_recommend_reasons.py
# 新增query和推荐理由可以在config文件添加
# 用例：批量验证三方 APP 推荐理由
#   1. 进入 AI 桌面（仅一次，减少解锁/入口重复带来的不稳定）
#   2. 遍历 cfg.RECOMMEND_QUERIES：
#        a. 发送 query
#        b. 轮询回复中出现推荐理由关键词
#        c. 点击右上角「+」新建会话，进入下一条
#   3. 汇总所有 query 结果，只要有任一条未命中即整体失败
# ============================================================

# ── IDE 直接运行支持：把项目根 NaturalLangua/ 加入 sys.path ──────────
import os as _os
import sys as _sys
_ROOT = _os.path.abspath(_os.path.dirname(__file__))
while _ROOT and not _os.path.exists(_os.path.join(_ROOT, "run_apk_tests.py")):
    _parent = _os.path.dirname(_ROOT)
    if _parent == _ROOT:
        break
    _ROOT = _parent
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

from tasks.apk.ailauncher import config as cfg
from tasks.apk.ailauncher.helpers import (
    dismiss_permission_popup,
    enter_ai_launcher,
    new_conversation,
    send_query,
    wait_for_keywords,
)
from tasks.framework.base_case import ApkTestCase
from utils.logger import logger


class CaseRecommendReasons(ApkTestCase):
    case_id = "TC002_recommend_reasons"
    case_name = "TC002_三方APP推荐理由_批量"
    case_desc = "一次进入 AI 桌面，顺序发送多条 query，逐条校验回复中含推荐理由关键词，中间用「+」新建会话切换"

    def run_steps(self) -> None:
        # ── 1. 进入 AI 桌面（仅此一次）──────────────────────────────
        self.assert_step(
            enter_ai_launcher(self.d),
            "应能通过桌面「Agent空间」进入 AI 桌面",
        )
        self.wait(1)

        # ── 2. 遍历 query 逐条发送并采集结果 ────────────────────────
        queries = cfg.RECOMMEND_QUERIES
        total = len(queries)
        results: list[tuple[str, list[str]]] = []  # (query, matched_keywords)

        for idx, query in enumerate(queries, 1):
            logger.info(f"── 第 {idx}/{total} 条：{query!r}")
            try:
                send_query(self.d, query)
                # 仅对 PERMISSION_CHECK_QUERIES 里的 query 轮询检查授权弹窗
                if query in cfg.PERMISSION_CHECK_QUERIES:
                    dismiss_permission_popup(self.d)
                matched = wait_for_keywords(
                    self.d, cfg.RECOMMEND_KEYWORDS, cfg.REPLY_WAIT_SEC
                )
            except Exception as exc:
                logger.error(f"[{idx}/{total}] 执行异常：{exc}")
                matched = []
            results.append((query, matched))
            status = "PASS" if matched else "FAIL"
            logger.info(f"[{idx}/{total}] {status} — 命中关键词: {matched}")

            # 每条 query 结束后新建会话（含最后一条，留干净状态给下次运行）
            try:
                new_conversation(self.d)
                self.wait(0.1)
            except Exception as exc:
                logger.warning(f"[{idx}/{total}] 新建会话失败：{exc}")

        # ── 3. 汇总 + 最终断言 ─────────────────────────────────────
        failed = [q for q, m in results if not m]
        passed_count = total - len(failed)
        logger.info("=" * 50)
        logger.info(f"批量结果：通过 {passed_count}/{total}，失败 {len(failed)}")
        for i, (q, m) in enumerate(results, 1):
            tag = "PASS" if m else "FAIL"
            logger.info(f"  [{tag}] #{i} {q!r} → {m}")   
        logger.info("=" * 50)

        self.assert_step(
            not failed,
            f"以下 {len(failed)}/{total} 条 query 未命中推荐理由关键词：{failed}",
        )


if __name__ == "__main__":
    from tasks.framework.runner import TestRunner
    _report = TestRunner().run_apk("ailauncher", case_ids=[CaseRecommendReasons.case_id])
    _report.print_summary()
    _sys.exit(0 if _report.all_passed else 1)

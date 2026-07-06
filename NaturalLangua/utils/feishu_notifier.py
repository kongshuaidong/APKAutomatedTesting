# ============================================================
# 【工具层】feishu_notifier.py
# 飞书自建应用机器人：把 APK 自动化跑完的汇总报告以交互式卡片形式
# 发送到指定用户私聊（或群 chat_id）。未配置 env 时静默跳过。
#
# 需要的 env（写到 .env）：
#   FEISHU_APP_ID           自建应用的 App ID
#   FEISHU_APP_SECRET       自建应用的 App Secret
#   FEISHU_RECEIVE_ID       接收方标识（默认按邮箱）
#   FEISHU_RECEIVE_ID_TYPE  email / open_id / user_id / union_id / phone / chat_id
#
# 自建应用权限要求：
#   im:message              发送消息
#   im:message:send_as_bot  机器人身份发送
# ============================================================

import json
import time
from typing import List, Optional

import requests

from utils.logger import logger


class FeishuNotifier:
    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    SEND_URL = "https://open.feishu.cn/open-apis/im/v1/messages"

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        receive_id: str,
        receive_id_type: str = "email",
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.receive_id = receive_id
        self.receive_id_type = receive_id_type
        self._token: str = ""
        self._token_exp: float = 0.0

    @property
    def configured(self) -> bool:
        return bool(self.app_id and self.app_secret and self.receive_id)

    def _get_token(self) -> str:
        """按需刷新 tenant_access_token（默认有效期 2 小时，提前 60 秒续期）。"""
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        resp = requests.post(
            self.TOKEN_URL,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"获取 tenant_access_token 失败：{data}")
        self._token = data["tenant_access_token"]
        self._token_exp = time.time() + int(data.get("expire", 7200))
        return self._token

    def send_card(self, card: dict) -> None:
        """发送交互式卡片消息。"""
        token = self._get_token()
        resp = requests.post(
            f"{self.SEND_URL}?receive_id_type={self.receive_id_type}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "receive_id": self.receive_id,
                "msg_type": "interactive",
                "content": json.dumps(card, ensure_ascii=False),
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"飞书发送卡片失败：{data}")


def build_report_card(
    *,
    title: str,
    results: List,
    elapsed_sec: float,
    device_serial: str = "",
) -> dict:
    """
    根据 RunReport.results 构造交互式卡片。

    参数：
        title         : 卡片标题（例如 "APK 自动化 · browser"）
        results       : List[CaseResult]，含 apk_id / case_id / case_name / passed / error
        elapsed_sec   : 整轮耗时（秒）
        device_serial : ADB 设备序列号，可选

    返回：飞书 interactive 卡片 JSON dict
    """
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    all_passed = failed == 0 and total > 0

    template = "green" if all_passed else "red"
    status_emoji = "🎉" if all_passed else "⚠️"

    minutes, seconds = divmod(int(elapsed_sec), 60)
    elapsed_str = f"{minutes}m{seconds:02d}s"

    summary = (
        f"**通过:** {passed} / {total}"
        f"    **失败:** {failed}"
        f"    **耗时:** {elapsed_str}"
    )
    if device_serial:
        summary += f"\n**设备:** `{device_serial}`"

    detail_lines = []
    for r in results:
        icon = "✅" if r.passed else "❌"
        line = f"{icon} `{r.apk_id}/{r.case_id}` {r.case_name}"
        if not r.passed and getattr(r, "error", ""):
            err = str(r.error).replace("\n", " ").strip()
            if len(err) > 200:
                err = err[:200] + "…"
            line += f"\n   > {err}"
        detail_lines.append(line)

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"{status_emoji} {title}"},
            "template": template,
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": summary}},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(detail_lines)}},
        ],
    }


def notify_report(
    *,
    title: str,
    results: List,
    elapsed_sec: float,
    device_serial: str = "",
) -> None:
    """
    读取 config 中的 FEISHU_* 环境变量，构造并发送卡片。
    未配置时静默跳过；发送失败仅日志警告，不抛异常。
    """
    import config as cfg

    notifier = FeishuNotifier(
        app_id=cfg.FEISHU_APP_ID,
        app_secret=cfg.FEISHU_APP_SECRET,
        receive_id=cfg.FEISHU_RECEIVE_ID,
        receive_id_type=cfg.FEISHU_RECEIVE_ID_TYPE,
    )
    if not notifier.configured:
        logger.debug("未配置 FEISHU_APP_ID/APP_SECRET/RECEIVE_ID，跳过飞书通知")
        return

    try:
        card = build_report_card(
            title=title,
            results=results,
            elapsed_sec=elapsed_sec,
            device_serial=device_serial,
        )
        notifier.send_card(card)
        logger.info("飞书通知已发送")
    except Exception as exc:
        logger.warning(f"飞书通知发送失败（不影响用例结果）：{exc}")

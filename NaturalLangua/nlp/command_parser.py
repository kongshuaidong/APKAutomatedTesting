# ============================================================
# 【NLP 层】command_parser.py
# 职责：将用户的自然语言指令转换为可执行的动作列表
#
# 核心机制：LLM Function Calling（工具调用）
#   1. 预先定义一批"工具函数"（TOOLS），描述每个动作的名称和参数
#   2. 将用户输入发送给 LLM，LLM 根据指令决定调用哪些函数、传什么参数
#   3. 解析 LLM 返回的 tool_calls，转换成动作字典列表
#   4. 把执行结果回传给 LLM（多轮对话），让模型知道执行是否成功
#
# 兼容性：使用 OpenAI SDK 的标准接口，支持 OpenAI / DeepSeek / Kimi
#          只需在 .env 中修改 BASE_URL 和 MODEL 即可切换
# ============================================================

import json
from openai import OpenAI
from utils.logger import logger
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL

# ---------------------------------------------------------------------------
# TOOLS：告诉 LLM 它可以调用哪些函数
# 每个工具对应 ActionExecutor 中的一个操作方法
# LLM 会根据用户指令自动选择并填写参数
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "launch_app",
            "description": "Launch an Android app by its package name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_name": {
                        "type": "string",
                        "description": "Android package name, e.g. com.tencent.mm",
                    }
                },
                "required": ["package_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_app",
            "description": "Force-stop an Android app by its package name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_name": {"type": "string", "description": "Android package name"}
                },
                "required": ["package_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": (
                "Click a UI element or screen coordinates. "
                "Provide either (x, y) OR one of text / resource_id / description."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "Absolute X coordinate"},
                    "y": {"type": "number", "description": "Absolute Y coordinate"},
                    "text": {"type": "string", "description": "Visible text of the element"},
                    "resource_id": {"type": "string", "description": "Resource ID of the element"},
                    "description": {"type": "string", "description": "Content description of the element"},
                    "timeout": {"type": "number", "description": "Max wait seconds (default 10)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "long_click",
            "description": "Long-press a UI element or screen coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "text": {"type": "string"},
                    "duration": {"type": "number", "description": "Press duration in seconds"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "input_text",
            "description": "Type text into the currently focused input field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                    "clear_first": {
                        "type": "boolean",
                        "description": "Whether to clear the field before typing (default false)",
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "swipe",
            "description": "Swipe the screen in a direction (up/down/left/right).",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down", "left", "right"],
                    },
                    "duration": {"type": "number", "description": "Swipe duration in seconds"},
                },
                "required": ["direction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the main scrollable view up or down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down"]},
                },
                "required": ["direction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "back",
            "description": "Press the Android Back hardware button.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "home",
            "description": "Press the Android Home hardware button.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot",
            "description": "Take a screenshot of the current screen.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Pause execution for a specified number of seconds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "description": "Seconds to wait"}
                },
                "required": ["seconds"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wait_for_element",
            "description": "Wait until a UI element appears on screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "resource_id": {"type": "string"},
                    "description": {"type": "string"},
                    "timeout": {"type": "number", "description": "Max wait seconds (default 10)"},
                },
            },
        },
    },
]

# ---------------------------------------------------------------------------
# 常见 App 包名速查表（注入到系统提示词，让 LLM 知道"微信"对应哪个包名）
# ---------------------------------------------------------------------------
COMMON_PACKAGES = """
Common Android package names (use these unless the user specifies otherwise):
• WeChat          → com.tencent.mm
• QQ              → com.tencent.mobileqq
• Alipay          → com.eg.android.AlipayGphone
• Taobao          → com.taobao.taobao
• JD              → com.jingdong.app.mall
• Douyin/TikTok   → com.ss.android.ugc.aweme
• Weibo           → com.sina.weibo
• Bilibili        → tv.danmaku.bili
• Chrome          → com.android.chrome
• Settings        → com.android.settings
• Camera          → com.android.camera2
• Gallery         → com.android.gallery3d
• Contacts        → com.android.contacts
• Phone/Dialer    → com.android.dialer
• Messages/SMS    → com.android.mms
• Calculator      → com.android.calculator2
• Maps            → com.google.android.apps.maps
• YouTube         → com.google.android.youtube
• Gmail           → com.google.android.gm
"""

# ---------------------------------------------------------------------------
# 系统提示词：定义 LLM 的角色和行为规范
# 这段文字是整个 NLP 层的"灵魂"，决定了 LLM 如何理解和拆解用户指令
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""You are an expert Android UI automation assistant.
Your job is to interpret the user's natural language instructions and convert them into \
a precise sequence of UI automation function calls.

Guidelines:
1. Break compound tasks into individual atomic steps and call each function in order.
2. After launching an app, add a brief wait (1-2 s) before interacting with its UI.
3. Prefer locating elements by visible text over coordinates.
4. If a package name is not obvious, use your best knowledge or ask the user to confirm.
5. Briefly explain what you are about to do in plain language before issuing tool calls.
6. If a step is ambiguous or likely to fail, say so and suggest an alternative.

{COMMON_PACKAGES}
"""


class CommandParser:
    """自然语言指令解析器：调用 LLM 将用户输入转换为动作列表"""

    def __init__(self):
        # 初始化 OpenAI 兼容客户端（DeepSeek/Kimi 同样适用）
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )
        # 对话历史：保留完整上下文，支持多轮连续指令
        # 第一条消息固定为系统提示词
        self._history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def parse(self, user_command: str) -> tuple[list[dict], str | None]:
        """
        解析一条自然语言指令。

        流程：
          用户输入 → 追加到对话历史 → 发送给 LLM（携带 TOOLS 定义）
          → LLM 返回 tool_calls（要调用哪些函数+参数）
          → 解析成 actions 列表返回

        返回：
          - actions: [{"function": "launch_app", "args": {...}, "tool_call_id": "..."}]
          - ai_message: LLM 的文字说明（可能为 None）
        """
        self._history.append({"role": "user", "content": user_command})

        # 发送请求给 LLM，tool_choice="auto" 让模型自己决定是否调用工具
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=self._history,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        actions: list[dict] = []

        if message.tool_calls:
            # LLM 决定调用工具：解析每个 tool_call 的函数名和参数
            for tc in message.tool_calls:
                actions.append(
                    {
                        "function": tc.function.name,
                        "args": json.loads(tc.function.arguments),  # JSON 字符串 → dict
                        "tool_call_id": tc.id,  # 用于后续回传执行结果（多轮对话必须）
                    }
                )
            # 将 assistant 消息存入历史，以便后续回传 tool 结果
            self._history.append(message)

        ai_text = message.content  # LLM 的文字解释（如"我来帮你打开微信..."）
        if ai_text:
            logger.info(f"AI: {ai_text}")

        return actions, ai_text

    def add_tool_results(self, results: list[dict]):
        """
        将工具执行结果回传给 LLM（多轮对话闭环）。
        LLM 看到执行结果后可以决定是否需要继续操作或报告错误。
        tool_call_id 必须与 parse() 返回的 id 一一对应。
        """
        for r in results:
            self._history.append(
                {
                    "role": "tool",
                    "tool_call_id": r["tool_call_id"],
                    "content": r["content"],    # "OK: Launched com.xxx" 或 "ERROR: ..."
                }
            )

    def follow_up(self) -> tuple[list[dict], str | None]:
        """
        在回传执行结果后，再次询问 LLM 是否有后续动作。
        实现"执行→观察→再执行"的自动化闭环。
        """
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=self._history,
            tools=TOOLS,
            tool_choice="auto",
        )
        message = response.choices[0].message
        actions: list[dict] = []

        if message.tool_calls:
            for tc in message.tool_calls:
                actions.append(
                    {
                        "function": tc.function.name,
                        "args": json.loads(tc.function.arguments),
                        "tool_call_id": tc.id,
                    }
                )
            self._history.append(message)

        ai_text = message.content
        if ai_text:
            logger.info(f"AI follow-up: {ai_text}")

        return actions, ai_text

    def reset(self):
        """清空对话历史（只保留系统提示词），开始全新对话"""
        self._history = [{"role": "system", "content": SYSTEM_PROMPT}]
        logger.info("Conversation history reset.")

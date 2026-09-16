#!/usr/bin/env python3
# ============================================================
# 【报告生成】gen_report.py
# 把 allure-results/ 目录下的 JSON 结果渲染成一个自包含 HTML。
# 不依赖 Allure CLI / Java，纯 Python 实现。
#
# 用法：
#   cd NaturalLangua
#   python gen_report.py                    # 生成 report.html
#   python gen_report.py --open             # 生成后用默认浏览器打开
#   python gen_report.py --out my.html      # 指定输出文件
#   python gen_report.py --results other/   # 指定结果目录
#   python gen_report.py --no-embed         # 不 base64 嵌入图片（HTML 更小，但需保留 allure-results/）
#
# 与官方 Allure CLI 相比：
#   ✅ 零依赖、单文件可分享、无需 Java
#   ✅ 展示 汇总 / 用例 / 步骤 / 截图 / 错误堆栈 / 环境信息
#   ❌ 无历史趋势 / 分类统计图 / 复杂过滤（想要请装 allure CLI）
# ============================================================

from __future__ import annotations

import argparse
import base64
import glob
import html
import json
import mimetypes
import os
import sys
import webbrowser
from collections import Counter
from datetime import datetime
from typing import Optional


STATUS_META = {
    "passed":  {"label": "通过", "color": "#22c55e", "icon": "✓"},
    "failed":  {"label": "断言失败", "color": "#ef4444", "icon": "✕"},
    "broken":  {"label": "异常", "color": "#f59e0b", "icon": "!"},
    "skipped": {"label": "跳过", "color": "#94a3b8", "icon": "–"},
    "unknown": {"label": "未知", "color": "#64748b", "icon": "?"},
}


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RESULTS_DIR = os.path.join(PROJECT_ROOT, "allure-results")
DEFAULT_REPORT_DIR = os.path.join(DEFAULT_RESULTS_DIR, "report")


def default_report_path(label: str | None) -> str:
    """
    默认报告文件路径：
      - 有 label：allure-results/report/report_<label>_<YYYYMMDD_HHMM>.html
      - 无 label：allure-results/report/report.html
    与 run_apk_tests.py / scheduler.py 共用，避免路径推算重复。
    """
    if label:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        safe = _sanitize_label(label)
        return os.path.join(DEFAULT_REPORT_DIR, f"report_{safe}_{ts}.html")
    return os.path.join(DEFAULT_REPORT_DIR, "report.html")


def _sanitize_label(label: str) -> str:
    """把 label 里可能有的空格 / 路径分隔符替换成 `-`，其他保留。"""
    bad = set(" \\/:*?\"<>|")
    return "".join(c if c not in bad else "-" for c in label).strip("-") or "run"


def _load_results(results_dir: str) -> list[dict]:
    """加载所有 *-result.json，按开始时间排序。"""
    paths = glob.glob(os.path.join(results_dir, "*-result.json"))
    items = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                items.append(json.load(f))
        except (OSError, json.JSONDecodeError) as e:
            print(f"[跳过] 读取失败 {p}: {e}", file=sys.stderr)
    items.sort(key=lambda r: r.get("start", 0))
    return items


def _load_env(results_dir: str) -> dict:
    """读 environment.properties → dict。"""
    path = os.path.join(results_dir, "environment.properties")
    env: dict = {}
    if not os.path.isfile(path):
        return env
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line or line.startswith("#"):
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    except OSError:
        pass
    return env


def _fmt_duration(start: int, stop: int) -> str:
    ms = max(0, (stop or 0) - (start or 0))
    if ms < 1000:
        return f"{ms} ms"
    sec = ms / 1000
    if sec < 60:
        return f"{sec:.1f} s"
    m, s = divmod(int(sec), 60)
    return f"{m}m{s:02d}s"


def _fmt_ts(ms: int) -> str:
    if not ms:
        return "-"
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def _attachment_src(att: dict, results_dir: str, embed: bool) -> Optional[str]:
    """把附件转为 <img src>/<a href> 用的 URL/data-URI。找不到返回 None。"""
    source = att.get("source")
    if not source:
        return None
    abs_path = os.path.join(results_dir, source)
    if not os.path.isfile(abs_path):
        return None
    mime = att.get("type") or mimetypes.guess_type(source)[0] or "application/octet-stream"
    if embed:
        try:
            with open(abs_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except OSError:
            return None
    # 相对路径引用（HTML 需与 allure-results/ 同目录才能加载）
    return os.path.relpath(abs_path, os.path.dirname(_out_path_hint)) if _out_path_hint else source


# _out_path_hint 用于 --no-embed 模式下计算相对路径
_out_path_hint: Optional[str] = None


def _render_attachment(att: dict, results_dir: str, embed: bool) -> str:
    src = _attachment_src(att, results_dir, embed)
    if not src:
        return ""
    name = html.escape(att.get("name") or att.get("source") or "attachment")
    mime = (att.get("type") or "").lower()
    if mime.startswith("image/"):
        return (
            f'<div class="att image">'
            f'<div class="att-name">📷 {name}</div>'
            f'<a href="{src}" target="_blank"><img src="{src}" alt="{name}"/></a>'
            f"</div>"
        )
    if mime.startswith("text/") or mime in ("application/json", "application/xml"):
        try:
            src_no_prefix = src.split(",", 1)[1] if src.startswith("data:") else None
            text = (
                base64.b64decode(src_no_prefix).decode("utf-8", errors="replace")
                if src_no_prefix
                else ""
            )
        except Exception:  # noqa: BLE001
            text = ""
        if text:
            return (
                f'<div class="att text">'
                f'<div class="att-name">📄 {name}</div>'
                f'<pre>{html.escape(text)}</pre>'
                f"</div>"
            )
    # 其他类型：给一个下载链接
    return (
        f'<div class="att other">'
        f'<a href="{src}" download="{name}">⬇ {name}</a>'
        f"</div>"
    )


def _render_steps(steps: list[dict], results_dir: str, embed: bool, depth: int = 0) -> str:
    if not steps:
        return ""
    lines = ['<ul class="steps">']
    for s in steps:
        status = (s.get("status") or "unknown").lower()
        meta = STATUS_META.get(status, STATUS_META["unknown"])
        dur = _fmt_duration(s.get("start", 0), s.get("stop", 0))
        name = html.escape(s.get("name", "step"))
        details = s.get("statusDetails") or {}
        message = html.escape(details.get("message", "") or "")
        trace = html.escape(details.get("trace", "") or "")

        atts_html = "".join(
            _render_attachment(a, results_dir, embed) for a in (s.get("attachments") or [])
        )
        inner_steps = _render_steps(s.get("steps") or [], results_dir, embed, depth + 1)
        err_block = ""
        if status in ("failed", "broken") and (message or trace):
            err_block = (
                f'<div class="err"><div class="err-msg">{message}</div>'
                f'<pre class="err-trace">{trace}</pre></div>'
            )

        lines.append(
            f'<li class="step step-{status}">'
            f'<div class="step-head">'
            f'<span class="dot" style="background:{meta["color"]}"></span>'
            f'<span class="step-name">{name}</span>'
            f'<span class="step-dur">{dur}</span>'
            f"</div>"
            f"{err_block}{atts_html}{inner_steps}"
            f"</li>"
        )
    lines.append("</ul>")
    return "".join(lines)


def _render_case(case: dict, results_dir: str, embed: bool, idx: int) -> str:
    status = (case.get("status") or "unknown").lower()
    meta = STATUS_META.get(status, STATUS_META["unknown"])
    name = html.escape(case.get("name") or case.get("fullName") or "case")
    full = html.escape(case.get("fullName") or "")
    desc = html.escape(case.get("description") or "")
    dur = _fmt_duration(case.get("start", 0), case.get("stop", 0))
    start_str = _fmt_ts(case.get("start", 0))

    labels = {lb["name"]: lb["value"] for lb in case.get("labels") or [] if lb.get("name")}
    feature = html.escape(labels.get("feature", ""))
    subsuite = html.escape(labels.get("subSuite", ""))

    details = case.get("statusDetails") or {}
    message = html.escape(details.get("message", "") or "")
    trace = html.escape(details.get("trace", "") or "")
    err_block = ""
    if status in ("failed", "broken") and (message or trace):
        err_block = (
            f'<div class="err"><div class="err-msg">{message}</div>'
            f'<pre class="err-trace">{trace}</pre></div>'
        )

    steps_html = _render_steps(case.get("steps") or [], results_dir, embed)
    case_atts_html = "".join(
        _render_attachment(a, results_dir, embed) for a in (case.get("attachments") or [])
    )

    return (
        f'<details class="case case-{status}" data-status="{status}"'
        f'{" open" if status != "passed" else ""}>'
        f'<summary>'
        f'<span class="badge" style="background:{meta["color"]}">'
        f'{meta["icon"]} {meta["label"]}</span>'
        f'<span class="case-name">{name}</span>'
        f'<span class="case-meta">{feature or subsuite} · {dur} · {start_str}</span>'
        f"</summary>"
        f'<div class="case-body">'
        f'<div class="case-full">{full}</div>'
        f'{f"<div class=\"case-desc\">{desc}</div>" if desc else ""}'
        f"{err_block}"
        f"{steps_html}"
        f'{f"<div class=\"case-atts\">{case_atts_html}</div>" if case_atts_html else ""}'
        f"</div>"
        f"</details>"
    )


def _render_html(cases: list[dict], env: dict, results_dir: str, embed: bool) -> str:
    counter = Counter((c.get("status") or "unknown").lower() for c in cases)
    total = len(cases)
    total_ms = sum(max(0, (c.get("stop", 0) or 0) - (c.get("start", 0) or 0)) for c in cases)

    stat_cards = []
    for st in ("passed", "failed", "broken", "skipped"):
        n = counter.get(st, 0)
        m = STATUS_META[st]
        stat_cards.append(
            f'<div class="stat" data-filter="{st}">'
            f'<div class="stat-count" style="color:{m["color"]}">{n}</div>'
            f'<div class="stat-label">{m["label"]}</div>'
            f"</div>"
        )

    env_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
        for k, v in env.items()
    ) or "<tr><td colspan='2' class='muted'>无</td></tr>"

    cases_by_feature: dict[str, list[dict]] = {}
    for c in cases:
        labels = {lb["name"]: lb["value"] for lb in c.get("labels") or [] if lb.get("name")}
        feat = labels.get("feature") or labels.get("subSuite") or "(未分组)"
        cases_by_feature.setdefault(feat, []).append(c)

    cases_html_parts = []
    for feat, group in cases_by_feature.items():
        c_pass = sum(1 for c in group if (c.get("status") or "").lower() == "passed")
        cases_html_parts.append(
            f'<section class="group">'
            f'<h2>{html.escape(feat)} '
            f'<span class="group-count">{c_pass}/{len(group)}</span></h2>'
            + "".join(_render_case(c, results_dir, embed, i) for i, c in enumerate(group))
            + "</section>"
        )
    cases_html = "".join(cases_html_parts) or '<p class="muted">无用例结果</p>'

    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pass_rate = f"{counter.get('passed', 0) / total * 100:.0f}%" if total else "-"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>APK 自动化测试报告</title>
<style>
:root {{
  --bg: #f7f8fa; --panel: #fff; --text: #0f172a; --muted: #64748b;
  --border: #e2e8f0; --code-bg: #f1f5f9;
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#0b1220; --panel:#111827; --text:#e5e7eb; --muted:#94a3b8;
           --border:#1f2937; --code-bg:#0f172a; }}
}}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Microsoft YaHei", sans-serif; background:var(--bg); color:var(--text); font-size:14px; }}
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px 60px; }}
header {{ display:flex; align-items:baseline; justify-content:space-between; gap:16px;
          margin-bottom:20px; flex-wrap:wrap; }}
header h1 {{ font-size: 22px; margin:0; }}
header .sub {{ color:var(--muted); font-size:12px; }}
.panel {{ background:var(--panel); border:1px solid var(--border); border-radius:12px;
          padding:16px 18px; margin-bottom:16px; }}
.stats {{ display:grid; grid-template-columns: repeat(5, 1fr); gap:12px; }}
.stat {{ background:var(--panel); border:1px solid var(--border); border-radius:12px;
         padding:14px; text-align:center; cursor:pointer; user-select:none;
         transition: transform .1s; }}
.stat:hover {{ transform: translateY(-1px); }}
.stat.active {{ outline: 2px solid #6366f1; }}
.stat-count {{ font-size:26px; font-weight:600; }}
.stat-label {{ color:var(--muted); font-size:12px; margin-top:4px; }}
.pass-rate {{ font-size:16px; font-weight:600; }}
.env table {{ width:100%; border-collapse: collapse; }}
.env td {{ padding:4px 8px; border-bottom:1px solid var(--border); font-family: ui-monospace,
           "SF Mono", Consolas, monospace; font-size:12px; }}
.env td:first-child {{ color:var(--muted); width:200px; }}
.group h2 {{ font-size:15px; margin: 24px 0 10px; display:flex; align-items:center; gap:10px; }}
.group-count {{ font-weight:400; color:var(--muted); font-size:12px; }}
.case {{ background:var(--panel); border:1px solid var(--border); border-radius:10px;
         margin-bottom:8px; overflow:hidden; }}
.case > summary {{ list-style:none; padding: 12px 16px; cursor:pointer;
                   display:flex; gap:12px; align-items:center; }}
.case > summary::-webkit-details-marker {{ display:none; }}
.case > summary::before {{ content:"▶"; color:var(--muted); font-size:10px;
                            transition: transform .15s; }}
.case[open] > summary::before {{ transform: rotate(90deg); }}
.badge {{ display:inline-block; color:#fff; padding:2px 8px; border-radius:999px;
          font-size:11px; font-weight:600; letter-spacing:.3px; }}
.case-name {{ font-weight:500; flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; }}
.case-meta {{ color:var(--muted); font-size:12px; }}
.case-body {{ padding: 0 16px 16px; border-top: 1px solid var(--border); }}
.case-full {{ font-family: ui-monospace, monospace; font-size:11px; color:var(--muted);
              margin:10px 0 6px; }}
.case-desc {{ color:var(--muted); font-size:13px; margin:6px 0 10px; }}
.steps {{ list-style:none; padding-left:0; margin:8px 0; }}
.step {{ margin: 2px 0; }}
.step-head {{ display:flex; align-items:center; gap:8px; padding:4px 0; }}
.dot {{ width:8px; height:8px; border-radius:50%; flex:0 0 auto; }}
.step-name {{ flex:1; }}
.step-dur {{ color:var(--muted); font-size:11px; }}
.step .steps {{ padding-left:20px; border-left:1px dashed var(--border); margin-left:3px; }}
.err {{ background: rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.35);
        border-radius:6px; padding:8px 10px; margin:6px 0; }}
.err-msg {{ color:#ef4444; font-weight:500; font-family: ui-monospace, monospace; font-size:12px; }}
.err-trace {{ margin:6px 0 0; background: var(--code-bg); padding:8px; border-radius:4px;
              font-size:11px; overflow-x:auto; }}
.att {{ margin:8px 0; }}
.att-name {{ color:var(--muted); font-size:12px; margin-bottom:4px; }}
.att img {{ max-width:100%; max-height:600px; border:1px solid var(--border);
            border-radius:6px; cursor: zoom-in; }}
.att pre {{ background: var(--code-bg); padding:8px; border-radius:6px;
            font-size:11px; overflow-x:auto; max-height:400px; }}
.att.other a {{ display:inline-block; padding:4px 10px; background:var(--code-bg);
                border-radius:6px; text-decoration:none; color:var(--text); font-size:12px; }}
.muted {{ color: var(--muted); }}
pre {{ white-space: pre-wrap; word-break: break-word; margin:0;
       font-family: ui-monospace, "SF Mono", Consolas, monospace; }}
@media (max-width: 720px) {{
  .stats {{ grid-template-columns: repeat(2, 1fr); }}
  .case-meta {{ display:none; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>APK 自动化测试报告</h1>
      <div class="sub">生成于 {generated} · 用例 {total} 条 · 通过率 {pass_rate} · 总耗时 {_fmt_duration(0, total_ms)}</div>
    </div>
    <div class="pass-rate" style="color:{STATUS_META['passed']['color']}">{pass_rate}</div>
  </header>

  <div class="stats">
    <div class="stat" data-filter="all">
      <div class="stat-count">{total}</div>
      <div class="stat-label">全部</div>
    </div>
    {"".join(stat_cards)}
  </div>

  <div class="panel env">
    <h3 style="margin:0 0 8px;font-size:13px;color:var(--muted);">环境信息</h3>
    <table><tbody>{env_rows}</tbody></table>
  </div>

  <div id="cases">
    {cases_html}
  </div>
</div>

<script>
(function() {{
  const stats = document.querySelectorAll('.stat');
  const cases = document.querySelectorAll('.case');
  stats.forEach(s => s.addEventListener('click', () => {{
    const f = s.dataset.filter;
    stats.forEach(x => x.classList.toggle('active', x === s));
    cases.forEach(c => {{
      c.style.display = (f === 'all' || c.dataset.status === f) ? '' : 'none';
    }});
  }}));
}})();
</script>
</body>
</html>
"""


def main() -> int:
    global _out_path_hint

    parser = argparse.ArgumentParser(description="从 allure-results/ 生成自包含 HTML 报告")
    parser.add_argument(
        "--results", "-r",
        default=DEFAULT_RESULTS_DIR,
        help="Allure 结果目录（默认 <项目>/allure-results）",
    )
    parser.add_argument(
        "--out", "-o",
        default=None,
        help="输出 HTML 路径。不指定时：给了 --label 就用 "
             "allure-results/report/report_<label>_<YYYYMMDD_HHMM>.html，"
             "否则用 allure-results/report/report.html",
    )
    parser.add_argument(
        "--label", "-L",
        default=None,
        help="应用/套件标识，会拼进默认文件名，例如 ailauncher / suite-core",
    )
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="不 base64 嵌入图片/文件；HTML 更小但需与 allure-results/ 保持相对路径",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="生成后用默认浏览器打开",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.results):
        print(f"[错误] 结果目录不存在：{args.results}", file=sys.stderr)
        print("      先执行 `python run_apk_tests.py --apk <APK>` 生成结果。", file=sys.stderr)
        return 1

    out_path = args.out or default_report_path(args.label)

    _out_path_hint = os.path.abspath(out_path)
    cases = _load_results(args.results)
    if not cases:
        print(f"[警告] {args.results} 中未找到 *-result.json", file=sys.stderr)

    env = _load_env(args.results)
    html_str = _render_html(cases, env, args.results, embed=not args.no_embed)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_str)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"报告已生成：{os.path.abspath(out_path)}  ({size_kb:.1f} KB, {len(cases)} 条用例)")

    if args.open:
        webbrowser.open("file:///" + os.path.abspath(out_path).replace("\\", "/"))

    return 0


if __name__ == "__main__":
    sys.exit(main())

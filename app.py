import os
import re
import json
import html
import time
import requests
import streamlit as st
import streamlit.components.v1 as components

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="清小知——高校通知模拟器",
    layout="wide",
)

# =========================
# Styles (cool + premium)
# =========================
st.markdown(
    """
    <style>
      /* Background must apply in Streamlit */
      [data-testid="stAppViewContainer"]{
        background:
          radial-gradient(1200px 700px at 20% 0%, rgba(59,130,246,.16), transparent 60%),
          radial-gradient(900px 520px at 85% 10%, rgba(37,99,235,.12), transparent 55%),
          linear-gradient(180deg, rgba(239,246,255,1) 0%, rgba(248,250,252,1) 55%, rgba(255,255,255,1) 100%);
      }
      [data-testid="stHeader"]{ background: transparent; }
      .block-container {padding-top: 1.1rem; padding-bottom: 2.0rem; max-width: 1120px;}

      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      /* Header */
      .hero { text-align:center; padding: 8px 0 14px 0; position: relative; }
      .hero-title{
        font-size: 42px; font-weight: 900; letter-spacing: -0.03em;
        color: rgba(15, 23, 42, .95); margin: 0;
        animation: floatIn .7s ease-out both;
        text-shadow: 0 10px 35px rgba(37,99,235,.18);
      }
      .hero-pill{
        display:inline-flex; align-items:center; gap:10px;
        padding: 10px 16px; border-radius: 999px;
        border: 1px solid rgba(2,6,23,.06);
        background: rgba(255,255,255,.75);
        box-shadow: 0 10px 30px rgba(2,6,23,.06);
        color: rgba(51,65,85,.90); font-size: 14px; margin-top: 10px;
        animation: glow 3.2s ease-in-out infinite;
      }
      .hero-dot{
        width:10px; height:10px; border-radius:999px;
        background: rgba(37,99,235,.85);
        box-shadow: 0 0 0 6px rgba(37,99,235,.12);
      }
      @keyframes floatIn{ from{ transform: translateY(8px); opacity: 0; } to{ transform: translateY(0); opacity: 1; } }
      @keyframes glow{ 0%,100% { box-shadow: 0 10px 30px rgba(2,6,23,.06); } 50% { box-shadow: 0 18px 40px rgba(37,99,235,.12); } }

      /* Section title */
      .section-h{
        font-size: 19px; font-weight: 900;
        margin: 0.35rem 0 1.0rem 0;
        border-left: 4px solid rgba(37,99,235,.55);
        padding-left: 12px;
        color: rgba(15,23,42,.92);
      }

      /* Card */
      .card {
        background: rgba(255,255,255,.88);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 12px 34px rgba(2,6,23,.07);
        border: 1px solid rgba(2,6,23,.05);
      }
      .muted {color: rgba(51,65,85,.70);}

      /* KPI */
      .kpi-label {color: rgba(51,65,85,.60); font-size: 12px; letter-spacing: .06em;}
      .kpi-value {font-size: 34px; font-weight: 900; margin-top: 6px; color: rgba(15,23,42,.92);}
      .kpi-value2 {font-size: 22px; font-weight: 900; margin-top: 10px; color: rgba(15,23,42,.92);}
      .bar {height: 10px; border-radius: 999px; background: rgba(15,23,42,.08); overflow: hidden; margin-top: 10px;}
      .bar > div {height: 100%; border-radius: 999px; background: linear-gradient(90deg, rgba(37,99,235,.95), rgba(59,130,246,.75));}

      /* Highlight */
      mark.hl { background: rgba(59, 130, 246, 0.22); color: inherit; padding: 0 .18em; border-radius: .35em; }

      /* Tips */
      .tip{
        margin-top: 10px; padding: 12px 14px;
        border-radius: 16px;
        background: rgba(37,99,235,0.055);
        border: 1px solid rgba(2,6,23,.05);
        box-shadow: 0 10px 26px rgba(2,6,23,.04);
      }
      .tip-title{ font-weight: 900; color: rgba(15,23,42,.90); margin-bottom: 6px; font-size: 13px; }
      .tip-text{ color: rgba(51,65,85,.76); line-height: 1.65; white-space: pre-line; font-size: 12.5px; }

      /* Blue tags */
      .blue-tag{
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        background:rgba(37,99,235,.12);
        color:rgba(37,99,235,1);
        font-size:12px;
        margin-right:8px;
        margin-bottom:6px;
        border: 1px solid rgba(37,99,235,.18);
        font-weight: 700;
      }

      /* Chat bubble */
      .bubble{
        margin-top:10px;
        background: rgba(255,255,255,.94);
        border: 1px solid rgba(2,6,23,.07);
        border-radius: 18px;
        padding: 12px 14px;
        font-size: 14px;
        line-height: 1.75;
        color: rgba(15,23,42,.92);
        box-shadow: 0 12px 28px rgba(2,6,23,.06);
        position: relative;
      }
      .bubble:before{
        content:"";
        position:absolute;
        left:18px;
        top:-8px;
        width:14px;
        height:14px;
        background: rgba(255,255,255,.94);
        border-left: 1px solid rgba(2,6,23,.07);
        border-top: 1px solid rgba(2,6,23,.07);
        transform: rotate(45deg);
      }

      /* Risk item */
      .rp-item{
        padding: 12px 12px;
        border-radius: 14px;
        border: 1px solid rgba(2,6,23,.06);
        background: rgba(255,255,255,.74);
        margin-bottom: 10px;
      }

      /* Tabs */
      .stTabs [data-baseweb="tab-list"]{ justify-content: space-around; padding: 0 28px; }
      .stTabs [data-baseweb="tab"]{ font-size: 15px; font-weight: 900; padding-left: 0 !important; padding-right: 0 !important; }

      /* Primary button */
      div.stButton > button[kind="primary"]{
        width: 100%;
        border: 0 !important;
        border-radius: 16px !important;
        padding: 14px 16px !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, rgba(37,99,235,.96), rgba(59,130,246,.92)) !important;
        box-shadow: 0 18px 44px rgba(37,99,235,.22) !important;
        transition: transform .15s ease, box-shadow .2s ease, filter .2s ease;
      }
      div.stButton > button[kind="primary"]:hover{
        transform: translateY(-1px);
        filter: brightness(1.02);
        box-shadow: 0 22px 60px rgba(37,99,235,.28) !important;
      }
      div.stButton > button[kind="primary"]:active{ transform: translateY(0px) scale(.99); }

      /* Loading */
      .loading{
        display:flex;
        align-items:center;
        justify-content:center;
        gap:10px;
        padding: 14px 16px;
        border-radius: 16px;
        background: linear-gradient(90deg, rgba(37,99,235,.96), rgba(59,130,246,.92));
        color: white;
        font-weight: 900;
        box-shadow: 0 18px 44px rgba(37,99,235,.22);
        user-select:none;
      }
      .dots span{
        display:inline-block;
        width:6px; height:6px;
        border-radius:999px;
        background:white;
        margin-left:5px;
        opacity:.25;
        animation: blink 1.1s infinite;
      }
      .dots span:nth-child(2){ animation-delay: .15s; }
      .dots span:nth-child(3){ animation-delay: .3s; }
      @keyframes blink{
        0%,100%{ opacity:.25; transform: translateY(0); }
        50%{ opacity:1; transform: translateY(-2px); }
      }

      /* Secondary action button (emoji) — match "复制该版本" */
      div.stButton > button[kind="secondary"]{
        width: 100%;
        border-radius: 14px !important;
        padding: 10px 12px !important;
        font-weight: 900 !important;
        font-size: 15px !important;

        border: 1px solid rgba(37,99,235,.25) !important;
        background: rgba(37,99,235,.08) !important;
        color: rgba(37,99,235,1) !important;

        transition: transform .15s ease, filter .2s ease;
      }
      div.stButton > button[kind="secondary"]:hover{
        transform: translateY(-1px);
        filter: brightness(1.02);
      }

      /* Footnote */
      .footnote {
        color: rgba(51,65,85,.55);
        font-size: 12px;
        margin-top: 18px;
        text-align:center;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Header
# =========================
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">清小知</div>
      <div class="hero-pill">
        <span class="hero-dot"></span>
        <span>高校通知小助手｜让通知更容易被理解</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# DeepSeek config
# =========================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

if not DEEPSEEK_API_KEY:
    st.error(
        "未检测到 DEEPSEEK_API_KEY。\n\n"
        "- Streamlit Cloud：Manage app → Secrets 添加 DEEPSEEK_API_KEY\n"
        "- 本地：终端执行 export DEEPSEEK_API_KEY='你的key'"
    )
    st.stop()

# =========================
# Helpers
# =========================
EMOJI_MAP = {
    "焦虑": "😰",
    "紧张": "😟",
    "抵触": "😤",
    "困惑": "😕",
    "不安": "😣",
    "担忧": "😧",
    "生气": "😡",
    "配合": "🙂",
    "反感": "🙃",
}

def safe_extract_json(text: str):
    if not text:
        return None, "empty_response"
    cleaned = re.sub(r"```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()

    try:
        return json.loads(cleaned), None
    except Exception:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start : end + 1]
        candidate = candidate.replace("“", "\"").replace("”", "\"").replace("’", "'").replace("‘", "'")
        try:
            return json.loads(candidate), None
        except Exception as e:
            return None, f"json_parse_failed: {e}"

    return None, "no_json_object_found"

def call_deepseek(system_prompt: str, user_prompt: str, model: str = "deepseek-chat"):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        "temperature": 0.3,
    }
    r = requests.post(API_URL, headers=headers, json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

def local_fallback(text: str):
    risky_words = ["严肃处理", "通报批评", "纪律处分", "一律", "从严", "不得", "立即", "清退", "追责", "强制", "处分", "严禁", "必须"]
    hits = [w for w in risky_words if w in text]
    score = 10 + min(70, len(hits) * 10)
    level = "LOW" if score < 30 else ("MEDIUM" if score < 60 else "HIGH")

    issues = []
    if hits:
        issues.append(
            {
                "title": "措辞强硬 / 惩戒导向",
                "evidence": hits[0],
                "why": "学生容易解读为高压或“结果已定”，引发抵触、吐槽与二次传播。",
                "rewrite_tip": "补充依据与范围，明确流程与咨询渠道；用“提醒+规范+支持”替代单纯惩戒。",
            }
        )

    emotions = [
        {"group": "普通学生", "sentiment": "焦虑", "intensity": 0.55, "sample_comment": "能不能说清楚标准和范围？"},
        {"group": "宿舍长/楼委", "sentiment": "担忧", "intensity": 0.45, "sample_comment": "希望给个可操作的清单。"},
        {"group": "敏感群体", "sentiment": "抵触", "intensity": 0.65, "sample_comment": "别一刀切，给个申诉渠道。"},
    ]

    rewrites = [
        {"name": "更清晰", "pred_risk_score": max(5, score - 20), "text": "（兜底模式）请补充时间窗口、范围、替代方式与咨询渠道。", "why": "补齐关键信息，减少误读。"},
        {"name": "更安抚", "pred_risk_score": max(5, score - 15), "text": "（兜底模式）强调目的与减少打扰承诺，说明冲突可登记。", "why": "降低对抗情绪。"},
        {"name": "更可执行", "pred_risk_score": max(5, score - 25), "text": "（兜底模式）给出清单、流程、抽查范围与替代路径。", "why": "提高透明度与可执行性。"},
    ]

    return {
        "risk_score": int(score),
        "risk_level": level,
        "summary": "已生成风险点与改写建议（当前为兜底模式输出）。",
        "issues": issues,
        "student_emotions": emotions,
        "rewrites": rewrites,
    }

def analyze(text: str, scenario: str, profile: dict):
    system_prompt = (
        "你是高校舆情风险与学生情绪分析专家。"
        "你必须输出【严格 JSON】且只能输出 JSON，不能有任何解释、前后缀、代码块标记。"
        "JSON 必须可被 Python json.loads 直接解析。"
    )

    user_prompt = f"""
请分析下面高校文本的传播风险与学生情绪，并给出三种改写版本。

【场景】{scenario}

【受众画像】
- 年级/阶段：{profile.get("grade")}
- 身份：{profile.get("role")}
- 性别：{profile.get("gender")}
- 情绪敏感度：{profile.get("sensitivity")}
- 画像补充：{profile.get("custom")}

【原文】
{text}

【输出要求】请输出严格 JSON，结构如下（字段名必须一致）：
{{
  "risk_score": 0-100的整数,
  "risk_level": "LOW"|"MEDIUM"|"HIGH",
  "summary": "一句话结论（具体、可读）",
  "issues": [
    {{
      "title": "风险点标题",
      "evidence": "原文中触发风险的短语（必须来自原文，尽量 3-12 字）",
      "why": "原因（高校语境）",
      "rewrite_tip": "改写建议（具体怎么改）"
    }}
  ],
  "student_emotions": [
    {{
      "group": "学生群体名称",
      "sentiment": "主要情绪（中文短词，如：焦虑/抵触/困惑/担忧/紧张）",
      "intensity": 0到1的小数,
      "sample_comment": "一句典型评论（仿真口吻，口语化）"
    }}
  ],
  "rewrites": [
    {{
      "name": "必须为：更清晰 / 更安抚 / 更可执行",
      "pred_risk_score": 0-100整数,
      "text": "改写后的完整文本（含义一致，但表达要明显不同）",
      "why": "用 1-2 句话说明为何更稳（简短）"
    }}
  ]
}}

【硬性规则】
1) rewrites 必须且只能包含 3 个版本，按顺序输出：更清晰、更安抚、更可执行；
2) 每个版本必须补充“执行标准/时间范围/咨询或申诉渠道”中的至少一个；
3) intensity 必须在 0~1；
4) issues.evidence 必须能在原文中直接找到（不要写概括、不要写同义改写）。
"""

    try:
        content = call_deepseek(system_prompt, user_prompt)
        parsed, _ = safe_extract_json(content)
        if parsed is None:
            return local_fallback(text)

        rewrites = parsed.get("rewrites", []) or []
        buckets = {"更清晰": None, "更安抚": None, "更可执行": None}
        for rw in rewrites:
            n = (rw.get("name") or "").strip()
            if n in buckets and buckets[n] is None:
                rw["name"] = n
                buckets[n] = rw

        fixed = []
        for n in ["更清晰", "更安抚", "更可执行"]:
            if buckets[n] is not None:
                fixed.append(buckets[n])

        if len(fixed) < 3:
            for rw in rewrites:
                if rw not in fixed:
                    fixed.append(rw)
                if len(fixed) >= 3:
                    break

        parsed["rewrites"] = fixed[:3]
        return parsed
    except Exception:
        return local_fallback(text)

def clamp01(x):
    try:
        x = float(x)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, x))

def highlight_text_html(raw_text: str, phrases: list[str]) -> str:
    if not raw_text:
        return ""
    safe = html.escape(raw_text)

    uniq = []
    for p in phrases or []:
        p = (p or "").strip()
        if not p:
            continue
        if p not in raw_text:
            continue
        if p not in uniq:
            uniq.append(p)

    for p in sorted(uniq, key=len, reverse=True):
        safe_p = html.escape(p)
        safe = safe.replace(safe_p, f"<mark class='hl'>{safe_p}</mark>")

    return f"<div class='card' style='line-height:1.85;font-size:15px;'>{safe}</div>"

def render_overview(risk_score: int, risk_level: str, summary: str):
    pct = max(0, min(100, int(risk_score)))
    k1, k2, k3 = st.columns([1, 1, 2], gap="medium")

    with k1:
        st.markdown(
            f"""
            <div class="card">
              <div class="kpi-label">风险分数</div>
              <div class="kpi-value">{pct}</div>
              <div class="bar"><div style="width:{pct}%;"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        label = ("低" if risk_level == "LOW" else ("中" if risk_level == "MEDIUM" else "高"))
        st.markdown(
            f"""
            <div class="card">
              <div class="kpi-label">风险等级</div>
              <div class="kpi-value2">{risk_level}</div>
              <div class="muted" style="margin-top:8px;">{label}风险</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="card">
              <div class="kpi-label">结论</div>
              <div style="font-size:16px;font-weight:900;margin-top:10px;line-height:1.55;color:rgba(15,23,42,.92);">
                {html.escape(summary)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def tip_block():
    st.markdown(
        """
        <div class="tip">
          <div class="tip-title">通知小贴士</div>
          <div class="tip-text">撰写通知时应尽量涵盖时间窗口 / 执行范围 / 可替代方案 / 咨询渠道。<br>信息越完整，越不容易被误读噢💙</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def clipboard_copy_button(text: str, key: str):
    """复制按钮（JS clipboard）"""
    safe = json.dumps(text, ensure_ascii=False)
    components.html(
        f"""
        <div style="margin-top:2px;">
          <button id="btn-{key}" style="
            width:100%;
            border:1px solid rgba(37,99,235,.25);
            background: rgba(37,99,235,.08);
            color: rgba(37,99,235,1);
            padding:10px 12px;
            border-radius:14px;
            font-weight:900;
            cursor:pointer;
          ">复制该版本</button>
        </div>
        <script>
          const btn = document.getElementById("btn-{key}");
          btn.addEventListener("click", async () => {{
            try {{
              await navigator.clipboard.writeText({safe});
              btn.innerText = "已复制 ✓";
              setTimeout(() => btn.innerText = "复制该版本", 1200);
            }} catch (e) {{
              btn.innerText = "复制失败（请手动全选复制）";
              setTimeout(() => btn.innerText = "复制该版本", 1600);
            }}
          }});
        </script>
        """,
        height=52,
    )
def js_action_button(label: str, key: str) -> bool:
    """
    画一个和“复制该版本”同款样式的按钮。
    点击后用 st.session_state["_js_clicked_<key>"]=True 通知 Python。
    """
    flag = f"_js_clicked_{key}"
    if flag not in st.session_state:
        st.session_state[flag] = False

    components.html(
        f"""
        <div style="margin-top:2px;">
          <button id="btn-{key}" style="
            width:100%;
            border:1px solid rgba(37,99,235,.25);
            background: rgba(37,99,235,.08);
            color: rgba(37,99,235,1);
            padding:10px 12px;
            border-radius:14px;
            font-weight:900;
            font-size:15px;
            cursor:pointer;
          ">{html.escape(label)}</button>
        </div>
        <script>
          const btn = document.getElementById("btn-{key}");
          btn.addEventListener("click", () => {{
            const params = new URLSearchParams(window.location.search);
            params.set("{flag}", "1");
            window.location.search = params.toString();
          }});
        </script>
        """,
        height=52,
    )

    # 通过 query param 判断是否刚刚点了这个按钮
    qp = st.query_params
    if qp.get(flag) == "1":
        # 清掉 query param，避免刷新反复触发
        try:
            st.query_params.pop(flag)
        except Exception:
            pass
        return True

    return False

def pretty_notice(raw: str) -> str:
    """
    把模型输出的 markdown/奇怪转义，整理成更像群通知的排版：
    - 去掉 \1. 这种转义
    - 去掉 **加粗**、__加粗__、`代码`
    - 列表/编号分段更清楚
    """
    if not raw:
        return ""

    s = raw.replace("\r\n", "\n").replace("\r", "\n").strip()

    # 1) 去掉类似 "\1." "\2、" "\3)" 这种反斜杠转义
    s = re.sub(r"\\(?=\d+[\.\、\)])", "", s)

    # 2) 去掉 markdown 痕迹（粗体/下划线/代码）
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"__(.*?)__", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)

    # 3) 把 "- xxx" 变成更像群消息的 “· xxx”
    s = re.sub(r"(?m)^\s*-\s+", "· ", s)

    # 4) 编号行前插入空行
    s = re.sub(r"(?m)^(?=\d+[\.\、\)])", "\n", s)

    # 5) 常见 “【信息咨询】/【申诉与咨询】” 前加空行
    s = re.sub(r"\n?【", "\n\n【", s)

    # 6) 合并多余空行
    s = re.sub(r"\n{3,}", "\n\n", s).strip()

    return s

def add_emojis_smart(text: str) -> str:
    """在合适位置加少量 emoji（不刷屏），更像校园通知。"""
    if not text:
        return ""

    lines = text.split("\n")
    out = []

    for i, line in enumerate(lines):
        L = line.strip()
        if not L:
            out.append("")
            continue

        has_emoji_prefix = bool(re.match(r"^[\u2600-\u27BF\U0001F300-\U0001FAFF]", L))
        if not has_emoji_prefix:
            if i <= 1 and re.search(r"(同学|大家|各位)", L):
                L = "👋 " + L

            if re.search(r"(时间|今晚|明天|上午|下午|晚上|\d{1,2}[:：]\d{2})", L):
                L = "⏰ " + L
            elif re.search(r"(地点|位置|教室|楼|宿舍|会议室)", L):
                L = "📍 " + L
            elif re.search(r"(咨询|联系|沟通|电话|微信|邮箱)", L):
                L = "☎️ " + L
            elif re.search(r"(注意|提醒|请勿|禁止|务必|重要)", L):
                L = "⚠️ " + L
            elif re.search(r"(材料|附件|表格|申请|提交)", L):
                L = "📄 " + L
            elif re.search(r"(步骤|流程|操作|请按|依次)", L):
                L = "✅ " + L

        out.append(L)

    return "\n".join(out).strip()

# =========================
# Session state
# =========================
if "result" not in st.session_state:
    st.session_state.result = None
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = {"text": "", "scenario": "", "profile": {}}
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False

for k in ["更清晰", "更安抚", "更可执行"]:
    st.session_state.setdefault(f"emoji_on_{k}", False)

# =========================
# Input layout
# =========================
left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown('<div class="section-h">待发布文本</div>', unsafe_allow_html=True)
    text = st.text_area(
        " ",
        height=290,
        placeholder="粘贴或输入通知/公告/制度文本…",
        label_visibility="collapsed",
        value=st.session_state.last_inputs.get("text", ""),
    )
    tip_block()

with right:
    st.markdown('<div class="section-h">场景与受众</div>', unsafe_allow_html=True)

    st.markdown("**发布场景**")
    scenario = st.selectbox(
        " ",
        [
            "宿舍与安全管理通知",
            "课程/考试/成绩相关通知",
            "奖助学金/资助政策通知",
            "纪律处分/违纪处理通告",
            "校内活动/讲座报名通知",
            "疫情/卫生/公共安全通知",
            "其他（通用高校公告）",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("**受众画像**")
    c1, c2 = st.columns(2)
    with c1:
        grade = st.selectbox("年级/阶段", ["新生", "大二/大三", "大四/毕业班", "研究生", "混合群体"], index=1)
        role = st.selectbox("身份", ["普通学生", "宿舍长/楼委", "学生干部", "社团成员", "考研/保研群体", "留学生/交流生", "混合"], index=0)
    with c2:
        gender = st.selectbox("性别", ["不指定", "偏男性", "偏女性", "混合"], index=0)
        sensitivity = st.selectbox("情绪敏感度", ["低", "中", "高"], index=1)

    custom = st.text_input("画像补充（可选）", placeholder="例如：近期对宿舍检查较敏感，担心被通报。")
    profile = {"grade": grade, "role": role, "gender": gender, "sensitivity": sensitivity, "custom": custom}

    btn_area = st.empty()

# =========================
# Run button
# =========================
clicked = False
if st.session_state.is_loading:
    btn_area.markdown(
        "<div class='loading'>预测中… <span class='dots'><span></span><span></span><span></span></span></div>",
        unsafe_allow_html=True,
    )
else:
    clicked = btn_area.button("一键发布预测", type="primary", use_container_width=True)

if clicked:
    if not text.strip():
        st.warning("请先输入一段文本。")
    else:
        st.session_state.is_loading = True
        btn_area.markdown(
            "<div class='loading'>预测中… <span class='dots'><span></span><span></span><span></span></span></div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.05)

        with st.spinner("正在生成预测…"):
            result = analyze(text, scenario, profile)

        st.session_state.result = result
        st.session_state.last_inputs = {"text": text, "scenario": scenario, "profile": profile}
        st.session_state.is_loading = False
        st.rerun()

st.divider()

result = st.session_state.result
current_text = st.session_state.last_inputs.get("text", "")

# =========================
# Output
# =========================
if not result:
    st.info("请输入文本并点击「一键发布预测」。")
    st.stop()

render_overview(int(result.get("risk_score", 0)), result.get("risk_level", "LOW"), result.get("summary", ""))

issues = result.get("issues", []) or []
phrases = [(it.get("evidence") or "").strip() for it in issues if (it.get("evidence") or "").strip()]

if current_text.strip() and phrases:
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-h">原文标注</div>', unsafe_allow_html=True)
    st.markdown(highlight_text_html(current_text, phrases), unsafe_allow_html=True)

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# =========================
# Emotion Prediction
# =========================
st.markdown('<div class="section-h">情绪预测</div>', unsafe_allow_html=True)

risk_col, emo_col = st.columns([1.1, 1], gap="large")

with risk_col:
    st.markdown("**风险点**")
    issues = result.get("issues", []) or []
    if not issues:
        st.info("未识别到明显风险点。")
    else:
        options = [f"{i+1}. {it.get('title','(未命名)')}" for i, it in enumerate(issues)]
        selected = st.radio(" ", options=options, label_visibility="collapsed", key="risk_pick")
        idx = int(selected.split(".")[0]) - 1
        it = issues[idx]

        st.markdown(
            f"""
            <div class='rp-item'>
              <div style="font-weight:900; margin-bottom:8px; color:rgba(37,99,235,1);">
                触发片段：{html.escape(str(it.get('evidence','')))}
              </div>
              <div style="margin-top:6px; color:rgba(15,23,42,.88); line-height:1.75;">
                <b>原因：</b>{html.escape(str(it.get('why','')))}
              </div>
              <div style="margin-top:8px; color:rgba(15,23,42,.88); line-height:1.75;">
                <b>建议：</b>{html.escape(str(it.get('rewrite_tip','')))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with emo_col:
    st.markdown("**学生情绪**")
    emos = result.get("student_emotions", []) or []
    if not emos:
        st.info("未生成情绪画像。")
    else:
        for e in emos:
            emo = (e.get("sentiment") or "").strip()
            emoji = EMOJI_MAP.get(emo, "💭")
            intensity = clamp01(e.get("intensity", 0))
            group = e.get("group", "群体")
            comment = e.get("sample_comment", "")

            st.markdown(
                f"""
                <div style="margin-bottom:16px;">
                  <span class="blue-tag">{html.escape(str(group))}</span>
                  <span class="blue-tag">情绪：{html.escape(str(emo))} {emoji}</span>
                  <span class="blue-tag">强度：{intensity:.2f}</span>
                  <div class="bubble">{html.escape(str(comment))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# =========================
# Rewrite suggestions
# =========================
st.markdown('<div class="section-h">改写建议</div>', unsafe_allow_html=True)

rewrites = result.get("rewrites", []) or []
while len(rewrites) < 3:
    rewrites.append({"name": f"版本{len(rewrites)+1}", "pred_risk_score": "-", "text": "", "why": ""})
rewrites = rewrites[:3]

name_to_rw = {(rw.get("name") or "").strip(): rw for rw in rewrites}
tabs = st.tabs(["更清晰", "更安抚", "更可执行"])

for tname, tab in zip(["更清晰", "更安抚", "更可执行"], tabs):
    rw = name_to_rw.get(tname, {"name": tname, "pred_risk_score": "-", "text": "", "why": ""})
    rw["name"] = tname

    with tab:
        pr = rw.get("pred_risk_score", "-")
        why = rw.get("why", "")

        st.markdown(
            f"""
            <div class="card">
              <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
                <div style="font-weight:900; font-size:16px; line-height:1.25;">{html.escape(tname)}</div>
                <span class="blue-tag">预测风险 {html.escape(str(pr))}</span>
              </div>
              <div class="muted" style="margin-top:10px; font-size:13px; line-height:1.55;">
                {html.escape(str(why))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        emoji_key = f"emoji_on_{tname}"

        raw_txt = rw.get("text", "") or ""
        cleaned = pretty_notice(raw_txt)
        final_txt = add_emojis_smart(cleaned) if st.session_state[emoji_key] else cleaned

        safe_text = html.escape(final_txt).replace("\n", "<br>")
        st.markdown(
            f"""
            <div class="card" style="margin-top:12px; font-size:15px; line-height:1.85;">
              {safe_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

        b1, b2 = st.columns(2, gap="medium")
        with b1:
            clipboard_copy_button(final_txt, key=f"copy_{tname}")
        with b2:
            label = "取消emoji" if st.session_state[emoji_key] else "添加emoji"
            if js_action_button(label, key=f"emoji_{tname}"):
                st.session_state[emoji_key] = not st.session_state[emoji_key]
                st.rerun()

st.markdown(
    "<div class='footnote'>注：本工具用于文字优化与风险提示；不分析个人，不替代人工判断。</div>",
    unsafe_allow_html=True,
)

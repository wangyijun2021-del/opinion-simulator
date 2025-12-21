import os
import re
import json
import html
import requests
import streamlit as st

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="高校舆情风险与学生情绪预测系统",
    layout="wide",
)

# =========================
# Styles (formal + premium) + Color + Motion (no logic change)
# =========================
st.markdown(
    """
    <style>
      /* ---------- Page background (subtle animated gradient) ---------- */
      body{
        background:
          radial-gradient(1200px 600px at 15% 0%, rgba(59,130,246,.10), transparent 60%),
          radial-gradient(900px 500px at 85% 10%, rgba(16,185,129,.08), transparent 55%),
          radial-gradient(800px 520px at 60% 90%, rgba(245,158,11,.08), transparent 60%),
          #ffffff;
        animation: bgShift 14s ease-in-out infinite alternate;
      }
      @keyframes bgShift{
        0%{
          filter: hue-rotate(0deg);
          background-position: 0% 0%;
        }
        100%{
          filter: hue-rotate(8deg);
          background-position: 100% 100%;
        }
      }

      .block-container {padding-top: 2.0rem; padding-bottom: 2.0rem; max-width: 1120px;}
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      /* ---------- Header typography ---------- */
      .title {
        font-size: 34px;
        font-weight: 850;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
        position: relative;
      }
      .subtitle {
        color: rgba(17,24,39,.62);
        font-size: 14px;
        margin-bottom: 1.2rem;
        line-height: 1.6;
      }

      /* ---------- Section header ---------- */
      .section-h{
        font-size: 16px;
        font-weight: 800;
        margin: 0.2rem 0 0.8rem 0;
        border-left: 3px solid rgba(59,130,246,.55);
        padding-left: 10px;
      }

      /* ---------- Cards (hover + glass) ---------- */
      .card {
        background: rgba(255,255,255,.92);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,.06);
        border: 1px solid rgba(0,0,0,.04);
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        will-change: transform;
      }
      .card:hover{
        transform: translateY(-2px);
        box-shadow: 0 16px 40px rgba(0,0,0,.09);
        border-color: rgba(59,130,246,.18);
      }

      .kpi-label {color: rgba(17,24,39,.55); font-size: 12px; letter-spacing: .06em;}
      .kpi-value {font-size: 34px; font-weight: 850; margin-top: 6px;}
      .kpi-value2 {font-size: 22px; font-weight: 850; margin-top: 10px;}
      .muted {color: rgba(17,24,39,.62);}
      .mono {font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;}

      .badge {
        display:inline-flex; align-items:center;
        padding: 5px 10px; border-radius: 999px; font-size: 12px;
        border: 1px solid rgba(0,0,0,.08);
        color: rgba(17,24,39,.85);
        background: rgba(255,255,255,.78);
        margin-right: 6px; margin-bottom: 6px;
        transition: transform .18s ease, border-color .18s ease;
      }
      .badge:hover{ transform: translateY(-1px); border-color: rgba(16,185,129,.18); }

      /* ---------- Progress bar (animated fill) ---------- */
      .bar {height: 10px; border-radius: 999px; background: rgba(17,24,39,.08); overflow: hidden; margin-top: 10px;}
      .bar > div {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, rgba(59,130,246,.95), rgba(16,185,129,.85));
        animation: fillGrow .9s ease-out both;
        transform-origin: left;
      }
      @keyframes fillGrow{
        from { transform: scaleX(0.2); filter: blur(.2px); }
        to   { transform: scaleX(1);   filter: blur(0); }
      }

      /* ---------- Highlight ---------- */
      mark.hl {
        background: rgba(245, 158, 11, 0.25);
        color: inherit;
        padding: 0 .18em;
        border-radius: .35em;
        box-shadow: inset 0 0 0 1px rgba(245,158,11,.10);
        transition: background .18s ease;
      }
      mark.hl:hover{
        background: rgba(245, 158, 11, 0.32);
      }

      /* ---------- Compact text ---------- */
      .clamp2{
        display:-webkit-box;
        -webkit-line-clamp:2;
        -webkit-box-orient:vertical;
        overflow:hidden;
      }
      .clamp3{
        display:-webkit-box;
        -webkit-line-clamp:3;
        -webkit-box-orient:vertical;
        overflow:hidden;
      }

      .pill{
        font-size:12px; padding:4px 10px; border-radius:999px;
        border:1px solid rgba(0,0,0,.08);
        background:rgba(255,255,255,.78);
        color:rgba(17,24,39,.78);
        white-space:nowrap;
      }

      .footnote {
        color: rgba(17,24,39,.48);
        font-size: 12px;
        margin-top: 18px;
      }

      /* ---------- Illustration container (animated SVG strokes) ---------- */
      .illu {
        margin-top: 14px;
        padding: 16px;
        border-radius: 16px;
        background:
          radial-gradient(600px 120px at 20% 0%, rgba(59,130,246,.10), transparent 60%),
          rgba(59,130,246,0.04);
        border: 1px solid rgba(0,0,0,.04);
        display: flex;
        align-items: center;
        gap: 16px;
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
      }
      .illu:hover{
        transform: translateY(-2px);
        box-shadow: 0 16px 40px rgba(0,0,0,.06);
        border-color: rgba(59,130,246,.14);
      }
      .illu-text {
        color: rgba(17,24,39,.55);
        font-size: 13px;
        line-height: 1.55;
      }
      .illu svg path, .illu svg circle{
        stroke-dasharray: 800;
        stroke-dashoffset: 800;
        animation: drawLine 1.1s ease-out forwards;
      }
      .illu svg circle{
        stroke-dasharray: 40;
        stroke-dashoffset: 40;
      }
      @keyframes drawLine{
        to{ stroke-dashoffset: 0; }
      }

      /* ---------- Streamlit widgets polish ---------- */
      /* Primary button: subtle pulse highlight */
      div.stButton > button[kind="primary"]{
        border-radius: 14px !important;
        padding: 0.75rem 1rem !important;
        background: linear-gradient(90deg, rgba(239,68,68,.92), rgba(245,158,11,.80)) !important;
        border: 1px solid rgba(0,0,0,.06) !important;
        box-shadow: 0 14px 30px rgba(239,68,68,.18) !important;
        transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
        position: relative;
        overflow: hidden;
      }
      div.stButton > button[kind="primary"]::after{
        content:"";
        position:absolute; inset:-40% -60%;
        background: linear-gradient(120deg, transparent, rgba(255,255,255,.35), transparent);
        transform: translateX(-60%) rotate(12deg);
        animation: shine 2.8s ease-in-out infinite;
      }
      @keyframes shine{
        0%{ transform: translateX(-60%) rotate(12deg); opacity: 0; }
        25%{ opacity: .9; }
        60%{ opacity: .6; }
        100%{ transform: translateX(80%) rotate(12deg); opacity: 0; }
      }
      div.stButton > button[kind="primary"]:hover{
        transform: translateY(-1px);
        filter: saturate(1.05);
        box-shadow: 0 18px 38px rgba(239,68,68,.22) !important;
      }

      /* Text area / inputs: softer corners */
      textarea, input{
        border-radius: 14px !important;
      }

      /* Tabs: make it look cleaner */
      button[data-baseweb="tab"]{
        font-weight: 750 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Header
# =========================
st.markdown('<div class="title">高校舆情风险与学生情绪预测系统</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div style="position:relative; margin-top:-8px;">
      <div style="position:absolute; right:0; top:-22px; opacity:0.12; pointer-events:none;">
        <svg width="260" height="140" viewBox="0 0 260 140" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M30 95C70 55 115 45 150 55C185 65 210 90 235 115" stroke="#111827" stroke-width="2"/>
          <path d="M40 110C85 80 125 75 155 82C185 89 205 105 225 125" stroke="#111827" stroke-width="2"/>
          <circle cx="55" cy="78" r="4" fill="#111827"/>
          <circle cx="160" cy="60" r="4" fill="#111827"/>
          <circle cx="210" cy="108" r="4" fill="#111827"/>
        </svg>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">输入通知/公告/制度文本，选择场景与受众画像，系统给出风险点、学生情绪态势与改写建议。</div>',
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
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
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
                "evidence": hits[0] if hits else "",
                "why": "学生容易解读为高压或“结果已定”，引发抵触、吐槽与二次传播。",
                "rewrite_tip": "补充依据与范围，明确流程与咨询渠道；用“提醒+规范+支持”替代单纯惩戒。",
            }
        )

    emotions = [
        {"group": "普通学生", "sentiment": "紧张/被约束", "intensity": 0.55, "sample_comment": "能不能说清楚标准和范围？"},
        {"group": "宿舍长/楼委", "sentiment": "配合但担心执行成本", "intensity": 0.45, "sample_comment": "希望给个可操作的清单。"},
        {"group": "敏感群体", "sentiment": "警惕/抵触", "intensity": 0.65, "sample_comment": "别一刀切，给个申诉渠道。"},
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
      "sentiment": "主要情绪",
      "intensity": 0到1的小数,
      "sample_comment": "一句典型评论（仿真口吻）"
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

    return f"<div class='card' style='line-height:1.8;font-size:15px;'>{safe}</div>"


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
              <div style="font-size:16px;font-weight:780;margin-top:10px;line-height:1.5;">
                {html.escape(summary)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_student_illustration():
    # Cute but restrained: campus vibe (no emoji, no cartoon faces)
    st.markdown(
        """
        <div class="illu">
          <svg width="120" height="86" viewBox="0 0 240 172" fill="none" xmlns="http://www.w3.org/2000/svg" style="opacity:.75;">
            <!-- ground -->
            <path d="M18 146C52 132 88 126 120 126C152 126 188 132 222 146" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
            <!-- simple building -->
            <path d="M52 138V78L92 56L132 78V138" stroke="#3B82F6" stroke-width="3" stroke-linejoin="round"/>
            <path d="M70 138V96H114V138" stroke="#3B82F6" stroke-width="3" stroke-linejoin="round"/>
            <path d="M78 106H106" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/>
            <!-- small figures (abstract) -->
            <circle cx="162" cy="108" r="6" fill="#10B981"/>
            <path d="M162 116V132" stroke="#10B981" stroke-width="3" stroke-linecap="round"/>
            <path d="M154 124H170" stroke="#10B981" stroke-width="3" stroke-linecap="round"/>
            <circle cx="190" cy="112" r="6" fill="#10B981"/>
            <path d="M190 120V134" stroke="#10B981" stroke-width="3" stroke-linecap="round"/>
            <path d="M182 128H198" stroke="#10B981" stroke-width="3" stroke-linecap="round"/>
            <!-- sky lines -->
            <path d="M146 44C168 30 190 28 214 36" stroke="#111827" stroke-width="2" stroke-linecap="round" opacity="0.45"/>
            <path d="M150 58C176 46 196 46 220 54" stroke="#111827" stroke-width="2" stroke-linecap="round" opacity="0.35"/>
          </svg>
          <div class="illu-text">
            把通知当作一次“对话”来设计：明确边界、解释原因、给出选项与渠道，往往比强调命令更有效。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rewrite_fulltext(rw: dict):
    pr = rw.get("pred_risk_score", "-")
    why = rw.get("why", "")
    txt = rw.get("text", "")

    st.markdown(
        f"""
        <div class="card">
          <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
            <div style="font-weight:850; font-size:14px; line-height:1.25;">{html.escape(str(rw.get("name","")))}</div>
            <div class="pill">预测风险 {html.escape(str(pr))}</div>
          </div>
          <div class="muted clamp3" style="margin-top:10px; font-size:13px; line-height:1.45;">
            {html.escape(str(why))}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Full text shown directly (no expander)
    safe_text = html.escape(str(txt)).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="card" style="margin-top:12px; font-size:15px; line-height:1.78;">
          {safe_text}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Session state
# =========================
if "result" not in st.session_state:
    st.session_state.result = None
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = {"text": "", "scenario": "", "profile": {}}

# =========================
# Input layout
# =========================
left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown('<div class="section-h">待发布文本</div>', unsafe_allow_html=True)
    text = st.text_area(
        " ",
        height=260,
        placeholder="粘贴或输入通知/公告/制度文本…",
        label_visibility="collapsed",
        value=st.session_state.last_inputs.get("text", ""),
    )

    # illustration (same as before, now animated via CSS)
    render_student_illustration()

with right:
    st.markdown('<div class="section-h">场景与受众</div>', unsafe_allow_html=True)

    scenario = st.selectbox(
        "发布场景",
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
    )

    st.markdown("**受众画像（高校版）**")
    c1, c2 = st.columns(2)
    with c1:
        grade = st.selectbox("年级/阶段", ["新生", "大二/大三", "大四/毕业班", "研究生", "混合群体"], index=1)
        role = st.selectbox("身份", ["普通学生", "宿舍长/楼委", "学生干部", "社团成员", "考研/保研群体", "留学生/交流生", "混合"], index=0)
    with c2:
        gender = st.selectbox("性别", ["不指定", "偏男性", "偏女性", "混合"], index=0)
        sensitivity = st.selectbox("情绪敏感度", ["低", "中", "高"], index=1)

    custom = st.text_input("画像补充（可选）", placeholder="例如：近期对宿舍检查较敏感，担心被通报。")

    profile = {
        "grade": grade,
        "role": role,
        "gender": gender,
        "sensitivity": sensitivity,
        "custom": custom,
    }

    analyze_btn = st.button("分析并生成改写", type="primary", use_container_width=True)

st.divider()

# =========================
# Run
# =========================
if analyze_btn:
    if not text.strip():
        st.warning("请先输入一段文本。")
    else:
        with st.spinner("正在分析…"):
            result = analyze(text, scenario, profile)
        st.session_state.result = result
        st.session_state.last_inputs = {"text": text, "scenario": scenario, "profile": profile}

result = st.session_state.result
current_text = st.session_state.last_inputs.get("text", "")

# =========================
# Output
# =========================
if not result:
    st.info("请输入文本并点击「分析并生成改写」。")
else:
    render_overview(int(result.get("risk_score", 0)), result.get("risk_level", "LOW"), result.get("summary", ""))

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ---- Rewrite area: show full text directly ----
    st.markdown('<div class="section-h">改写建议</div>', unsafe_allow_html=True)

    rewrites = result.get("rewrites", []) or []
    while len(rewrites) < 3:
        rewrites.append({"name": f"版本{len(rewrites)+1}", "pred_risk_score": "-", "text": "", "why": ""})
    rewrites = rewrites[:3]

    name_to_rw = { (rw.get("name") or "").strip(): rw for rw in rewrites }
    tabs = st.tabs(["更清晰", "更安抚", "更可执行"])
    for tname, tab in zip(["更清晰", "更安抚", "更可执行"], tabs):
        rw = name_to_rw.get(tname, {"name": tname, "pred_risk_score": "-", "text": "", "why": ""})
        rw["name"] = tname
        with tab:
            render_rewrite_fulltext(rw)

    # ---- Detailed analysis: risk + emotion ----
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    with st.expander("查看详细分析", expanded=False):
        tab1, tab2 = st.tabs(["风险点", "学生情绪"])

        with tab1:
            issues = result.get("issues", []) or []
            if not issues:
                st.info("未识别到明显风险点。")
            else:
                phrases = []
                for it in issues:
                    ev = (it.get("evidence") or "").strip()
                    if ev:
                        phrases.append(ev)

                st.markdown("**原文（标注）**")
                st.markdown(highlight_text_html(current_text, phrases), unsafe_allow_html=True)

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                st.markdown("**风险点列表**")
                for i, it in enumerate(issues, start=1):
                    st.markdown(f"**{i}. {it.get('title','(未命名)')}**")
                    st.markdown(f"- 触发片段：{it.get('evidence','')}")
                    st.markdown(f"- 原因：{it.get('why','')}")
                    st.markdown(f"- 建议：{it.get('rewrite_tip','')}")
                    st.divider()

        with tab2:
            emos = result.get("student_emotions", []) or []
            if not emos:
                st.info("未生成情绪画像。")
            else:
                for e in emos:
                    intensity = clamp01(e.get("intensity", 0))
                    st.markdown(
                        f"""
                        <div class='card'>
                          <div>
                            <span class='badge'>{html.escape(str(e.get('group','群体')))}</span>
                            <span class='badge'>情绪：{html.escape(str(e.get('sentiment','')))}</span>
                            <span class='badge'>强度：{intensity:.2f}</span>
                          </div>
                          <div style='margin-top:10px;' class='mono'>“{html.escape(str(e.get('sample_comment','')))}”</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.write("")

st.markdown(
    "<div class='footnote'>注：本工具用于文字优化与风险提示；不分析个人，不替代人工判断。</div>",
    unsafe_allow_html=True,
)

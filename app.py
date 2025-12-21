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
    page_title="清小知｜高校通知小助手",
    layout="wide",
)

# =========================
# Styles (formal + premium + subtle motion)
# =========================
st.markdown(
    """
    <style>
      /* ✅ Streamlit 的实际背景容器不是 body，必须覆盖这些 */
      .stApp,
      [data-testid="stAppViewContainer"],
      body{
        background:
          radial-gradient(1200px 600px at 18% 0%, rgba(59,130,246,.12), transparent 62%),
          radial-gradient(900px 500px at 86% 12%, rgba(16,185,129,.10), transparent 58%),
          linear-gradient(180deg, rgba(236,246,255,1) 0%, rgba(246,250,255,1) 55%, rgba(255,255,255,1) 100%) !important;
      }

      .block-container {padding-top: 1.8rem; padding-bottom: 2.2rem; max-width: 1120px;}
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      /* Header */
      .hero{
        position: relative;
        margin: 0 0 1.2rem 0;
        padding: 0.2rem 0 0.4rem 0;
        text-align: center;
      }
      .hero::before{
        content:"";
        position:absolute;
        left:50%;
        top:-18px;
        transform:translateX(-50%);
        width: 520px;
        height: 140px;
        background:
          radial-gradient(220px 120px at 30% 40%, rgba(59,130,246,.16), transparent 65%),
          radial-gradient(220px 120px at 70% 45%, rgba(99,102,241,.12), transparent 70%);
        filter: blur(12px);
        opacity: .95;
        pointer-events:none;
        z-index:0;
      }

      .brand-title{
        position: relative;
        z-index: 1;
        font-size: 44px;
        font-weight: 900;
        letter-spacing: -0.03em;
        line-height: 1.0;
        display: inline-block;

        background: linear-gradient(90deg,
          rgba(17,24,39,1) 0%,
          rgba(37,99,235,1) 30%,
          rgba(79,70,229,1) 70%,
          rgba(17,24,39,1) 100%);
        background-size: 220% 100%;
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;

        animation: titleFlow 8s ease-in-out infinite;
        transform: translateY(0);
      }
      @keyframes titleFlow{
        0%{background-position: 0% 50%;}
        50%{background-position: 100% 50%;}
        100%{background-position: 0% 50%;}
      }
      .brand-title:hover{
        filter: drop-shadow(0 18px 35px rgba(37,99,235,.18));
        transform: translateY(-1px);
        transition: 220ms ease;
      }

      .brand-subtitle{
        position: relative;
        z-index: 1;
        margin-top: 0.6rem;
        color: rgba(17,24,39,.62);
        font-size: 14px;
        line-height: 1.6;
        display:inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        border: 1px solid rgba(0,0,0,.06);
        background: rgba(255,255,255,.72);
        box-shadow: 0 10px 26px rgba(0,0,0,.06);
        backdrop-filter: blur(6px);
      }

      /* Section heading */
      .section-h{
        font-size: 16px;
        font-weight: 800;
        margin: 0.2rem 0 0.8rem 0;
        border-left: 3px solid rgba(37,99,235,.45);
        padding-left: 10px;
      }

      /* Cards */
      .card {
        background: rgba(255,255,255,.90);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,.06);
        border: 1px solid rgba(0,0,0,.04);
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
        background: rgba(255,255,255,.74);
        margin-right: 6px; margin-bottom: 6px;
      }

      .bar {height: 10px; border-radius: 999px; background: rgba(17,24,39,.08); overflow: hidden; margin-top: 10px;}
      .bar > div {height: 100%; border-radius: 999px; background: rgba(37,99,235,.86);}

      /* Highlight */
      mark.hl {
        background: rgba(245, 158, 11, 0.25);
        color: inherit;
        padding: 0 .18em;
        border-radius: .35em;
      }

      /* Compact text */
      .clamp3{
        display:-webkit-box;
        -webkit-line-clamp:3;
        -webkit-box-orient:vertical;
        overflow:hidden;
      }
      .pill{
        font-size:12px; padding:4px 10px; border-radius:999px;
        border:1px solid rgba(0,0,0,.08);
        background:rgba(255,255,255,.72);
        color:rgba(17,24,39,.78);
        white-space:nowrap;
      }

      .footnote {
        color: rgba(17,24,39,.48);
        font-size: 12px;
        margin-top: 18px;
        text-align:center;
      }

      /* Tip block */
      .tip {
        margin-top: 14px;
        padding: 14px 16px;
        border-radius: 16px;
        border: 1px solid rgba(37,99,235,.10);
        background:
          linear-gradient(180deg, rgba(37,99,235,.08), rgba(99,102,241,.06));
        box-shadow: 0 12px 30px rgba(0,0,0,.06);
        position: relative;
        overflow: hidden;
      }
      .tip::after{
        content:"";
        position:absolute;
        top:-40%;
        left:-30%;
        width: 60%;
        height: 180%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,.62), transparent);
        transform: rotate(18deg);
        animation: shimmer 5.8s ease-in-out infinite;
        opacity: .65;
        pointer-events:none;
      }
      @keyframes shimmer{
        0%{transform: translateX(-40%) rotate(18deg);}
        50%{transform: translateX(140%) rotate(18deg);}
        100%{transform: translateX(-40%) rotate(18deg);}
      }
      .tip-h{
        font-weight: 850;
        font-size: 13px;
        color: rgba(17,24,39,.88);
        margin-bottom: 6px;
      }
      .tip-t{
        color: rgba(17,24,39,.62);
        font-size: 13px;
        line-height: 1.65;
        white-space: pre-line;
      }

      /* Primary button (cool + animated) */
      div.stButton > button[kind="primary"]{
        width: 100%;
        border: 1px solid rgba(255,255,255,.18) !important;
        background: linear-gradient(90deg, rgba(37,99,235,1), rgba(79,70,229,1), rgba(14,165,233,1)) !important;
        background-size: 220% 100% !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        border-radius: 14px !important;
        padding: 0.85rem 1.1rem !important;
        box-shadow: 0 18px 40px rgba(37,99,235,.22) !important;
        transform: translateY(0px);
        transition: transform 160ms ease, box-shadow 200ms ease, filter 200ms ease;
        animation: btnFlow 7.5s ease-in-out infinite, btnGlow 3.6s ease-in-out infinite;
      }
      @keyframes btnFlow{
        0%{background-position: 0% 50%;}
        50%{background-position: 100% 50%;}
        100%{background-position: 0% 50%;}
      }
      @keyframes btnGlow{
        0%,100%{box-shadow: 0 18px 40px rgba(37,99,235,.18);}
        50%{box-shadow: 0 22px 52px rgba(79,70,229,.26);}
      }
      div.stButton > button[kind="primary"]:hover{
        transform: translateY(-2px);
        filter: brightness(1.03) saturate(1.05);
        box-shadow: 0 26px 60px rgba(37,99,235,.26) !important;
      }
      div.stButton > button[kind="primary"]:active{
        transform: translateY(1px) scale(0.99);
        box-shadow: 0 14px 34px rgba(37,99,235,.18) !important;
      }
      div.stButton > button[kind="primary"] p{
        font-size: 18px !important;
        letter-spacing: .02em;
      }

      /* ✅ Loading state: disabled primary button shows animated dots */
      div.stButton > button[kind="primary"][disabled]{
        cursor: wait !important;
        filter: saturate(0.98) brightness(0.98);
      }
      div.stButton > button[kind="primary"][disabled] p::after{
        content: "...";
        display: inline-block;
        width: 18px;
        overflow: hidden;
        vertical-align: bottom;
        margin-left: 8px;
        animation: dots 1.2s steps(4,end) infinite;
      }
      @keyframes dots{
        0%{width:0px;}
        100%{width:18px;}
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
      <div class="brand-title">清小知</div>
      <div style="margin-top:10px;">
        <div class="brand-subtitle">高校通知小助手｜让通知更容易被理解</div>
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


def render_tip_block():
    tip_text = (
        "撰写通知时应尽量涵盖时间窗口 / 执行范围 / 可替代方案 / 咨询渠道。\n"
        "信息越完整，越不容易被误读噢💙"
    )
    st.markdown(
        f"""
        <div class="tip">
          <div class="tip-h">通知小贴士</div>
          <div class="tip-t">{html.escape(tip_text)}</div>
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

    safe_text = html.escape(str(txt)).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="card" style="margin-top:12px; font-size:15px; line-height:1.78;">
          {safe_text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def extract_phrases_from_result(res: dict) -> list[str]:
    phrases = []
    if not res:
        return phrases
    for it in (res.get("issues", []) or []):
        ev = (it.get("evidence") or "").strip()
        if ev:
            phrases.append(ev)
    seen = set()
    out = []
    for p in phrases:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


# =========================
# Session state
# =========================
if "result" not in st.session_state:
    st.session_state.result = None
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = {"text": "", "scenario": "", "profile": {}}
if "run_pending" not in st.session_state:
    st.session_state.run_pending = False

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

    # ✅ 预测后：直接在这里显示风险高亮（不再放折叠里）
    if st.session_state.result and st.session_state.last_inputs.get("text", "").strip():
        phrases = extract_phrases_from_result(st.session_state.result)
        if phrases:
            st.markdown('<div class="section-h" style="margin-top:14px;">原文（高亮标注）</div>', unsafe_allow_html=True)
            st.markdown(
                highlight_text_html(st.session_state.last_inputs.get("text", ""), phrases),
                unsafe_allow_html=True,
            )
        else:
            render_tip_block()
    else:
        render_tip_block()

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

    st.markdown("**受众画像**")
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

    # ✅ Loading-state button
    btn_slot = st.empty()

    if st.session_state.run_pending:
        btn_slot.button("预测中", type="primary", use_container_width=True, disabled=True)
    else:
        clicked = btn_slot.button("发布预测", type="primary", use_container_width=True)
        if clicked:
            if not text.strip():
                st.warning("请先输入一段文本。")
            else:
                st.session_state.run_pending = True
                st.session_state.last_inputs = {"text": text, "scenario": scenario, "profile": profile}
                st.rerun()

st.divider()

# =========================
# Run pending job (2nd pass)
# =========================
if st.session_state.run_pending:
    _text = st.session_state.last_inputs.get("text", "")
    _scenario = st.session_state.last_inputs.get("scenario", "宿舍与安全管理通知")
    _profile = st.session_state.last_inputs.get("profile", {})

    res = analyze(_text, _scenario, _profile)
    st.session_state.result = res

    st.session_state.run_pending = False
    st.rerun()

result = st.session_state.result
current_text = st.session_state.last_inputs.get("text", "")

# =========================
# Output
# =========================
if not result:
    st.info("请输入文本并点击「发布预测」。")
else:
    render_overview(int(result.get("risk_score", 0)), result.get("risk_level", "LOW"), result.get("summary", ""))

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ✅ 2) 不折叠：并列板块；✅ 3) 放在改写建议之前；✅ 改名为「情绪预测」
    st.markdown('<div class="section-h">情绪预测</div>', unsafe_allow_html=True)
    cL, cR = st.columns([1.15, 1.0], gap="large")

    with cL:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**风险点**")
        issues = result.get("issues", []) or []
        if not issues:
            st.info("未识别到明显风险点。")
        else:
            for i, it in enumerate(issues, start=1):
                st.markdown(f"**{i}. {it.get('title','(未命名)')}**")
                st.markdown(f"- 触发片段：{it.get('evidence','')}")
                st.markdown(f"- 原因：{it.get('why','')}")
                st.markdown(f"- 建议：{it.get('rewrite_tip','')}")
                if i != len(issues):
                    st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)

    with cR:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**学生情绪**")
        emos = result.get("student_emotions", []) or []
        if not emos:
            st.info("未生成情绪画像。")
        else:
            for e in emos:
                intensity = clamp01(e.get("intensity", 0))
                st.markdown(
                    f"""
                    <div style="margin-top:10px;">
                      <span class='badge'>{html.escape(str(e.get('group','群体')))}</span>
                      <span class='badge'>情绪：{html.escape(str(e.get('sentiment','')))}</span>
                      <span class='badge'>强度：{intensity:.2f}</span>
                      <div style='margin-top:8px;' class='mono'>“{html.escape(str(e.get('sample_comment','')))}”</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ---- Rewrite area ----
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
            render_rewrite_fulltext(rw)

st.markdown(
    "<div class='footnote'>注：本工具用于文字优化与风险提示；不分析个人，不替代人工判断。</div>",
    unsafe_allow_html=True,
)

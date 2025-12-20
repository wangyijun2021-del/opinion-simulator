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
# Styles (formal + premium)
# =========================
st.markdown(
    """
    <style>
      body{
        background:
          radial-gradient(1200px 600px at 15% 0%, rgba(59,130,246,.08), transparent 60%),
          radial-gradient(900px 500px at 85% 10%, rgba(16,185,129,.06), transparent 55%),
          #ffffff;
      }
      .block-container {padding-top: 2.0rem; padding-bottom: 2.0rem; max-width: 1120px;}
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      .title {
        font-size: 34px;
        font-weight: 850;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
      }
      .subtitle {
        color: rgba(17,24,39,.62);
        font-size: 14px;
        margin-bottom: 1.2rem;
        line-height: 1.6;
      }

      .section-h{
        font-size: 16px;
        font-weight: 800;
        margin: 0.2rem 0 0.8rem 0;
        border-left: 3px solid rgba(59,130,246,.45);
        padding-left: 10px;
      }

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
      .bar > div {height: 100%; border-radius: 999px; background: rgba(59,130,246,.86);}

      /* Highlight */
      mark.hl {
        background: rgba(245, 158, 11, 0.25);
        color: inherit;
        padding: 0 .18em;
        border-radius: .35em;
      }

      /* Compact text */
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
        background:rgba(255,255,255,.72);
        color:rgba(17,24,39,.78);
        white-space:nowrap;
      }

      .footnote {
        color: rgba(17,24,39,.48);
        font-size: 12px;
        margin-top: 18px;
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

        # Normalize rewrites to fixed names/order
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

        # Fill missing with any leftovers
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
            "疫情

import os
import re
import json
import html
import hashlib
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
        background: rgba(255,255,255,.92);
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

      mark.hl {
        background: rgba(245, 158, 11, 0.25);
        color: inherit;
        padding: 0 .18em;
        border-radius: .35em;
      }

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

      /* Brand illustration strip: NO text, just visual */
      .brand-strip{
        margin-top: 14px;
        border-radius: 18px;
        background:
          radial-gradient(900px 160px at 30% 20%, rgba(59,130,246,.10), transparent 60%),
          radial-gradient(900px 160px at 70% 30%, rgba(16,185,129,.08), transparent 60%),
          rgba(255,255,255,.80);
        border: 1px solid rgba(0,0,0,.04);
        box-shadow: 0 10px 30px rgba(0,0,0,.05);
        padding: 10px 14px;
        overflow: hidden;
      }
      .brand-strip svg{ display:block; width:100%; height:96px; opacity:0.95; }

      .footnote {
        color: rgba(17,24,39,.48);
        font-size: 12px;
        margin-top: 18px;
      }

      /* Make code blocks look premium */
      pre {
        border-radius: 14px !important;
        border: 1px solid rgba(0,0,0,.06) !important;
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


# -------------------------
# Brand illustration system (no text, consistent style)
# -------------------------
def _svg_strip_dorm():
    return """
    <svg viewBox="0 0 1100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M40 88C140 64 246 56 355 56C464 56 570 64 670 88C780 106 900 106 1060 78"
            stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.65"/>
      <path d="M125 92V44L215 18L305 44V92" stroke="#3B82F6" stroke-width="3" stroke-linejoin="round" opacity="0.85"/>
      <path d="M155 92V58H275V92" stroke="#3B82F6" stroke-width="3" stroke-linejoin="round" opacity="0.85"/>
      <path d="M175 68H255" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.85"/>
      <circle cx="455" cy="64" r="8" fill="#10B981" opacity="0.75"/>
      <path d="M455 74V96" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.75"/>
      <path d="M441 84H469" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.75"/>
      <circle cx="510" cy="66" r="8" fill="#10B981" opacity="0.65"/>
      <path d="M510 76V96" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.65"/>
      <path d="M496 86H524" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.65"/>
      <path d="M760 26C820 10 890 12 960 34" stroke="#111827" stroke-width="2" stroke-linecap="round" opacity="0.25"/>
      <path d="M780 44C840 32 900 34 980 52" stroke="#111827" stroke-width="2" stroke-linecap="round" opacity="0.18"/>
    </svg>
    """


def _svg_strip_exam():
    return """
    <svg viewBox="0 0 1100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M60 86C190 60 320 52 440 56C560 60 680 78 820 86C940 92 1020 88 1060 78"
            stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
      <path d="M160 24H360V88H160V24Z" stroke="#3B82F6" stroke-width="3" opacity="0.85"/>
      <path d="M190 42H330" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.75"/>
      <path d="M190 58H310" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.65"/>
      <path d="M190 74H290" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
      <path d="M480 30C520 18 560 18 600 30" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
      <path d="M540 30V88" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
      <circle cx="760" cy="62" r="10" fill="#10B981" opacity="0.55"/>
      <path d="M760 74V92" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
      <path d="M742 84H778" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
      <path d="M850 26C910 10 980 12 1040 34" stroke="#111827" stroke-width="2" stroke-linecap="round" opacity="0.22"/>
    </svg>
    """


def _svg_strip_event():
    return """
    <svg viewBox="0 0 1100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M50 88C180 70 300 56 420 56C540 56 660 70 790 88C920 106 1000 104 1060 90"
            stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
      <path d="M170 84V44C170 32 180 22 192 22H314C326 22 336 32 336 44V84"
            stroke="#3B82F6" stroke-width="3" opacity="0.85"/>
      <path d="M198 38H308" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.75"/>
      <path d="M198 54H290" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.65"/>
      <path d="M520 30L560 76L600 30" stroke="#10B981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
      <circle cx="560" cy="82" r="7" fill="#10B981" opacity="0.55"/>
      <path d="M720 34C780 18 840 18 900 34" stroke="#111827" stroke-width="2" stroke-linecap="round" opacity="0.18"/>
      <path d="M740 50C800 36 860 36 940 52" stroke="#111827" stroke-width="2" stroke-linecap="round" opacity="0.13"/>
    </svg>
    """


def _svg_strip_policy():
    return """
    <svg viewBox="0 0 1100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M60 86C200 60 340 50 470 56C600 62 720 84 860 88C980 92 1030 86 1060 76"
            stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
      <path d="M170 22H340V92H170V22Z" stroke="#3B82F6" stroke-width="3" opacity="0.85"/>
      <path d="M200 42H310" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.75"/>
      <path d="M200 60H290" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.65"/>
      <path d="M200 78H270" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
      <path d="M520 28C560 16 600 16 640 28" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
      <path d="M540 40H620" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
      <path d="M560 52H600" stroke="#10B981" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
      <path d="M820 30C880 12 950 14 1030 40" stroke="#111827" stroke-width="2" stroke-linecap="round" opacity="0.18"/>
    </svg>
    """


def get_brand_svg_for_scenario(scenario: str) -> str:
    # map to consistent brand illustrations
    mapping = {
        "宿舍与安全管理通知": _svg_strip_dorm,
        "课程/考试/成绩相关通知": _svg_strip_exam,
        "校内活动/讲座报名通知": _svg_strip_event,
        "奖助学金/资助政策通知": _svg_strip_policy,
        "纪律处分/违纪处理通告": _svg_strip_policy,
        "疫情/卫生/公共安全通知": _svg_strip_dorm,
        "其他（通用高校公告）": _svg_strip_event,
    }
    fn = mapping.get(scenario, _svg_strip_event)
    return fn()


def render_brand_strip(scenario: str):
    svg = get_brand_svg_for_scenario(scenario)
    st.markdown(f"<div class='brand-strip'>{svg}</div>", unsafe_allow_html=True)


# -------------------------
# Publish-ready formatting
# -------------------------
def normalize_text_for_render(text: str) -> str:
    return (text or "").strip().replace("\r\n", "\n").replace("\r", "\n")


def format_for_channel(rewrite_text: str, channel: str, scenario: str) -> str:
    """
    Turn the rewrite into ready-to-send layouts.
    Keep it deterministic and simple (product-ish).
    """
    t = normalize_text_for_render(rewrite_text)

    # If model outputs a long paragraph, keep it as-is but add structure where appropriate
    # We'll only add wrappers, not rewrite semantics.
    if channel == "班群版":
        # short title + body + optional closing line
        title = f"【通知】{scenario}"
        body = t
        return f"{title}\n\n{body}"

    if channel == "公告栏版":
        # more formal: title + sections if possible
        title = f"{scenario}通知"
        return f"{title}\n\n{t}\n"

    if channel == "邮件版":
        subject = f"主题：{scenario}通知"
        greeting = "各位同学："
        closing = "此致\n敬礼"
        return f"{subject}\n\n{greeting}\n{t}\n\n{closing}\n（学生工作部门）"

    if channel == "短信版":
        # compress: take first ~120-160 chars, keep key info
        s = re.sub(r"\s+", " ", t)
        if len(s) > 160:
            s = s[:160].rstrip() + "…"
        return s

    return t


def render_rewrite_block(name: str, rw: dict, scenario: str, key_prefix: str):
    pr = rw.get("pred_risk_score", "-")
    why = rw.get("why", "")
    txt = rw.get("text", "")

    st.markdown(
        f"""
        <div class="card">
          <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
            <div style="font-weight:850; font-size:14px; line-height:1.25;">{html.escape(name)}</div>
            <div class="pill">预测风险 {html.escape(str(pr))}</div>
          </div>
          <div class="muted clamp3" style="margin-top:10px; font-size:13px; line-height:1.45;">
            {html.escape(str(why))}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Publish-ready layouts
    channel = st.segmented_control(
        "发布排版",
        options=["班群版", "邮件版", "公告栏版", "短信版"],
        default="班群版",
        key=f"{key_prefix}_channel_{name}",
    )

    out = format_for_channel(txt, channel, scenario)

    # Display as code (premium, copy-friendly)
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.code(out, language="text")

    # Download
    st.download_button(
        "下载为文本",
        data=out.encode("utf-8"),
        file_name=f"{scenario}-{name}-{channel}.txt",
        mime="text/plain",
        use_container_width=False,
        key=f"{key_prefix}_dl_{name}",
    )


# =========================
# Session state
# =========================
if "result" not in st.session_state:
    st.session_state.result = None
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = {"text": "", "scenario": "宿舍与安全管理通知", "profile": {}}

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

    profile = {"grade": grade, "role": role, "gender": gender, "sensitivity": sensitivity, "custom": custom}

    analyze_btn = st.button("分析并生成改写", type="primary", use_container_width=True)

# --- Brand illustration strip under input, no text (requested) ---
# Put it under the left input area visually, but we need scenario value which is in right col.
# So render it after both columns, aligned to left width using container trick:
st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
cL, cR = st.columns([3, 2], gap="large")
with cL:
    render_brand_strip(scenario)
with cR:
    pass

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
current_scenario = st.session_state.last_inputs.get("scenario", scenario)

# =========================
# Output
# =========================
if not result:
    st.info("请输入文本并点击「分析并生成改写」。")
else:
    render_overview(int(result.get("risk_score", 0)), result.get("risk_level", "LOW"), result.get("summary", ""))

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ---- Rewrite area: publish-ready layouts ----
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
            render_rewrite_block(tname, rw, current_scenario, key_prefix="rw")

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

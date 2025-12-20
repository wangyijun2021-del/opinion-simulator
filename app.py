import os
import re
import json
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
# Premium-ish styles
# =========================
st.markdown(
    """
    <style>
      /* Page spacing */
      .block-container {
        padding-top: 2.2rem;
        padding-bottom: 2.2rem;
        max-width: 1120px;
      }

      /* Hide Streamlit default UI */
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      /* Typography */
      .title {
        font-size: 34px;
        font-weight: 850;
        letter-spacing: -0.02em;
        margin-bottom: 0.35rem;
      }
      .subtitle {
        color: rgba(17,24,39,.62);
        font-size: 14px;
        margin-bottom: 1.6rem;
        line-height: 1.6;
      }
      .section-h {
        font-size: 16px;
        font-weight: 750;
        margin: 0.2rem 0 0.8rem 0;
      }

      /* Cards */
      .card {
        background: rgba(255,255,255,.88);
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

      /* Badges */
      .badge {
        display:inline-flex;
        align-items:center;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 12px;
        border: 1px solid rgba(0,0,0,.08);
        color: rgba(17,24,39,.85);
        background: rgba(255,255,255,.72);
        margin-right: 6px;
        margin-bottom: 6px;
      }

      /* Risk bar */
      .bar {
        height: 10px;
        border-radius: 999px;
        background: rgba(17,24,39,.08);
        overflow: hidden;
        margin-top: 10px;
      }
      .bar > div {
        height: 100%;
        border-radius: 999px;
        background: rgba(59,130,246,.86); /* blue */
      }

      /* Subtle panel */
      .panel {
        border-radius: 18px;
        padding: 14px 16px;
        background: rgba(17,24,39,.03);
        border: 1px solid rgba(0,0,0,.03);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">🎓 高校舆情风险与学生情绪预测系统</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">用于高校通知/公告/制度发布前：识别争议点、预测学生情绪与舆论走势，并生成更稳妥的改写方案（仅作群体趋势研判，不替代人工判断）。</div>',
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
        "- 若在 Streamlit Cloud：Manage app → Secrets 添加 DEEPSEEK_API_KEY\n"
        "- 若本地：终端执行 export DEEPSEEK_API_KEY='你的key'"
    )
    st.stop()

# =========================
# Helpers
# =========================
def safe_extract_json(text: str):
    """
    Robustly extract JSON object from model output.
    Handles code fences, leading/trailing explanations, etc.
    """
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


def local_fallback(text: str):
    """
    If model returns non-JSON or request fails, use simple heuristic fallback
    so the app never crashes.
    """
    risky_words = ["严肃处理", "通报批评", "纪律处分", "一律", "从严", "不得", "立即", "清退", "追责", "强制", "处分", "严禁", "必须"]
    base = 10
    hits = [w for w in risky_words if w in text]
    score = base + min(70, len(hits) * 10)

    level = "LOW" if score < 30 else ("MEDIUM" if score < 60 else "HIGH")

    issues = []
    if hits:
        issues.append(
            {
                "title": "措辞强硬 / 惩戒导向",
                "evidence": "命中词：" + "、".join(hits[:6]),
                "why": "学生容易解读为高压管理或“结果已定”，触发对抗性情绪与二次传播。",
                "rewrite_tip": "补充依据与范围、提供咨询/申诉渠道，用“提醒+规范+支持”替代单纯惩戒式措辞。",
            }
        )

    emotions = [
        {"group": "普通学生", "sentiment": "紧张/被约束", "intensity": 0.55, "sample_comment": "能不能说清楚标准和范围？"},
        {"group": "学生干部/宿舍长", "sentiment": "配合但担心执行成本", "intensity": 0.45, "sample_comment": "希望给个可操作的检查清单。"},
        {"group": "敏感群体", "sentiment": "警惕/抵触", "intensity": 0.65, "sample_comment": "不要搞一刀切和随意处分。"},
    ]

    rewrites = [
        {
            "name": "更稳妥版本（信息完整、语气更稳）",
            "pred_risk_score": max(5, score - 20),
            "text": (
                "【温馨提醒】近期宿舍用电进入高峰期。为降低安全隐患，请同学们在今晚完成一次自查与同寝互查：\n"
                "1）不使用外观破损、线路老化的电器（尤其发热类）；\n"
                "2）插排避免超负荷与多重串接，如出现发烫/接触不良请及时停用并报修；\n"
                "3）离开宿舍前请关闭电源，避免长时间待机。\n\n"
                "如对具体标准或处理流程有疑问，可联系宿管/辅导员咨询；如确需临时用电支持，可说明情况申请协助。感谢大家共同维护宿舍安全。"
            ),
            "why": "弱化惩戒语气，补充可执行清单与咨询渠道，降低误读与对抗情绪。",
        }
    ]

    return {
        "risk_score": int(score),
        "risk_level": level,
        "summary": "模型输出异常，已启用本地兜底规则（用于保证系统稳定，不代表最终结论）。",
        "issues": issues,
        "student_emotions": emotions,
        "rewrites": rewrites,
    }


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
    r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def analyze(text: str, scenario: str, profile: dict):
    system_prompt = (
        "你是高校舆情风控与学生情绪分析专家。"
        "你必须输出【严格 JSON】且只能输出 JSON，不能有任何解释、前后缀、代码块标记。"
        "JSON 必须可被 Python json.loads 直接解析。"
    )

    user_prompt = f"""
请分析下面“高校场景文本”的舆情风险与学生情绪，并生成改写方案（发布前预演）。

【场景】{scenario}

【受众画像】
- 年级/阶段：{profile.get("grade")}
- 身份：{profile.get("role")}
- 性别：{profile.get("gender")}
- 情绪敏感度：{profile.get("sensitivity")}
- 额外画像：{profile.get("custom")}

【原文】
{text}

【输出要求】请输出严格 JSON，结构如下（字段名必须一致）：
{{
  "risk_score": 0-100的整数,
  "risk_level": "LOW"|"MEDIUM"|"HIGH",
  "summary": "一句话总结（不要空泛）",
  "issues": [
    {{
      "title": "风险点标题",
      "evidence": "原文中触发风险的片段（尽量短语级）",
      "why": "为什么会引发学生情绪/传播风险（高校语境）",
      "rewrite_tip": "可操作的改写建议"
    }}
  ],
  "student_emotions": [
    {{
      "group": "学生群体名称（例如：普通学生/考研学生/新生/宿舍长/社团干部等）",
      "sentiment": "主要情绪（例如：焦虑/抵触/理解/支持/讽刺）",
      "intensity": 0到1的小数,
      "sample_comment": "一句典型评论（仿真口吻）"
    }}
  ],
  "rewrites": [
    {{
      "name": "方案名称（建议体现策略标签：Clarify/ Reassure/ Procedural）",
      "pred_risk_score": 0-100整数（预测改写后风险）,
      "text": "改写后的完整文本",
      "why": "为何能降低风险（具体）"
    }}
  ]
}}

【硬性规则】
1) rewrites 至少给 3 个方案；每个方案 text 必须与原文明显不同（不得照抄原句结构/句式），但含义要一致；
2) 每个方案必须补充“执行标准/时间范围/咨询或申诉渠道”中的至少一个要素；
3) intensity 必须在 0~1 之间；
4) issues 的 evidence 尽量给短语级片段，便于高亮标注。
"""

    try:
        content = call_deepseek(system_prompt, user_prompt)
        parsed, err = safe_extract_json(content)
        if parsed is None:
            return local_fallback(text)
        return parsed
    except Exception:
        return local_fallback(text)


def clamp01(x):
    try:
        x = float(x)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, x))


def highlight_text_md(text: str, phrases):
    """
    Streamlit Markdown supports ==highlight==.
    We highlight evidence phrases (short ones) inside the original text.
    """
    if not text or not phrases:
        return text
    out = text
    uniq = []
    for p in phrases:
        p = (p or "").strip()
        if p and p not in uniq:
            uniq.append(p)

    # longer first to avoid partial overlaps
    for p in sorted(uniq, key=len, reverse=True):
        if len(p) > 40:
            continue
        if p in out:
            out = out.replace(p, f"=={p}==")
    return out


def render_overview(risk_score: int, risk_level: str, summary: str):
    pct = max(0, min(100, int(risk_score)))
    k1, k2, k3 = st.columns([1, 1, 2], gap="medium")

    with k1:
        st.markdown(
            f"""
            <div class="card">
              <div class="kpi-label">RISK SCORE</div>
              <div class="kpi-value">{pct}</div>
              <div class="bar"><div style="width:{pct}%;"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="card">
              <div class="kpi-label">RISK LEVEL</div>
              <div class="kpi-value2">{risk_level}</div>
              <div class="muted" style="margin-top:8px;">发布前态势判断</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="card">
              <div class="kpi-label">SUMMARY</div>
              <div style="font-size:16px;font-weight:750;margin-top:10px;line-height:1.5;">
                {summary}
              </div>
              <div class="muted" style="margin-top:10px;">仅作群体趋势研判，不替代人工判断</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_decision(text: str, rewrites: list):
    if not rewrites:
        st.info("未生成改写方案。")
        return

    top = rewrites[:3]
    cols = st.columns(len(top), gap="medium")
    for i, rw in enumerate(top):
        with cols[i]:
            name = rw.get("name", f"方案 {i+1}")
            pr = rw.get("pred_risk_score", "-")
            why = rw.get("why", "")

            st.markdown(
                f"""
                <div class="card">
                  <div style="font-weight:850;font-size:15px;margin-bottom:6px;">{name}</div>
                  <div class="muted" style="margin-bottom:10px;">
                    预测风险：<span style="font-weight:850;color:rgba(17,24,39,.92)">{pr}</span>
                  </div>
                  <div class="muted" style="font-size:13px;line-height:1.45;">{why}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("查看对比"):
                cA, cB = st.columns(2, gap="large")
                with cA:
                    st.markdown("**原始文本**")
                    st.write(text)
                with cB:
                    st.markdown("**改写版本**")
                    st.write(rw.get("text", ""))


# =========================
# Session state for stability
# =========================
if "result" not in st.session_state:
    st.session_state.result = None
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = {"text": "", "scenario": "", "profile": {}}

# =========================
# Module 1: Action Entry
# =========================
st.markdown("### ① 启动发布前预演")

with st.container():
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown('<div class="section-h">✍️ 待发布文本</div>', unsafe_allow_html=True)
        text = st.text_area(
            "请输入要分析的通知/公告/制度文本（越接近真实越好）",
            height=260,
            placeholder="例如：今晚宿舍将进行用电检查……",
        )
        st.caption("提示：越接近真实发布版本，预演效果越好。")

    with right:
        st.markdown('<div class="section-h">🎯 场景与受众</div>', unsafe_allow_html=True)
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
            grade = st.selectbox("年级/阶段", ["新生", "大二/大三", "大四/毕业班", "研究生", "混合群体"], index=4)
            role = st.selectbox("身份", ["普通学生", "宿舍长/楼委", "学生干部", "社团成员", "考研/保研群体", "留学生/交流生", "混合"], index=0)
        with c2:
            gender = st.selectbox("性别", ["不指定", "偏男性", "偏女性", "混合"], index=0)
            sensitivity = st.selectbox("情绪敏感度", ["低", "中", "高"], index=1)

        custom = st.text_input("画像补充（可选）", placeholder="例如：近期对宿舍检查很敏感、担心被通报、容易在社媒吐槽。")

        profile = {
            "grade": grade,
            "role": role,
            "gender": gender,
            "sensitivity": sensitivity,
            "custom": custom,
        }

        st.markdown(
            '<div class="panel muted" style="margin-top:10px;">'
            "本系统不做个体画像，不做自动决策，仅用于发布前风险预演与文字优化。"
            "</div>",
            unsafe_allow_html=True,
        )

        analyze_btn = st.button("启动发布前预演", type="primary", use_container_width=True)

st.divider()

# =========================
# Trigger analysis
# =========================
if analyze_btn:
    if not text.strip():
        st.warning("请先输入一段文本再预演。")
    else:
        with st.spinner("正在预演（DeepSeek）..."):
            result = analyze(text, scenario, profile)

        st.session_state.result = result
        st.session_state.last_inputs = {"text": text, "scenario": scenario, "profile": profile}

# Use stored result for stable UI
result = st.session_state.result
last_inputs = st.session_state.last_inputs
current_text = last_inputs.get("text", "")

# =========================
# Module 2: Situation Awareness
# =========================
st.markdown("### ② 情绪与风险概览（5 秒判断）")
overview_slot = st.container()

with overview_slot:
    if not result:
        st.info("在上方输入文本并点击「启动发布前预演」，这里会展示风险分数、风险等级与一句话结论。")
    else:
        risk_score = int(result.get("risk_score", 0))
        risk_level = result.get("risk_level", "LOW")
        summary = result.get("summary", "")

        render_overview(risk_score, risk_level, summary)

st.divider()

# =========================
# Module 3: Decision Preview
# =========================
st.markdown("### ③ 改写方案对比（多版本世界线）")
decision_slot = st.container()

with decision_slot:
    if not result:
        st.info("完成预演后，这里会并排展示三种改写策略，并支持展开对比原文与改写版本。")
    else:
        render_decision(current_text, result.get("rewrites", []))

# =========================
# Deep-dive (optional): Risks / Emotions / Evidence highlight
# =========================
if result:
    st.divider()
    with st.expander("查看完整研判细节（风险点 / 情绪画像 / 原文高亮）", expanded=False):
        tab1, tab2, tab3 = st.tabs(["⚠️ 风险点与原文标注", "🎭 学生情绪画像", "✍️ 全部改写文本"])

        with tab1:
            issues = result.get("issues", []) or []
            if not issues:
                st.info("未识别到明显风险点（或文本较中性）。")
            else:
                phrases = []
                for it in issues:
                    ev = (it.get("evidence") or "").strip()
                    if ev:
                        # 如果 evidence 是“命中词：”，也照样可以高亮；但太长就不高亮
                        phrases.append(ev.replace("命中词：", "").strip())

                st.markdown("#### 原文风险标注（触发片段高亮）")
                st.markdown(highlight_text_md(current_text, phrases))

                st.markdown("#### 风险点列表")
                for i, it in enumerate(issues, start=1):
                    st.markdown(f"**{i}. {it.get('title','(未命名风险点)')}**")
                    st.markdown(f"- **触发片段**：{it.get('evidence','')}")
                    st.markdown(f"- **为什么危险**：{it.get('why','')}")
                    st.markdown(f"- **改写建议**：{it.get('rewrite_tip','')}")
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
                            <span class='badge'>{e.get('group','群体')}</span>
                            <span class='badge'>情绪：{e.get('sentiment','')}</span>
                            <span class='badge'>强度：{intensity:.2f}</span>
                          </div>
                          <div style='margin-top:10px;' class='mono'>“{e.get('sample_comment','')}”</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.write("")

        with tab3:
            rewrites = result.get("rewrites", []) or []
            if not rewrites:
                st.info("未生成改写方案。")
            else:
                for i, rw in enumerate(rewrites, start=1):
                    st.markdown(f"### {i}. {rw.get('name','方案')}")
                    st.markdown(f"- **预测风险**：`{rw.get('pred_risk_score','-')}`")
                    st.markdown(f"- **为何更稳**：{rw.get('why','')}")
                    st.write(rw.get("text", ""))
                    st.divider()

st.caption("© 发布前预演系统：用于群体趋势研判与文字优化，不做个体画像，不替代人工判断。")

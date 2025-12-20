import os
import json
import re
import time
import requests
import pandas as pd
import streamlit as st

# -----------------------
# UI 基础配置
# -----------------------
st.set_page_config(page_title="高校舆情风险与学生情绪预测系统", layout="wide")

CUSTOM_CSS = """
<style>
:root { --muted:#6b7280; }
.block-title{font-size:28px;font-weight:800;margin:0 0 6px 0;}
.block-sub{color:var(--muted);margin:0 0 18px 0;}
.kpi{padding:14px 14px;border-radius:14px;background:#0b1220;border:1px solid rgba(255,255,255,0.08);}
.kpi h3{margin:0;font-size:12px;color:rgba(255,255,255,0.6);font-weight:600;letter-spacing:0.08em;text-transform:uppercase;}
.kpi .big{font-size:26px;font-weight:800;margin-top:6px;}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;border:1px solid rgba(255,255,255,0.12);color:rgba(255,255,255,0.8);}
.card{padding:16px;border-radius:16px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);}
small{color:var(--muted);}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown('<div class="block-title">🎓 高校舆情风险与学生情绪预测系统</div>', unsafe_allow_html=True)
st.markdown('<div class="block-sub">面向高校通知/公告/处分/活动/住宿后勤等场景：识别风险点、模拟学生群体情绪反馈，并给出更稳妥的改写建议。</div>', unsafe_allow_html=True)

# -----------------------
# DeepSeek 配置
# -----------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

if not DEEPSEEK_API_KEY:
    st.error("未检测到 DEEPSEEK_API_KEY。若在 Streamlit Cloud：请到 Manage app → Secrets 添加 DEEPSEEK_API_KEY。")
    st.stop()

# -----------------------
# 高校场景预设（更好用）
# -----------------------
SCENARIOS = {
    "住宿后勤": "宿舍管理、卫生检查、空调供暖、维修、用电、夜间管理等。重点关注：对学生的尊重、执行透明度、程序正义、‘一刀切’措辞、惩罚导向。",
    "纪律处分": "违纪通报、处分决定、考试纪律、学术诚信等。重点关注：措辞是否羞辱化、标签化；是否给出申诉/流程；是否过度公开个人信息。",
    "奖助评优": "奖学金、助学金、困难认定、评优评奖等。重点关注：公平性、指标解释、争议点、对困难群体的保护。",
    "教学考试": "考试安排、补考缓考、课程调整、教学管理等。重点关注：可执行性、对特殊情况的照顾、信息完整性。",
    "活动宣传": "讲座、团学活动、志愿服务、招生宣传等。重点关注：是否夸大、是否强制、是否引发对立（‘必须’‘不得’）。",
    "安全应急": "突发事件通报、疫情防控、消防演练等。重点关注：恐慌扩散、信息透明、谣言空间、安抚与行动指引。"
}

# -----------------------
# 兜底（本地规则分析）确保永不崩
# -----------------------
def heuristic_analysis(text: str) -> dict:
    hard_words = {
        "严查": "容易被理解为高压治理，触发紧张与不安。",
        "从严": "惩罚导向明显，可能引发对程序正义的质疑。",
        "通报批评": "带有公开羞辱风险，需注意范围与方式。",
        "处分": "强惩罚信号，需补充流程与申诉机制。",
        "清退": "极端处置用语，容易引发恐慌和对抗。",
        "一律": "一刀切信号强，容易引发公平性质疑。",
        "不得": "命令式强，容易引起反感，建议配理由与替代方案。",
        "必须": "强制感强，建议加例外与帮助渠道。",
    }
    groups = ["学生", "辅导员", "家长", "一线后勤", "考研/保研群体", "困难学生"]

    found = [w for w in hard_words if w in text]
    risk = 20 + 15 * len(found)
    if any(w in text for w in ["罚", "记过", "留校察看", "开除", "处分"]):
        risk += 20
    risk = min(100, max(0, risk))

    if risk < 30:
        level = "low"
    elif risk < 70:
        level = "medium"
    else:
        level = "high"

    high_risk_words = [{"word": w, "reason": hard_words[w]} for w in found]

    audiences = [
        {
            "label": "普通在校学生",
            "emotion_score": -0.2 if risk >= 50 else 0.0,
            "emotion_label": "轻度负面/中性",
            "keywords": ["担心", "观望", "希望更明确"],
            "comments": ["能不能说清楚规则和执行标准？", "希望不要一刀切，给特殊情况留空间。"]
        },
        {
            "label": "规则敏感型学生（关注程序正义）",
            "emotion_score": -0.5 if risk >= 50 else -0.2,
            "emotion_label": "中度负面",
            "keywords": ["质疑程序", "担忧公正", "要求解释"],
            "comments": ["处分/检查的依据是什么？有没有申诉渠道？", "请公开流程，不要只给结论。"]
        },
        {
            "label": "家长群体",
            "emotion_score": 0.2 if "安全" in text else 0.0,
            "emotion_label": "略微正面/中性",
            "keywords": ["关注安全", "担心影响学习", "希望沟通"],
            "comments": ["只要安全第一，措施清楚就支持。", "也请考虑孩子学习和生活的实际困难。"]
        }
    ]

    rewrite = []
    softened = text
    soften_map = {"严查": "重点排查", "从严": "依规处理", "一律": "原则上", "不得": "请避免", "必须": "请尽量"}
    for k, v in soften_map.items():
        softened = softened.replace(k, v)

    rewrite.append({
        "rewritten_text": softened + "（并明确执行标准、时间范围与咨询/申诉渠道）",
        "new_risk_score": max(0, risk - 20),
        "brief_reason": "弱化高压措辞，并补全程序与沟通渠道，降低被误读与对抗情绪。"
    })

    return {
        "risk_score": risk,
        "risk_level": level,
        "overall_explanation": "基于本地规则进行兜底分析（模型输出非 JSON 或请求异常时启用）。",
        "high_risk_words": high_risk_words,
        "audiences": audiences,
        "rewrite_suggestions": rewrite
    }

# -----------------------
# JSON 解析增强：从模型返回中“抠出 JSON”
# -----------------------
def safe_json_loads(text: str) -> dict:
    """
    支持：
    - 纯 JSON
    - ```json ... ```
    - JSON 前后带解释文字
    """
    text = text.strip()

    # 1) 直接尝试
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) 尝试从 ```json ...``` 中提取
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return json.loads(m.group(1))

    # 3) 尝试提取第一个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start:end+1])

    raise json.JSONDecodeError("No JSON object could be decoded", text, 0)

# -----------------------
# DeepSeek 调用（高校专用 prompt）
# -----------------------
def analyze_with_deepseek(text: str, scenario: str, audience_profile: str) -> dict:
    scenario_desc = SCENARIOS.get(scenario, "")
    profile_part = f"重点受众画像：{audience_profile}。" if audience_profile else "重点受众画像：默认以在校学生为主。"

    prompt = f"""
你是一名高校宣传/学生工作/舆情风控顾问。请对“高校通知/公告/制度/处分/活动文本”做发布前风险评估，并模拟学生群体情绪。

场景：{scenario}
场景说明：{scenario_desc}
{profile_part}

请严格只输出 JSON（不要输出任何解释文字，不要用 Markdown 代码块）。返回结构如下：

{{
  "risk_score": 0-100,
  "risk_level": "low"|"medium"|"high",
  "overall_explanation": "中文说明",
  "high_risk_words": [{{"word":"", "reason":""}}, ...],
  "audiences": [
    {{
      "label": "群体名称（高校语境）",
      "emotion_score": -1~1,
      "emotion_label": "强烈负面/中度负面/中性/略微正面/强烈正面",
      "keywords": ["3-5个词"],
      "comments": ["模拟评论1", "模拟评论2"]
    }}
  ],
  "rewrite_suggestions": [
    {{
      "rewritten_text": "改写后的完整文本（保持信息完整，语气更稳）",
      "new_risk_score": 0-100,
      "brief_reason": "一句话解释"
    }}
  ]
}}

需要分析的文本：
\"\"\"{text}\"\"\"
""".strip()

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return safe_json_loads(content)
    except Exception:
        return heuristic_analysis(text)

# -----------------------
# UI：左侧输入 / 右侧结果
# -----------------------
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    scenario = st.selectbox("📌 选择高校场景", list(SCENARIOS.keys()))
    st.caption(SCENARIOS[scenario])

    text = st.text_area("📝 输入通知/公告/制度文本", height=190, placeholder="例如：为保障宿舍安全，将对大功率电器开展检查...")
    with st.expander("🎯 高级设置：重点受众画像（可选）", expanded=False):
        role = st.multiselect("身份/角色（可多选）", ["本科生", "研究生", "新生", "毕业年级", "学生干部", "宿舍长", "困难学生", "国际学生", "家长"])
        mood = st.selectbox("情绪敏感度", ["未指定", "高", "中", "低"], index=0)
        custom = st.text_area("自定义画像（优先）", height=80, placeholder="例如：大一新生，刚入学，宿舍生活不熟悉，对管理措施较敏感。")

    profile_parts = []
    if role: profile_parts.append("、".join(role))
    if mood != "未指定": profile_parts.append(f"敏感度{mood}")
    audience_profile = custom.strip() if custom.strip() else ("；".join(profile_parts)).strip()

    run = st.button("🚀 开始分析", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    if run:
        if not text.strip():
            st.warning("请先输入文本。")
        else:
            with st.spinner("正在分析（DeepSeek）..."):
                result = analyze_with_deepseek(text, scenario, audience_profile)

            risk_score = int(result.get("risk_score", 0))
            risk_level = result.get("risk_level", "medium")
            explanation = result.get("overall_explanation", "")
            high_risk_words = result.get("high_risk_words", [])
            audiences = result.get("audiences", [])
            rewrites = result.get("rewrite_suggestions", [])

            # KPI 行
            k1, k2, k3 = st.columns([1,1,2], gap="large")
            with k1:
                st.markdown('<div class="kpi"><h3>Risk Score</h3><div class="big">{}</div></div>'.format(risk_score), unsafe_allow_html=True)
            with k2:
                badge = "low" if risk_level == "low" else ("medium" if risk_level == "medium" else "high")
                st.markdown('<div class="kpi"><h3>Risk Level</h3><div class="big"><span class="badge">{}</span></div></div>'.format(badge.upper()), unsafe_allow_html=True)
            with k3:
                st.markdown('<div class="kpi"><h3>Summary</h3><div style="margin-top:8px;color:rgba(255,255,255,0.85);line-height:1.4;">{}</div></div>'.format(explanation), unsafe_allow_html=True)

            st.progress(min(max(risk_score/100, 0.0), 1.0))
            st.markdown("")

            tab1, tab2, tab3 = st.tabs(["⚠️ 风险点", "🎭 学生情绪", "✍️ 改写建议"])

            with tab1:
                st.subheader("风险词/敏感表达")
                if not high_risk_words:
                    st.success("未识别到明显高风险词（仍建议结合实际语境复核）。")
                else:
                    for it in high_risk_words:
                        st.markdown(f"- **{it.get('word','')}**：{it.get('reason','')}")
                st.markdown("")

            with tab2:
                st.subheader("典型受众群体情绪模拟（高校语境）")
                if not audiences:
                    st.info("暂无受众情绪结果。")
                else:
                    rows = []
                    for a in audiences:
                        rows.append({
                            "受众群体": a.get("label",""),
                            "情绪评分": a.get("emotion_score", 0),
                            "情绪标签": a.get("emotion_label",""),
                            "关键词": " / ".join(a.get("keywords", []))
                        })
                        st.markdown(f"**{a.get('label','')}**")
                        st.write(f"情绪：{a.get('emotion_label','')}（{a.get('emotion_score',0)}）")
                        for c in a.get("comments", [])[:2]:
                            st.write(f"💬 {c}")
                        st.markdown("---")

                    try:
                        df = pd.DataFrame(rows).set_index("受众群体")[["情绪评分"]]
                        st.bar_chart(df)
                    except Exception:
                        pass

            with tab3:
                st.subheader("更稳妥的发布版本（信息完整、语气更稳）")
                if not rewrites:
                    st.info("暂无改写建议。")
                else:
                    options = [f"方案 {i+1}（预测风险 {rw.get('new_risk_score',0)}）" for i, rw in enumerate(rewrites)]
                    pick = st.radio("选择一个方案查看：", options, horizontal=True)
                    idx = options.index(pick)
                    chosen = rewrites[idx]

                    cL, cR = st.columns(2, gap="large")
                    with cL:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown("**原始文本**")
                        st.write(text)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with cR:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown("**推荐改写**")
                        st.write(chosen.get("rewritten_text",""))
                        st.caption(chosen.get("brief_reason",""))
                        st.markdown('</div>', unsafe_allow_html=True)

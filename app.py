import os
import json
import requests
import pandas as pd
import streamlit as st

# ================= 基础配置 =================
st.set_page_config(
    page_title="高校舆论风险与学生情绪预警系统",
    layout="wide"
)

st.title("🎓 高校舆论风险与学生情绪预警系统")
st.caption("面向高校管理与传播场景，模拟学生群体的舆论风险与情绪反应（教学示范版）")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

if not DEEPSEEK_API_KEY:
    st.error("未检测到 DEEPSEEK_API_KEY，请在 Secrets 中配置。")
    st.stop()

# ================= 高校发布场景 =================
SCENARIOS = {
    "exam": "考试与教学安排",
    "discipline": "学生管理与纪律通知",
    "safety": "校园安全与突发事件",
    "logistics": "宿舍 / 后勤 / 资源分配",
    "policy": "涉及学生权益的制度调整"
}

# ================= DeepSeek 分析函数 =================
def analyze(text, scenario, student_profile):
    prompt = f"""
你是一名高校舆情与学生事务领域的传播研究专家。

当前场景：{SCENARIOS[scenario]}
重点受众：高校学生群体
特别关注的学生画像：{student_profile if student_profile else "未指定，默认一般学生"}

请分析下面文本在高校学生中的传播风险，并返回 JSON，包含：

1. risk_score（0-100）
2. risk_level（low / medium / high）
3. overall_explanation
4. student_emotions（列表）：
   - emotion
   - intensity（0-1）
   - explanation
5. sensitive_points（学生可能反感或误解的点）
6. rewrite_suggestions（2 条）：
   - rewritten_text
   - new_risk_score
   - reason

只输出 JSON。

文本：
\"\"\"{text}\"\"\"
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    r = requests.post(API_URL, headers=headers, json=payload)
    r.raise_for_status()

    content = r.json()["choices"][0]["message"]["content"]
    return json.loads(content)

# ================= UI =================
left, right = st.columns([1, 2])

with left:
    scenario = st.selectbox(
        "📌 发布场景",
        list(SCENARIOS.keys()),
        format_func=lambda k: SCENARIOS[k]
    )

    text = st.text_area(
        "📄 待发布文本",
        height=180,
        placeholder="例如：学校将对晚归学生进行集中检查，并视情况给予通报处理。"
    )

    with st.expander("🎯 重点学生群体（可选）"):
        profile = st.text_area(
            "描述你特别关注的学生群体（可留空）",
            placeholder="例如：大三本科生，就业压力较大，对管理公平性高度敏感。"
        )

    submit = st.button("开始分析", type="primary")

with right:
    if submit and text.strip():
        with st.spinner("分析中…"):
            result = analyze(text, scenario, profile)

        st.subheader("📊 整体风险评估")
        st.metric("风险指数", result["risk_score"])
        st.write(result["overall_explanation"])

        st.subheader("😶 学生情绪预测")
        for emo in result["student_emotions"]:
            st.write(
                f"- **{emo['emotion']}**（强度 {emo['intensity']}）：{emo['explanation']}"
            )

        st.subheader("⚠️ 潜在敏感点")
        for p in result["sensitive_points"]:
            st.write(f"- {p}")

        st.subheader("✏️ 风险降低建议")
        for r in result["rewrite_suggestions"]:
            st.markdown(f"**改写文本：** {r['rewritten_text']}")
            st.caption(f"预测风险：{r['new_risk_score']} ｜ {r['reason']}")
            st.markdown("---")

import os
import json
import requests
import pandas as pd
import streamlit as st

# ========== 页面基础配置 & 简单样式 ==========
st.set_page_config(
    page_title="AI 舆论风险与受众情绪模拟器",
    layout="wide"
)

CUSTOM_CSS = """
<style>
.main-title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 0.2rem;
}
.sub-title {
    font-size: 14px;
    color: #666666;
    margin-bottom: 1.2rem;
}
.section-label {
    font-size: 12px;
    font-weight: 600;
    color: #888888;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown('<div class="main-title">AI 舆论风险与受众情绪模拟器（DeepSeek 驱动）</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">用于在发布前预估文本的舆论风险，并模拟不同受众群体的情绪反馈，辅助编辑做出更稳妥的用词决策。</div>', unsafe_allow_html=True)

# ========== 场景预设 ==========
SCENARIOS = {
    "general": {
        "label": "通用文本",
        "hint": "适用于一般新闻稿、评论、通知等文本。",
        "prompt": "请以一般公众为主要受众，综合考量措辞是否容易被误读、放大、断章取义。"
    },
    "policy": {
        "label": "政策 / 行政通告",
        "hint": "公告、整治通知、管理措施说明等。",
        "prompt": "这是政策 / 行政类通告，请重点关注是否存在一刀切、运动式执法、对一线群体不够体谅等风险。"
    },
    "pr": {
        "label": "品牌公关声明",
        "hint": "企业道歉声明、回应争议公告等。",
        "prompt": "这是品牌公关 / 危机回应文本，请重点关注态度是否真诚、是否推责、是否激化对立。"
    },
    "campus": {
        "label": "校园 / 校内通知",
        "hint": "高校/学校发给学生、家长、教职工的通知。",
        "prompt": "这是校园 / 校内通知，请重点关注对学生、家长等群体的尊重程度，以及是否容易引发“程序不透明”“不够人性化”等质疑。"
    },
    "public_issue": {
        "label": "公益宣传 / 社会议题",
        "hint": "涉及性别、劳动、弱势群体等议题的传播。",
        "prompt": "这是与社会议题 / 公益相关的内容，请重点关注是否再生产刻板印象、忽视弱势群体处境、或将责任单方面推给个体。"
    },
    "intl": {
        "label": "国际传播 / 对外表述",
        "hint": "面向国际受众的介绍、回应、形象传播等。",
        "prompt": "这是对外传播 / 国际舆论场景，请重点关注是否容易被误解为傲慢、防御性过强、或加深既有刻板印象。"
    }
}

# ========== 读取 DeepSeek API Key ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

if not DEEPSEEK_API_KEY:
    st.error("没有检测到 DEEPSEEK_API_KEY，请先在终端里执行：export DEEPSEEK_API_KEY='你的_key'")
    st.stop()


# ========== 本地规则分析（作为兜底） ==========
def heuristic_analysis(text: str) -> dict:
    """
    本地规则版分析：不调用任何外部 API，用简单规则模拟“舆论风险 + 受众情绪 + 重写建议”。
    """

    high_words_map = {
        "严厉": "用词偏重，给人强烈处罚和压制感，可能引发被针对感和恐惧情绪。",
        "整治": "带有惩罚性与运动式治理色彩，容易被解读为一刀切。",
        "打击": "语气强硬，容易让相关群体产生被敌视、被暴力对待的联想。",
        "取缔": "意味着彻底否定或禁止，容易引发强烈反弹或恐慌。",
        "管控": "强调控制与压制，容易引发对自由受限的担忧。",
        "严查": "带有高压执法意味，容易引起紧张和不安。",
    }

    vulnerable_groups = ["外卖骑手", "农民工", "一线员工", "普通群众", "个体工商户"]

    found_high = [w for w in high_words_map.keys() if w in text]
    found_vulnerable = [w for w in vulnerable_groups if w in text]

    # 简单打分规则
    risk_score = 20
    risk_score += 20 * len(found_high)
    risk_score += 10 * len(found_vulnerable)
    if any(w in text for w in ["处罚", "罚款", "清退", "封禁"]):
        risk_score += 15

    risk_score = max(0, min(100, risk_score))

    if risk_score < 30:
        risk_level = "low"
        overall_explanation = "整体表述相对温和，舆论风险较低。但仍需注意具体情境与传播环境。"
    elif risk_score < 70:
        risk_level = "medium"
        overall_explanation = "文本中包含一定力度较强的措辞，可能引发部分群体的争议或不安，需要结合场景谨慎使用。"
    else:
        risk_level = "high"
        overall_explanation = "文本中存在多处高压、惩罚性或运动式用语，且涉及潜在弱势群体，较容易引发舆论反弹或情绪放大。"

    high_risk_words = []
    for w in found_high:
        high_risk_words.append({
            "word": w,
            "reason": high_words_map[w]
        })

    audiences = []

    if found_vulnerable:
        label = "相关群体：" + "、".join(found_vulnerable)
        audiences.append({
            "label": label,
            "emotion_score": -0.7 if risk_score >= 70 else -0.4,
            "emotion_label": "中度到强烈负面",
            "keywords": ["被针对", "不安", "压力", "担忧"],
            "comments": [
                "感觉决策没有充分考虑到我们的处境和压力。",
                "为什么总是用这么强硬的语言来说我们？"
            ]
        })

    audiences.append({
        "label": "秩序优先者（重视管理和安全的公众）",
        "emotion_score": 0.3 if risk_score >= 40 else 0.1,
        "emotion_label": "略微正面到中性",
        "keywords": ["支持管理", "期待秩序", "但也担忧过度"],
        "comments": [
            "适度规范是有必要的，但希望不要演变成简单粗暴的一刀切。",
            "只要政策执行得当、透明公正，我是支持加强管理的。"
        ]
    })

    audiences.append({
        "label": "青年网民",
        "emotion_score": -0.2 if risk_score >= 50 else 0.0,
        "emotion_label": "轻度负面到中性",
        "keywords": ["质疑", "围观", "担心过度执法"],
        "comments": [
            "这种措辞听起来有点上头，希望不是一阵风式运动。",
            "具体怎么执行很关键，不要最后苦的还是一线普通人。"
        ]
    })

    rewrite_suggestions = []
    soften_map = {
        "严厉": "进一步",
        "打击": "规范和纠正",
        "整治": "优化和改进",
        "取缔": "有序调整和引导",
        "管控": "加强服务与管理",
        "严查": "重点排查与规范",
    }

    if found_high:
        rewritten_text = text
        for w in found_high:
            if w in soften_map:
                rewritten_text = rewritten_text.replace(w, soften_map[w])

        new_risk_score = max(0, risk_score - 25)
        rewrite_suggestions.append({
            "rewritten_text": rewritten_text,
            "new_risk_score": new_risk_score,
            "brief_reason": "通过将高压、惩罚性的措辞替换为过程性、服务性表达，可以降低被针对感和恐惧感。"
        })

    rewritten_text2 = text + " 同时，将通过听取各方意见、提供必要支持，确保相关群体的正当权益得到保障。"
    rewrite_suggestions.append({
        "rewritten_text": rewritten_text2,
        "new_risk_score": max(0, risk_score - 15),
        "brief_reason": "在原有表述基础上增加程序透明、保障性和沟通性的说明，有助于缓和情绪、减少误解。"
    })

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "overall_explanation": overall_explanation,
        "high_risk_words": high_risk_words,
        "audiences": audiences,
        "rewrite_suggestions": rewrite_suggestions,
    }


# ========== 受众画像拼接 ==========
def build_audience_profile(age, gender, stance, identities, sensitivity, custom_desc) -> str:
    """
    根据用户在侧边栏的选择，拼出一段给大模型看的受众画像描述。
    如果填写了自定义画像，则以自定义为主。
    """
    custom_desc = custom_desc.strip()
    if custom_desc:
        return custom_desc

    parts = []

    if age != "未指定":
        parts.append(age)

    if gender != "未指定":
        parts.append(gender)

    if stance != "未指定":
        parts.append(stance + "立场")

    if identities:
        parts.append("、".join(identities))

    if sensitivity != "未指定":
        parts.append(f"情绪敏感度{sensitivity}")

    if not parts:
        return ""

    return "、".join(parts)


# ========== DeepSeek 调用函数（带场景 & 兜底） ==========
def analyze_with_deepseek(text: str, scenario_key: str, audience_profile: str = "") -> dict:
    scenario = SCENARIOS.get(scenario_key, SCENARIOS["general"])
    scenario_label = scenario["label"]
    scenario_prompt = scenario["prompt"]

    scenario_part = f"当前编辑场景：{scenario_label}。{scenario_prompt}\n"

    profile_part = ""
    if audience_profile:
        profile_part = f"\n编辑特别关心的重点受众画像是：{audience_profile}。请在分析受众情绪时优先考虑这一群体的反应。\n"

    prompt = f"""
你是一名熟悉中国与国际舆论场的传播学与新闻学专家，现在需要帮助编辑在发文前预判舆论风险。

{scenario_part}
{profile_part}

请你阅读下面这段文本，对它进行系统分析，并用 JSON 返回结果。

需要包含的字段：

1. risk_score: 0-100 的数字，表示整体舆论风险等级（越高越危险）
2. risk_level: "low" / "medium" / "high" 三档
3. overall_explanation: 一段中文文字，解释为什么是这个风险等级
4. high_risk_words: 一个列表，包含若干对象：
   - word: 词语本身
   - reason: 为什么这个词有风险（比如：惩罚性、针对弱势群体、情绪化等）
5. audiences: 一个列表，包含 3-5 个典型受众群体，每个对象包含：
   - label: 群体名称（例如：外卖骑手、青年网民、秩序优先者、家长群体等）
   - emotion_score: -1 到 1 的数字（负面到正面）
   - emotion_label: 例如 "强烈负面" "中度负面" "中性" "略微正面" "强烈正面"
   - keywords: 用 3-5 个词概括他们的情绪（例如：愤怒 / 被针对 / 支持 / 担忧）
   - comments: 用 2 条简短中文句子，模拟他们可能在评论区留下的话
6. rewrite_suggestions: 一个列表，给出 2-3 个替代表达（可以是改写后的整句文本），每个对象包含：
   - rewritten_text: 改写后的句子
   - new_risk_score: 0-100 的风险评分（改写后的）
   - brief_reason: 一句话说明为什么这样改风险降低了

只输出 JSON，不要输出任何解释性文字。

需要分析的文本如下：

\"\"\"{text}\"\"\"
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)

        if resp.status_code == 402:
            return heuristic_analysis(text)

        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                result = json.loads(content[start:end+1])
            else:
                return heuristic_analysis(text)

        return result

    except Exception:
        return heuristic_analysis(text)


# ========== 页面布局：左侧控制面板 + 右侧结果 ==========
left, right = st.columns([1, 2])

with left:
    st.markdown('<div class="section-label">SCENARIO</div>', unsafe_allow_html=True)
    scenario_key = st.selectbox(
        "选择使用场景",
        list(SCENARIOS.keys()),
        format_func=lambda k: SCENARIOS[k]["label"],
    )
    st.caption(SCENARIOS[scenario_key]["hint"])

    st.markdown("---")
    st.markdown('<div class="section-label">TEXT</div>', unsafe_allow_html=True)
    user_text = st.text_area(
        "请输入要分析的标题或短文：",
        height=180,
        placeholder="例如：严厉整治外卖骑手违规现象。"
    )

    with st.expander("🎯 高级设置：指定重点受众画像（可选）", expanded=False):
        age = st.selectbox("年龄", ["未指定", "青年", "中年", "老年"])
        gender = st.selectbox("性别", ["未指定", "男性", "女性", "非二元 / 其他"])
        stance = st.selectbox("价值立场", ["未指定", "自由主义", "保守主义", "中立"])

        identities = st.multiselect(
            "身份 / 角色（可多选）",
            ["学生", "打工人", "管理层", "公务员", "媒体从业者", "家长", "退休人群", "乡村居民", "城市新移民"],
            default=[]
        )

        sensitivity = st.selectbox("情绪敏感度", ["未指定", "高", "中", "低"])

        custom_desc = st.text_area(
            "自定义受众画像（可选）",
            height=80,
            placeholder="例如：25岁女性，在一线城市做新媒体运营，对劳动权益议题高度敏感。"
        )

    audience_profile_text = build_audience_profile(
        age=age,
        gender=gender,
        stance=stance,
        identities=identities,
        sensitivity=sensitivity,
        custom_desc=custom_desc,
    )

    if audience_profile_text:
        st.caption(f"当前重点关注受众：{audience_profile_text}")
    else:
        st.caption("如不选择，将默认面向一般公众进行分析。")

    st.markdown("---")
    analyze_button = st.button("🚀 开始分析", type="primary")


with right:
    if analyze_button:
        if not user_text.strip():
            st.warning("请先输入文本。")
        else:
            with st.spinner("正在调用 DeepSeek 分析中，请稍候..."):
                result = analyze_with_deepseek(user_text, scenario_key, audience_profile_text)

            risk_score = result.get("risk_score", 0)
            risk_level = result.get("risk_level", "unknown")
            explanation = result.get("overall_explanation", "")
            high_risk_words = result.get("high_risk_words", [])
            audiences = result.get("audiences", [])
            rewrites = result.get("rewrite_suggestions", [])

            # ========= 总览区 =========
            st.subheader("📌 整体舆论风险总览")

            c1, c2 = st.columns([1, 3])
            with c1:
                st.metric("风险指数（0-100）", risk_score)

            with c2:
                if risk_level == "low":
                    st.success("风险等级：偏低（low）")
                elif risk_level == "medium":
                    st.warning("风险等级：中等（medium）")
                elif risk_level == "high":
                    st.error("风险等级：较高（high）")
                else:
                    st.info("风险等级：未知")

                st.progress(min(max(risk_score / 100, 0.0), 1.0))

            # 告知当前场景
            st.caption(f"当前场景：{SCENARIOS[scenario_key]['label']}")

            if explanation:
                st.write(explanation)

            st.markdown("---")

            # ========= 标签页：详细信息 =========
            tab_words, tab_aud, tab_rewrite = st.tabs(
                ["高风险措辞", "受众情绪可视化", "重写前后对比"]
            )

            # --- 高风险措辞 ---
            with tab_words:
                st.subheader("⚠️ 高风险词与敏感表达")
                if not high_risk_words:
                    st.write("未检测到明显高风险词。")
                else:
                    for item in high_risk_words:
                        word = item.get("word", "")
                        reason = item.get("reason", "")
                        st.markdown(f"- **{word}**：{reason}")

            # --- 受众情绪可视化 ---
            with tab_aud:
                st.subheader("🎭 典型受众群体情绪模拟")

                if not audiences:
                    st.write("暂未生成受众情绪模拟结果。")
                else:
                    for aud in audiences:
                        st.markdown(f"**{aud.get('label', '某类受众')}**")
                        col_a1, col_a2 = st.columns([1, 3])
                        with col_a1:
                            st.write(f"情绪评分：{aud.get('emotion_score', 0)}")
                            st.write(f"情绪类型：{aud.get('emotion_label', '')}")
                        with col_a2:
                            kws = aud.get("keywords", [])
                            if kws:
                                st.write("关键词：" + " / ".join(kws))
                        comments = aud.get("comments", [])
                        for c in comments:
                            st.write(f"💬 {c}")
                        st.markdown("---")

                    # 柱状图
                    try:
                        df = pd.DataFrame([
                            {
                                "受众群体": aud.get("label", ""),
                                "情绪评分": aud.get("emotion_score", 0)
                            }
                            for aud in audiences
                        ])
                        df = df.set_index("受众群体")
                        st.bar_chart(df)
                    except Exception:
                        pass

            # --- 重写建议 ---
            with tab_rewrite:
                st.subheader("✏️ 降低风险的重写建议")

                if not rewrites:
                    st.write("暂无重写建议。")
                else:
                    options = []
                    for idx, r in enumerate(rewrites, start=1):
                        score = r.get("new_risk_score", 0)
                        options.append(f"方案 {idx}（预测风险 {score}）")

                    choice = st.radio("请选择一个方案查看详情：", options)

                    idx = options.index(choice)
                    chosen = rewrites[idx]

                    col_o, col_n = st.columns(2)
                    with col_o:
                        st.markdown("**原始文本**")
                        st.write(user_text)
                        st.metric("原始风险", risk_score)

                    with col_n:
                        st.markdown("**重写方案**")
                        st.write(chosen.get("rewritten_text", ""))
                        new_score = chosen.get("new_risk_score", 0)
                        delta = new_score - risk_score
                        st.metric("重写后风险", new_score, delta=delta)
                        st.caption(chosen.get("brief_reason", ""))

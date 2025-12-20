import os
import re
import json
import time
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
# Basic styles (simple but nicer)
# =========================
st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 2rem;}
      .title {font-size: 34px; font-weight: 800; margin-bottom: 0.2rem;}
      .subtitle {color: #6b7280; font-size: 14px; margin-bottom: 1.2rem;}
      .card {border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; padding: 14px 16px; background: #fff;}
      .badge {display:inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; border:1px solid rgba(0,0,0,0.12); color:#111827;}
      .muted {color:#6b7280;}
      .mono {font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">🎓 高校舆情风险与学生情绪预测系统</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">用于高校通知/公告/制度发布前：识别争议点、预测学生情绪与舆论走势，并生成更稳妥的改写方案。</div>', unsafe_allow_html=True)

# =========================
# DeepSeek config
# =========================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

if not DEEPSEEK_API_KEY:
    st.error("未检测到 DEEPSEEK_API_KEY。若在 Streamlit Cloud：Manage app → Secrets 添加 DEEPSEEK_API_KEY。若本地：终端执行 export DEEPSEEK_API_KEY='你的key'")
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

    # Remove code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()

    # Try direct parse
    try:
        return json.loads(cleaned), None
    except Exception:
        pass

    # Try to find the first {...} block
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start:end+1]
        # common quote issues
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
    # very rough heuristic
    risky_words = ["严肃处理", "通报批评", "纪律处分", "一律", "从严", "不得", "立即", "清退", "追责", "强制", "处分"]
    score = 10
    hits = [w for w in risky_words if w in text]
    score += min(70, len(hits) * 10)

    level = "LOW" if score < 30 else ("MEDIUM" if score < 60 else "HIGH")
    issues = []
    if hits:
        issues.append({
            "title": "措辞强硬/惩戒导向",
            "evidence": "命中词：" + "、".join(hits),
            "why": "学生易解读为高压管理，触发对抗性情绪或二次传播。",
            "rewrite_tip": "尽量增加依据、范围、申诉渠道，用“提醒+规范+支持”替代单纯惩戒。"
        })

    emotions = [
        {"group": "普通学生", "sentiment": "紧张/被约束", "intensity": 0.55, "sample_comment": "能不能说清楚标准和范围？"},
        {"group": "宿舍长/楼委", "sentiment": "配合但担心执行成本", "intensity": 0.45, "sample_comment": "希望给个可操作的检查清单。"},
        {"group": "维权敏感群体", "sentiment": "警惕/抵触", "intensity": 0.65, "sample_comment": "不要搞一刀切和随意处分。"},
    ]

    rewrites = [
        {
            "name": "更稳妥版本（信息完整、语气更稳）",
            "pred_risk_score": max(5, score - 20),
            "text": (
                "【温馨提醒】近期宿舍用电进入高峰期。为降低安全隐患，请同学们今晚完成一次自查与同寝互查："
                "（1）不使用外观破损、线路老化的电器（尤其发热类）；"
                "（2）插排避免超负荷与多重串接，如出现发烫/接触不良请及时停用并报修；"
                "（3）离开宿舍前请关闭电源，避免长时间待机。"
                "如需帮助可联系宿管/辅导员，学校将提供报修与咨询支持。感谢大家共同维护宿舍安全。"
            ),
            "why": "弱化惩戒语气，补充可执行清单与求助渠道，降低误读与对抗情绪。"
        }
    ]

    return {
        "risk_score": score,
        "risk_level": level,
        "summary": "基于本地规则进行兜底分析（模型输出非 JSON 或请求异常时启用）。",
        "issues": issues,
        "student_emotions": emotions,
        "rewrites": rewrites
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

    # 强制“改写必须不同”，避免模型照抄
    user_prompt = f"""
请分析下面“高校场景文本”的舆情风险与学生情绪，并生成改写方案。

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
      "evidence": "原文中触发风险的片段（可引用短语）",
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
      "name": "方案名称",
      "pred_risk_score": 0-100整数（预测改写后风险）,
      "text": "改写后的完整文本",
      "why": "为何能降低风险（具体）"
    }}
  ]
}}

【硬性规则】
1) rewrites 里至少给 3 个方案；每个方案的 text 必须与原文明显不同（不得照抄原句结构/句式），但含义要一致；
2) 必须补充“执行标准/时间范围/咨询或申诉渠道”中的至少一个要素；
3) intensity 必须在 0~1 之间。
"""

    try:
        content = call_deepseek(system_prompt, user_prompt)
        parsed, err = safe_extract_json(content)
        if parsed is None:
            # fallback
            return local_fallback(text)
        return parsed
    except Exception:
        return local_fallback(text)

# =========================
# UI inputs
# =========================
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown("#### ✍️ 文本输入")
    text = st.text_area(
        "请输入要分析的通知/公告/制度文本（越接近真实越好）",
        height=240,
        placeholder="例如：今晚宿舍将进行用电检查……"
    )

    st.markdown("#### 🧭 场景预设")
    scenario = st.selectbox(
        "选择发布场景",
        [
            "宿舍与安全管理通知",
            "课程/考试/成绩相关通知",
            "奖助学金/资助政策通知",
            "纪律处分/违纪处理通告",
            "校内活动/讲座报名通知",
            "疫情/卫生/公共安全通知",
            "其他（通用高校公告）",
        ],
        index=0
    )

    st.markdown("#### 👤 受众画像（高校版）")
    c1, c2 = st.columns(2)
    with c1:
        grade = st.selectbox("年级/阶段", ["新生", "大二/大三", "大四/毕业班", "研究生", "混合群体"], index=4)
        role = st.selectbox("身份", ["普通学生", "宿舍长/楼委", "学生干部", "社团成员", "考研/保研群体", "留学生/交流生", "混合"], index=0)
    with c2:
        gender = st.selectbox("性别", ["不指定", "偏男性", "偏女性", "混合"], index=0)
        sensitivity = st.selectbox("情绪敏感度", ["低", "中", "高"], index=1)

    custom = st.text_input("自定义画像补充（可选）", placeholder="例如：近期对宿舍检查很敏感、担心被通报、容易在社媒吐槽。")

    profile = {
        "grade": grade,
        "role": role,
        "gender": gender,
        "sensitivity": sensitivity,
        "custom": custom
    }

    analyze_btn = st.button("开始分析", type="primary", use_container_width=True)

with right:
    st.markdown("#### 📊 分析结果")
    if analyze_btn:
        if not text.strip():
            st.warning("先输入一段文本再分析。")
        else:
            with st.spinner("正在分析（DeepSeek）..."):
                result = analyze(text, scenario, profile)

            risk_score = int(result.get("risk_score", 0))
            risk_level = result.get("risk_level", "LOW")
            summary = result.get("summary", "")

            k1, k2, k3 = st.columns([1, 1, 2], gap="medium")
            with k1:
                st.markdown('<div class="card"><div class="muted">RISK SCORE</div>'
                            f'<div style="font-size:40px;font-weight:800;margin-top:6px;">{risk_score}</div></div>',
                            unsafe_allow_html=True)
            with k2:
                st.markdown('<div class="card"><div class="muted">RISK LEVEL</div>'
                            f'<div style="font-size:28px;font-weight:800;margin-top:12px;">{risk_level}</div></div>',
                            unsafe_allow_html=True)
            with k3:
                st.markdown('<div class="card"><div class="muted">SUMMARY</div>'
                            f'<div style="font-size:18px;font-weight:700;margin-top:12px;">{summary}</div></div>',
                            unsafe_allow_html=True)

            st.progress(min(1.0, max(0.0, risk_score / 100.0)))

            tab1, tab2, tab3 = st.tabs(["⚠️ 风险点", "🎭 学生情绪", "✍️ 改写建议"])

            with tab1:
                issues = result.get("issues", [])
                if not issues:
                    st.info("未识别到明显风险点（或文本较中性）。")
                else:
                    for i, it in enumerate(issues, start=1):
                        st.markdown(f"**{i}. {it.get('title','(未命名风险点)')}**")
                        st.markdown(f"- **触发片段**：{it.get('evidence','')}")
                        st.markdown(f"- **为什么危险**：{it.get('why','')}")
                        st.markdown(f"- **改写建议**：{it.get('rewrite_tip','')}")
                        st.divider()

            with tab2:
                emos = result.get("student_emotions", [])
                if not emos:
                    st.info("未生成情绪画像。")
                else:
                    for e in emos:
                        st.markdown(
                            f"<div class='card'>"
                            f"<div><span class='badge'>{e.get('group','群体')}</span> "
                            f"<span class='badge'>情绪：{e.get('sentiment','')}</span> "
                            f"<span class='badge'>强度：{e.get('intensity',0)}</span></div>"
                            f"<div style='margin-top:10px;' class='mono'>“{e.get('sample_comment','')}”</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        st.write("")

            with tab3:
                rewrites = result.get("rewrites", [])
                if not rewrites:
                    st.info("未生成改写方案。")
                else:
                    options = [f"{i+1}. {rw.get('name','方案')}" for i, rw in enumerate(rewrites)]
                    idx = st.radio("选择一个方案查看：", list(range(len(options))), format_func=lambda i: options[i])
                    rw = rewrites[idx]

                    st.markdown("### 更稳妥的发布版本")
                    st.markdown(f"- **预测风险**：`{rw.get('pred_risk_score', '-')}`")
                    st.markdown(f"- **为什么更稳**：{rw.get('why','')}")
                    cA, cB = st.columns(2, gap="large")
                    with cA:
                        st.markdown("#### 原始文本")
                        st.write(text)
                    with cB:
                        st.markdown("#### 推荐改写")
                        st.write(rw.get("text", ""))

                    st.caption("提示：如果你发现方案仍然“几乎没改”，一般是模型输出不稳定；本版本已尽量用 prompt 和解析做了约束。")

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
# Styles
# =========================
st.markdown(
    """
    <style>
      [data-testid="stAppViewContainer"]{
        background:
          radial-gradient(1200px 700px at 20% 0%, rgba(59,130,246,.16), transparent 60%),
          radial-gradient(900px 520px at 85% 10%, rgba(37,99,235,.12), transparent 55%),
          linear-gradient(180deg, rgba(239,246,255,1) 0%, rgba(248,250,252,1) 55%, rgba(255,255,255,1) 100%);
      }
      header, footer, #MainMenu {visibility:hidden;}
      .block-container{max-width:1120px;padding-top:1.1rem;}

      .section-h{
        font-size:19px;font-weight:900;
        border-left:4px solid rgba(37,99,235,.55);
        padding-left:12px;margin-bottom:1rem;
      }

      .card{
        background:rgba(255,255,255,.88);
        border-radius:18px;
        padding:16px 18px;
        box-shadow:0 12px 34px rgba(2,6,23,.07);
        border:1px solid rgba(2,6,23,.05);
      }

      .blue-tag{
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        background:rgba(37,99,235,.12);
        color:rgba(37,99,235,1);
        font-size:12px;
        font-weight:700;
        border:1px solid rgba(37,99,235,.18);
        margin-right:8px;margin-bottom:6px;
      }

      .bubble{
        margin-top:10px;
        background:rgba(255,255,255,.94);
        border:1px solid rgba(2,6,23,.07);
        border-radius:18px;
        padding:12px 14px;
        line-height:1.75;
        box-shadow:0 12px 28px rgba(2,6,23,.06);
        position:relative;
      }
      .bubble:before{
        content:"";
        position:absolute;
        left:18px;top:-8px;
        width:14px;height:14px;
        background:rgba(255,255,255,.94);
        border-left:1px solid rgba(2,6,23,.07);
        border-top:1px solid rgba(2,6,23,.07);
        transform:rotate(45deg);
      }

      /* Primary */
      div.stButton > button[kind="primary"]{
        border-radius:16px!important;
        padding:14px 16px!important;
        font-weight:900!important;
        background:linear-gradient(90deg, rgba(37,99,235,.96), rgba(59,130,246,.92))!important;
        box-shadow:0 18px 44px rgba(37,99,235,.22)!important;
      }

      /* Secondary — identical to copy button */
      div.stButton > button[kind="secondary"]{
        width:100%!important;
        border:1px solid rgba(37,99,235,.25)!important;
        background:rgba(37,99,235,.08)!important;
        color:rgba(37,99,235,1)!important;
        padding:10px 12px!important;
        border-radius:14px!important;
        font-weight:900!important;
        font-size:15px!important;
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
    <div style="text-align:center;margin-bottom:1rem;">
      <div style="font-size:42px;font-weight:900;">清小知</div>
      <div style="opacity:.7;">高校通知小助手｜让通知更容易被理解</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# Utils
# =========================
def pretty_notice(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    s = re.sub(r"\\(?=\d+[\.\、\)])", "", s)
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"(?m)^\s*-\s+", "· ", s)
    s = re.sub(r"(?m)^(?=\d+[\.\、\)])", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def add_emojis_smart(text: str) -> str:
    if not text:
        return ""
    out = []
    for i, line in enumerate(text.split("\n")):
        L = line.strip()
        if not L:
            out.append("")
            continue
        if re.match(r"^[\U0001F300-\U0001FAFF]", L):
            out.append(L); continue
        if i <= 1 and re.search(r"(同学|大家|各位)", L):
            L = "👋 " + L
        elif re.search(r"(时间|今晚|明天|\d{1,2}[:：]\d{2})", L):
            L = "⏰ " + L
        elif re.search(r"(地点|教室|宿舍)", L):
            L = "📍 " + L
        elif re.search(r"(咨询|联系|电话|邮箱)", L):
            L = "☎️ " + L
        elif re.search(r"(注意|提醒|禁止|务必)", L):
            L = "⚠️ " + L
        out.append(L)
    return "\n".join(out).strip()

def clipboard_copy_button(text: str, key: str):
    safe = json.dumps(text, ensure_ascii=False)
    components.html(
        f"""
        <button id="btn-{key}" style="
          width:100%;
          border:1px solid rgba(37,99,235,.25);
          background:rgba(37,99,235,.08);
          color:rgba(37,99,235,1);
          padding:10px 12px;
          border-radius:14px;
          font-weight:900;
          font-size:15px;
        ">复制该版本</button>
        <script>
        document.getElementById("btn-{key}").onclick = async () => {{
          await navigator.clipboard.writeText({safe});
        }};
        </script>
        """,
        height=46,
    )

# =========================
# Session state
# =========================
for k in ["更清晰", "更安抚", "更可执行"]:
    st.session_state.setdefault(f"emoji_on_{k}", False)

# =========================
# Mock rewrite data（示例）
# =========================
rewrites = [
    {
        "name": "更清晰",
        "pred_risk_score": 40,
        "why": "结构更清楚，减少误读。",
        "text": "各位同学：\n\n下学期课程安排已更新，请注意时间与选课要求。\n\n如有疑问，请联系教学办。",
    },
    {
        "name": "更安抚",
        "pred_risk_score": 32,
        "why": "降低焦虑，提供支持。",
        "text": "各位同学：\n\n请大家放心，课程调整将充分考虑学习节奏。\n\n有问题可随时咨询。",
    },
    {
        "name": "更可执行",
        "pred_risk_score": 28,
        "why": "步骤明确，行动成本低。",
        "text": "各位同学：\n\n1. 查看教务系统\n2. 如需调整，提交申请\n\n咨询方式见下方。",
    },
]

# =========================
# Rewrite UI
# =========================
st.markdown('<div class="section-h">改写建议</div>', unsafe_allow_html=True)
tabs = st.tabs(["更清晰", "更安抚", "更可执行"])

for rw, tab in zip(rewrites, tabs):
    name = rw["name"]
    with tab:
        st.markdown(
            f"""
            <div class="card">
              <b>{name}</b>
              <span class="blue-tag">预测风险 {rw['pred_risk_score']}</span>
              <div style="opacity:.7;margin-top:6px;">{rw['why']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        emoji_key = f"emoji_on_{name}"
        cleaned = pretty_notice(rw["text"])
        final_txt = add_emojis_smart(cleaned) if st.session_state[emoji_key] else cleaned

        st.markdown(
            f"<div class='card' style='margin-top:12px;line-height:1.8;'>{html.escape(final_txt).replace(chr(10),'<br>')}</div>",
            unsafe_allow_html=True,
        )

        b1, b2 = st.columns(2, gap="medium")
        with b1:
            clipboard_copy_button(final_txt, key=f"copy_{name}")
        with b2:
            label = "取消emoji" if st.session_state[emoji_key] else "添加emoji"
            if st.button(label, key=f"emoji_btn_{name}", type="secondary", use_container_width=True):
                st.session_state[emoji_key] = not st.session_state[emoji_key]
                st.rerun()

st.markdown(
    "<div style='text-align:center;font-size:12px;opacity:.6;margin-top:24px;'>注：本工具仅用于文字优化与风险提示</div>",
    unsafe_allow_html=True,
)

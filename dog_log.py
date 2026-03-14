import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import os

# 1. UI/UX 기본 세팅
st.set_page_config(page_title="말티푸 헬스케어 v6.6", layout="centered", page_icon="🐾")

st.sidebar.header("⚙️ 관제 센터 설정")
ui_scale = st.sidebar.slider("🔍 전체 화면 비율 조절 (%)", 50, 150, 100) / 100.0

custom_css = f"""
<style>
    @media (max-width: 768px) {{
        div[data-testid="stHorizontalBlock"] {{
            flex-direction: row !important;
            flex-wrap: wrap !important;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
            flex: 1 1 45% !important;
            min-width: 45% !important;
        }}
    }}
    div.stButton > button {{
        font-size: {1.1 * ui_scale}rem !important;
        height: {3.5 * ui_scale}rem !important;
        border-radius: {10 * ui_scale}px !important;
        font-weight: bold !important;
        width: 100% !important;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

DATA_FILE = "dog_logs.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["시간", "활동"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

selected_date = st.date_input("📅 날짜 선택 (과거 로그 조회)", datetime.now())
target_date_str = selected_date.strftime("%Y-%m-%d")
today_str = datetime.now().strftime("%Y-%m-%d")

if not df.empty:
    df['날짜'] = df['시간'].apply(lambda x: x[:10])
    target_df = df[df['날짜'] == target_date_str]
else:
    target_df = pd.DataFrame(columns=["시간", "활동"])

st.markdown(f"### 🐾 말티푸 스마트 관제 센터")

def add_record(act, custom_time=None):
    global df
    t = custom_time if custom_time else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = {"시간": t, "활동": act}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.rerun()

# ==========================================
# [1구역] 실시간 듀얼 배변 모니터링 (대기 모드)
# ==========================================
st.subheader("💡 실시간 듀얼 배변 모니터링")
timer_scale = st.slider("↕️ 모니터링 창 크기 조절 (좌우로 밀어보세요)", 50, 150, 100) / 100.0

def get_timer_state(activity_name):
    records = target_df[target_df['활동'].str.contains(activity_name, na=False)]
    if not records.empty:
        last_record = records.iloc[-1]
        if "리셋" in last_record['활동']:
            return None
        else:
            return last_record['시간']
    return None

last_pee_raw = get_timer_state("소변")
last_poop_raw = get_timer_state("대변")

last_pee_iso = last_pee_raw.replace(" ", "T") if last_pee_raw else ""
last_poop_iso = last_poop_raw.replace(" ", "T") if last_poop_raw else ""

last_pee_time_str = last_pee_raw[11:16] if last_pee_raw else "--:--"
last_poop_time_str = last_poop_raw[11:16] if last_poop_raw else "--:--"

timer_html = f"""
<div style="display: flex; gap: 10px; justify-content: center; font-family: sans-serif;">
    <div style="flex: 1; background-color: #E8F5E9; padding: {15*timer_scale}px; border-radius: 12px; border: 3px solid #4CAF50; text-align: center;">
        <p style="color: #2E7D32; font-size: {0.8*timer_scale}rem; font-weight: bold; margin:0 0 5px 0;">💧 마지막 소변</p>
        <div style="color: #1B5E20; font-size: {2.2*timer_scale}rem; font-weight: 900; margin: 0;">{last_pee_time_str}</div>
        <div style="height: 2px; background-color: #A5D6A7; margin: {10*timer_scale}px 0;"></div>
        <div style="color: #4CAF50; font-size: {2.2*timer_scale}rem; font-weight: 900; margin: 0;">
            <span id="p_hrs">--</span><span class="dot" id="p_dot">:</span><span id="p_mins">--</span>
        </div>
        <p style="font-size: {0.8*timer_scale}rem; color: #4CAF50; margin:5px 0 0 0;">경과</p>
    </div>
    <div style="flex: 1; background-color: #FFF3E0; padding: {15*timer_scale}px; border-radius: 12px; border: 3px solid #FF9800; text-align: center;">
        <p style="color: #E65100; font-size: {0.8*timer_scale}rem; font-weight: bold; margin:0 0 5px 0;">💩 마지막 대변</p>
        <div style="color: #BF360C; font-size: {2.2*timer_scale}rem; font-weight: 900; margin: 0;">{last_poop_time_str}</div>
        <div style="height: 2px; background-color: #FFCC80; margin: {10*timer_scale}px 0;"></div>
        <div style="color: #FF9800; font-size: {2.2*timer_scale}rem; font-weight: 900; margin: 0;">
            <span id="d_hrs">--</span><span class="dot" id="d_dot">:</span><span id="d_mins">--</span>
        </div>
        <p style="font-size: {0.8*timer_scale}rem; color: #FF9800; margin:5px 0 0 0;">경과</p>
    </div>
</div>
<script>
    function update(id_h, id_m, dot_id, lastTimeStr) {{
        const el_h = document.getElementById(id_h);
        const el_m = document.getElementById(id_m);
        const dot = document.getElementById(dot_id);
        
        if(!lastTimeStr) {{
            el_h.innerText = '--';
            el_m.innerText = '--';
            dot.style.visibility = 'visible'; 
            return;
        }}
        
        const diff = new Date() - new Date(lastTimeStr);
        if(diff < 0) return;
        const mins = Math.floor(diff/60000);
        el_h.innerText = String(Math.floor(mins/60)).padStart(2,'0');
        el_m.innerText = String(mins%60).padStart(2,'0');
        
        dot.style.visibility = dot.style.visibility === 'hidden' ? 'visible' : 'hidden';
    }}
    setInterval(() => {{
        update('p_hrs', 'p_mins', 'p_dot', "{last_pee_iso}");
        update('d_hrs', 'd_mins', 'd_dot', "{last_poop_iso}");
    }}, 1000);
</script>
"""
components.html(timer_html, height=int(220 * timer_scale))

c1, c2 = st.columns(2)
with c1:
    if st.button("💧 소변 타이머 끄기 (--:--)", use_container_width=True): add_record("💦 소변 타이머 리셋")
with c2:
    if st.button("💩 대변 타이머 끄기 (--:--)", use_container_width=True): add_record("💩 대변 타이머 리셋")

with st.expander("⚙️ 배변 시간 수동 수정 (기록을 늦게 남겼을 때)"):
    manual_time = st.time_input("실제 활동 시간", datetime.now())
    col_a, col_b = st.columns(2)
    full_manual_time = f"{target_date_str} {manual_time.strftime('%H:%M:%S')}"
    if col_a.button("수동 소변 기록 (통계 미포함)"): add_record("💦 수동 소변", full_manual_time)
    if col_b.button("수동 대변 기록 (통계 미포함)"): add_record("💩 수동 대변", full_manual_time)

st.divider()

# ==========================================
# [2구역] 퀵 컨트롤 패널 (입력부)
# ==========================================
st.header("⭕ 퀵 컨트롤 패널")

st.write("🏠 **실내 활동**")
ic1, ic2, ic3, ic4 = st.columns(4)
with ic1: 
    if st.button("💦 소변", use_container_width=True): add_record("💦 집에서 소변")
with ic2: 
    if st.button("💩 대변", use_container_width=True): add_record("💩 집에서 대변")
with ic3: 
    if st.button("🍚 밥", use_container_width=True): add_record("🍚 밥 먹기")
with ic4: 
    if st.button("🔧 간식", use_container_width=True): add_record("🦴 간식")

st.write("🌳 **야외 산책**")
oc1, oc2, oc3, oc4 = st.columns(4)
with oc1: 
    if st.button("🦮+💦 소변", use_container_width=True): add_record("🦮+💦 산책 중 소변")
with oc2: 
    if st.button("🦮+💩 대변", use_container_width=True): add_record("🦮+💩 산책 중 대변")
with oc3: 
    if st.button("🦮+💦+💩 둘다", use_container_width=True): add_record("🦮+💦+💩 산책 중 소변과 대변")
with oc4: 
    if st.button("🦮 걷기만", use_container_width=True): add_record("🦮 일반 산책")

st.divider()

# ==========================================
# [3구역] 데이터베이스 유지보수 (수정부)
# ==========================================
st.header("🕒 데이터베이스 유지보수")

tab1, tab2 = st.tabs(["↩️ 퀵 실행 취소", "🗑️ 개별 로그 영구 삭제"])

with tab1:
    if not target_df.empty:
        st.info(f"마지막 기록: {target_df.iloc[-1]['시간']} | {target_df.iloc[-1]['활동']}")
        if st.button("↩️ 직전 기록 1개 삭제 (Undo)", use_container_width=True):
            df = df.drop(df.index[-1])
            save_data(df)
            st.rerun()
    else:
        st.write("오늘 기록이 없습니다.")

with tab2:
    st.write("잘못 입력된 특정 데이터를 선택하여 영구 삭제합니다.")
    if not target_df.empty:
        options = [f"[{idx}] {row['시간'][11:19]} | {row['활동']}" for idx, row in target_df.iterrows()]
        options.reverse()
        selected_log = st.selectbox("수정(삭제)할 오작동 기록 선택:", options)
        if st.button("🗑️ 선택한 데이터 삭제", use_container_width=True):
            real_idx = int(selected_log.split(']')[0].replace('[', ''))
            df = df.drop(real_idx)
            save_data(df)
            st.rerun()
    else:
        st.write("오늘 기록이 없습니다.")

st.divider()

# ==========================================
# [4구역] 최종 누적 데이터 (결과부)
# ==========================================
st.header(f"📊 {target_date_str} 최종 누적 데이터")

metrics_html = f"""
<div style="display: flex; flex-wrap: wrap; gap: {8 * ui_scale}px; justify-content: center; text-align: center; font-family: sans-serif; margin-bottom: 20px;">
"""
colors = [("소변", "#E3F2FD", "#1565C0"), ("대변", "#FFF3E0", "#E65100"), ("산책", "#E8F5E9", "#2E7D32"), ("밥", "#FCE4EC", "#AD1457"), ("간식", "#F3E5F5", "#6A1B9A")]

for label, bg, text_c in colors:
    # 🛠️ [핵심 로직] '리셋'과 '수동'이 포함된 기록은 횟수 계산에서 완전히 제외합니다.
    count = len(target_df[
        (target_df['활동'].str.contains(label, na=False)) & 
        (~target_df['활동'].str.contains('리셋', na=False)) &
        (~target_df['활동'].str.contains('수동', na=False))
    ])
    metrics_html += f"""
<div style="flex: 1 1 calc(30% - 10px); min-width: {70 * ui_scale}px; background-color: {bg}; padding: {12 * ui_scale}px 5px; border-radius: {12 * ui_scale}px; box-shadow: 0px 2px 4px rgba(0,0,0,0.08); border: 1px solid {text_c}33;">
<div style="font-size: {0.85 * ui_scale}rem; font-weight: bold; color: {text_c}; margin-bottom: 4px;">{label}</div>
<div style="font-size: {1.5 * ui_scale}rem; font-weight: 900; color: {text_c};">{count}</div>
</div>
"""
metrics_html += "</div>"
st.markdown(metrics_html, unsafe_allow_html=True)

st.write("")
st.write("")
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

# ==========================================
# 0. 한국 표준시(KST) 세팅
# ==========================================
KST = timezone(timedelta(hours=9))
def now_kst():
    return datetime.now(KST)

# ==========================================
# 1. UI/UX 기본 세팅 및 번역기 방지 설정
# ==========================================
st.set_page_config(page_title="말티푸 스마트 관제 센터", layout="centered", page_icon="🐾")

st.sidebar.header("⚙️ 관제 센터 설정")
ui_scale = st.sidebar.slider("🔍 화면 크기 조절 (%)", 50, 150, 100) / 100.0

# 🛠️ 스마트폰 구글 번역기가 맘대로 글자를 바꾸지 못하도록 방어막(notranslate) 추가
custom_css = f"""
<meta name="google" content="notranslate">
<style>
    /* 전체 페이지 번역 금지 클래스 적용 */
    body {{
        class: notranslate;
    }}
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

# 스트림릿 메인 컨테이너에 번역 방지 클래스 강제 삽입
st.markdown('<div class="notranslate" translate="no">', unsafe_allow_html=True)

DATA_FILE = "dog_logs.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["시간", "활동"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

selected_date = st.date_input("📅 날짜 선택 (과거 로그 조회)", now_kst().date())
target_date_str = selected_date.strftime("%Y-%m-%d")

if not df.empty:
    df['날짜'] = df['시간'].apply(lambda x: x[:10])
    target_df = df[df['날짜'] == target_date_str]
else:
    target_df = pd.DataFrame(columns=["시간", "활동"])

# 노트북 화면과 동일한 메인 타이틀
st.markdown(f"### 📊 말티푸 스마트 관제 센터")

def add_record(act, custom_time=None):
    global df
    t = custom_time if custom_time else now_kst().strftime("%Y-%m-%d %H:%M:%S")
    new_row = {"시간": t, "활동": act}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.rerun()

# ==========================================
# 2. 실시간 배변 모니터링 (노트북 텍스트 일치)
# ==========================================
st.subheader("💡 실시간 배변 모니터링")
timer_scale = st.slider("↕️ 타이머 크기 조절", 50, 150, 100, label_visibility="collapsed") / 100.0

def get_timer_state(activity_name):
    records = target_df[
        (target_df['활동'].str.contains(activity_name, na=False)) & 
        (~target_df['활동'].str.contains('누적', na=False)) & 
        (~target_df['활동'].str.contains('차감', na=False))
    ]
    if not records.empty:
        last_record = records.iloc[-1]
        if "타이머 끄기" in last_record['활동'] or "리셋" in last_record['활동']:
            return None
        return last_record['시간']
    return None

last_pee_iso = get_timer_state("소변").replace(" ", "T") + "+09:00" if get_timer_state("소변") else ""
last_poop_iso = get_timer_state("대변").replace(" ", "T") + "+09:00" if get_timer_state("대변") else ""

last_pee_time_str = get_timer_state("소변")[11:16] if get_timer_state("소변") else "--:--"
last_poop_time_str = get_timer_state("대변")[11:16] if get_timer_state("대변") else "--:--"

timer_html = f"""
<div style="display: flex; gap: 10px; justify-content: center; font-family: sans-serif;" class="notranslate" translate="no">
    <div style="flex: 1; background-color: #E8F5E9; padding: {15*timer_scale}px; border-radius: 12px; border: 3px solid #4CAF50; text-align: center;">
        <p style="color: #2E7D32; font-size: {0.8*timer_scale}rem; font-weight: bold; margin:0 0 5px 0;">💧 마지막 소변</p>
        <div style="color: #1B5E20; font-size: {2.2*timer_scale}rem; font-weight: 900; margin: 0;">{last_pee_time_str}</div>
        <div style="height: 2px; background-color: #A5D6A7; margin: {10*timer_scale}px 0;"></div>
        <div style="color: #4CAF50; font-size: {2.2*timer_scale}rem; font-weight: 900; margin: 0;">
            <span id="p_hrs">--</span><span class="dot" id="p_dot">:</span><span id="p_mins">--</span>
        </div>
    </div>
    <div style="flex: 1; background-color: #FFF3E0; padding: {15*timer_scale}px; border-radius: 12px; border: 3px solid #FF9800; text-align: center;">
        <p style="color: #E65100; font-size: {0.8*timer_scale}rem; font-weight: bold; margin:0 0 5px 0;">💩 마지막 대변</p>
        <div style="color: #BF360C; font-size: {2.2*timer_scale}rem; font-weight: 900; margin: 0;">{last_poop_time_str}</div>
        <div style="height: 2px; background-color: #FFCC80; margin: {10*timer_scale}px 0;"></div>
        <div style="color: #FF9800; font-size: {2.2*timer_scale}rem; font-weight: 900; margin: 0;">
            <span id="d_hrs">--</span><span class="dot" id="d_dot">:</span><span id="d_mins">--</span>
        </div>
    </div>
</div>
<script>
    function update(id_h, id_m, dot_id, lastTimeStr) {{
        const el_h = document.getElementById(id_h);
        const el_m = document.getElementById(id_m);
        const dot = document.getElementById(dot_id);
        if(!lastTimeStr) {{ el_h.innerText = '--'; el_m.innerText = '--'; dot.style.visibility = 'visible'; return; }}
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
components.html(timer_html, height=int(190 * timer_scale))

col_t1, col_t2 = st.columns(2)
with col_t1:
    if st.button("💧 소변 타이머 끄기", use_container_width=True, key="off_pee"): 
        add_record("💦 소변 타이머 끄기 (통계제외)")
with col_t2:
    if st.button("💩 대변 타이머 끄기", use_container_width=True, key="off_poop"): 
        add_record("💩 대변 타이머 끄기 (통계제외)")

# 서랍 텍스트 노트북 화면과 완전히 일치
with st.expander("⚙️ 전광판 시간 강제 수정 및 수동 입력 (상세 설정)"):
    manual_time = st.time_input("실제 배변 시간", now_kst().time(), key="time_manual")
    col_a, col_b = st.columns(2)
    full_manual_time = f"{target_date_str} {manual_time.strftime('%H:%M:%S')}"
    if col_a.button("💧 소변 시간 이걸로 변경", use_container_width=True, key="btn_manual_pee"): 
        add_record("💦 수동 소변 (통계제외)", full_manual_time)
    if col_b.button("💩 대변 시간 이걸로 변경", use_container_width=True, key="btn_manual_poop"): 
        add_record("💩 수동 대변 (통계제외)", full_manual_time)

st.divider()

# ==========================================
# 3. 퀵 컨트롤 패널 (노트북 텍스트 일치)
# ==========================================
st.header("⭕ 퀵 컨트롤 패널")

col_in1, col_in2 = st.columns(2)
with col_in1: 
    if st.button("💦 집에서 소변", use_container_width=True, key="btn_in_pee"): 
        add_record("💦 집에서 소변")
with col_in2: 
    if st.button("💩 집에서 대변", use_container_width=True, key="btn_in_poop"): 
        add_record("💩 집에서 대변")

st.write("🌳 **야외 산책**")
row1_col1, row1_col2 = st.columns(2)
with row1_col1: 
    if st.button("🦮 일반 산책", use_container_width=True, key="btn_out_walk"): 
        add_record("🦮 일반 산책")
with row1_col2: 
    if st.button("🦮+💦 산책 중 소변", use_container_width=True, key="btn_out_pee"): 
        add_record("🦮+💦 산책 중 소변")

row2_col1, row2_col2 = st.columns(2)
with row2_col1: 
    if st.button("🦮+💩 산책 중 대변", use_container_width=True, key="btn_out_poop"): 
        add_record("🦮+💩 산책 중 대변")
with row2_col2: 
    if st.button("🦮+💦+💩 소변과 대변", use_container_width=True, key="btn_out_both"): 
        add_record("🦮+💦+💩 산책 중 소변과 대변")

st.divider()

# ==========================================
# 4. 기록 취소 및 삭제 (노트북 텍스트 일치)
# ==========================================
st.header("🕒 기록 취소 및 삭제")

if not target_df.empty:
    st.success(f"✔️ 직전 기록: {target_df.iloc[-1]['시간'][11:16]} | {target_df.iloc[-1]['활동']}")
    
    if st.button("❌ 방금 누른 기록 지우기 (원상복구)", use_container_width=True, key="btn_undo_quick"):
        df = df.drop(df.index[-1])
        save_data(df)
        st.rerun()
else:
    st.info("오늘 아직 남긴 기록이 없습니다.")

with st.expander("⚙️ 예전 기록 지우기 (상세 설정)"):
    if not target_df.empty:
        options = [f"[{idx}] {row['시간'][11:16]} | {row['활동']}" for idx, row in target_df.iterrows()]
        options.reverse()
        selected_log = st.selectbox("지울 기록 선택:", options, key="select_del")
        if st.button("🗑️ 선택한 기록 완전히 지우기", key="btn_del_past"):
            real_idx = int(selected_log.split(']')[0].replace('[', ''))
            df = df.drop(real_idx)
            save_data(df)
            st.rerun()

st.divider()

# ==========================================
# 5. 누적 데이터 (노트북 텍스트 일치)
# ==========================================
st.header(f"📊 {target_date_str} 누적 데이터")

metrics_html = f"""
<div style="display: flex; flex-wrap: wrap; gap: {8 * ui_scale}px; justify-content: center; text-align: center; font-family: sans-serif; margin-bottom: 20px;">
"""
colors = [("소변", "#E3F2FD", "#1565C0"), ("대변", "#FFF3E0", "#E65100"), ("산책", "#E8F5E9", "#2E7D32")]

for label, bg, text_c in colors:
    base_logs = target_df[target_df['활동'].str.contains(label, na=False)]
    
    plus_count = len(base_logs[
        (~base_logs['활동'].str.contains('타이머 끄기|리셋', na=False)) & 
        (~base_logs['활동'].str.contains('통계제외', na=False)) &
        (~base_logs['활동'].str.contains('차감', na=False))
    ])
    plus_from_manual = len(base_logs[base_logs['활동'].str.contains('누적용 추가', na=False)])
    plus_total = plus_count + plus_from_manual

    minus_count = len(base_logs[base_logs['활동'].str.contains('차감', na=False)])
    
    final_count = plus_total - minus_count
    if final_count < 0: final_count = 0 
    
    metrics_html += f"""
<div style="flex: 1 1 calc(30% - 10px); min-width: {80 * ui_scale}px; background-color: {bg}; padding: {15 * ui_scale}px 5px; border-radius: {12 * ui_scale}px; box-shadow: 0px 2px 4px rgba(0,0,0,0.08); border: 1px solid {text_c}33;">
<div style="font-size: {1.0 * ui_scale}rem; font-weight: bold; color: {text_c}; margin-bottom: 5px;">{label}</div>
<div style="font-size: {1.8 * ui_scale}rem; font-weight: 900; color: {text_c};">{final_count}</div>
</div>
"""
metrics_html += "</div>"
st.markdown(metrics_html, unsafe_allow_html=True)

with st.expander("☝️ 터치하여 누적 횟수 강제 조절 (+ / -)"):
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        if st.button("소변 +1", use_container_width=True, key="plus_pee"): add_record("📊 누적용 추가 (소변)")
        if st.button("소변 -1", use_container_width=True, key="minus_pee"): add_record("📉 누적 차감 (소변)")
            
    with col_p2:
        if st.button("대변 +1", use_container_width=True, key="plus_poop"): add_record("📊 누적용 추가 (대변)")
        if st.button("대변 -1", use_container_width=True, key="minus_poop"): add_record("📉 누적 차감 (대변)")
            
    with col_p3:
        if st.button("산책 +1", use_container_width=True, key="plus_walk"): add_record("📊 누적용 추가 (산책)")
        if st.button("산책 -1", use_container_width=True, key="minus_walk"): add_record("📉 누적 차감 (산책)")

st.write("")
st.markdown('</div>', unsafe_allow_html=True) # 번역 방지 블록 닫기

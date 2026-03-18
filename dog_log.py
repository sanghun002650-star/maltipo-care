# ==========================================
# [ 말티푸 스마트 관제 센터 (내부 메모리 버전) ]
# 
# 📝 수정 이력 (Change Log)
# - v8.0 (2026-03-18): 구글 시트 연동 전 최종 안정화 버전.
# - v8.1 (2026-03-18): 화면 상단/하단 및 사이드바에 버전 정보 UI 추가.
# - v8.2 (2026-03-18): 소변/대변 시간 수동 수정 기능 및 타이머 끄기 버튼 추가.
# - v8.3 (2026-03-18): 시간 수동 기록 시 누적 횟수 제외 처리, 타이머 끄기 완벽 초기화 구현.
# ==========================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timezone, timedelta

# ==========================================
# 0. 앱 기본 설정 및 버전 정보
# ==========================================
APP_VERSION = "v8.3"
APP_UPDATE_DATE = "2026-03-18"

KST = timezone(timedelta(hours=9))
def now_kst():
    return datetime.now(KST)

st.set_page_config(page_title=f"스마트 관제 센터 {APP_VERSION}", layout="centered", page_icon="🐾")

# ==========================================
# 1. 사이드바: 설정 및 UI 조절
# ==========================================
st.sidebar.header("⚙️ 설정")
st.sidebar.caption(f"🚀 현재 버전: **{APP_VERSION}**") 

pet_name = st.sidebar.text_input("🐶 반려동물 이름", value="말티푸")
ui_scale = st.sidebar.slider("🔍 화면 크기 조절 (%)", 50, 150, 100) / 100.0

custom_css = f"""
<meta name="google" content="notranslate">
<style>
    body {{ class: notranslate; }}
    @media (max-width: 768px) {{
        div[data-testid="stHorizontalBlock"] {{ flex-direction: row !important; flex-wrap: wrap !important; }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{ flex: 1 1 45% !important; min-width: 45% !important; }}
    }}
    div.stButton > button {{
        font-size: {1.1 * ui_scale}rem !important; height: {3.2 * ui_scale}rem !important;
        border-radius: {10 * ui_scale}px !important; font-weight: bold !important; width: 100% !important;
    }}
    .footer {{
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #f8f9fa; color: #6c757d; text-align: center;
        padding: 5px 0; font-size: 0.8rem; border-top: 1px solid #e9ecef; z-index: 1000;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.markdown('<div class="notranslate" translate="no">', unsafe_allow_html=True)

# ==========================================
# 2. 데이터베이스 및 타이틀
# ==========================================
if 'pet_logs' not in st.session_state:
    st.session_state.pet_logs = pd.DataFrame(columns=["시간", "활동"])

df = st.session_state.pet_logs
selected_date = st.date_input("📅 날짜 선택", now_kst().date())
target_date_str = selected_date.strftime("%Y-%m-%d")

if not df.empty:
    df['날짜'] = df['시간'].apply(lambda x: str(x)[:10])
    target_df = df[df['날짜'] == target_date_str]
else:
    target_df = pd.DataFrame(columns=["시간", "활동", "날짜"])

st.markdown(f"### 📊 {pet_name} 스마트 관제 센터 <span style='font-size: 0.5em; color: gray;'>{APP_VERSION}</span>", unsafe_allow_html=True)

def add_record(act, custom_time=None):
    t = custom_time if custom_time else now_kst().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, new_row], ignore_index=True)
    st.rerun()

# ==========================================
# 3. 실시간 배변 모니터링 (타이머 & 시간수정)
# ==========================================
st.subheader("💡 실시간 배변 모니터링")

def get_timer_state(activity_name):
    """
    해당 활동의 마지막 시간을 찾습니다.
    '차감'이나 '끄기', '리셋' 기록이 있으면 타이머를 표시하지 않도록(None) 처리합니다.
    (수동으로 수정한 '시간수정' 기록은 타이머 기준점으로 사용됩니다.)
    """
    if not target_df.empty:
        # 순수한 활동 기록(수동 기록 포함)만 필터링 (누적 카운트용 키워드 제외)
        records = target_df[
            target_df['활동'].str.contains(activity_name) & 
            ~target_df['활동'].str.contains('차감')
        ]
        if not records.empty:
            last_record = records.iloc[-1]
            # 마지막 기록이 '끄기' 류의 명령이라면 None 반환 (초기화 상태)
            if "끄기" in last_record['활동'] or "리셋" in last_record['활동']:
                return None
            return str(last_record['시간'])
    return None

last_pee_iso = get_timer_state("소변").replace(" ", "T") + "+09:00" if get_timer_state("소변") else ""
last_poop_iso = get_timer_state("대변").replace(" ", "T") + "+09:00" if get_timer_state("대변") else ""
last_pee_time_str = get_timer_state("소변")[11:16] if get_timer_state("소변") else "--:--"
last_poop_time_str = get_timer_state("대변")[11:16] if get_timer_state("대변") else "--:--"

timer_html = f"""
<div style="display: flex; gap: 10px; justify-content: center; font-family: sans-serif;" class="notranslate" translate="no">
    <div style="flex: 1; background-color: #E8F5E9; padding: 15px; border-radius: 12px; border: 3px solid #4CAF50; text-align: center;">
        <p style="color: #2E7D32; font-size: 0.8rem; font-weight: bold; margin:0 0 5px 0;">💧 마지막 소변</p>
        <div style="color: #1B5E20; font-size: 2.2rem; font-weight: 900; margin: 0;">{last_pee_time_str}</div>
        <div style="color: #4CAF50; font-size: 2.2rem; font-weight: 900; margin: 0;">
            <span id="p_hrs">--</span><span class="dot" id="p_dot">:</span><span id="p_mins">--</span>
        </div>
    </div>
    <div style="flex: 1; background-color: #FFF3E0; padding: 15px; border-radius: 12px; border: 3px solid #FF9800; text-align: center;">
        <p style="color: #E65100; font-size: 0.8rem; font-weight: bold; margin:0 0 5px 0;">💩 마지막 대변</p>
        <div style="color: #BF360C; font-size: 2.2rem; font-weight: 900; margin: 0;">{last_poop_time_str}</div>
        <div style="color: #FF9800; font-size: 2.2rem; font-weight: 900; margin: 0;">
            <span id="d_hrs">--</span><span class="dot" id="d_dot">:</span><span id="d_mins">--</span>
        </div>
    </div>
</div>
<script>
    function update(id_h, id_m, dot_id, lastTimeStr) {{
        const el_h = document.getElementById(id_h);
        const el_m = document.getElementById(id_m);
        const dot = document.getElementById(dot_id);
        
        // 마지막 시간이 없으면(또는 리셋되었다면) 표시를 초기화
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
components.html(timer_html, height=150)

# --- 시간 수정 및 끄기 버튼 영역 ---
edit_col1, edit_col2 = st.columns(2)
with edit_col1:
    with st.expander("⏱️ 소변 시간 수정/종료"):
        new_time_p = st.time_input("소변 시각 선택", now_kst().time(), key="time_p")
        if st.button("수정된 시각으로 기록", key="btn_p"):
            final_dt_p = f"{target_date_str} {new_time_p.strftime('%H:%M:%S')}"
            # ★ 핵심: '(통계제외)' 문구를 추가하여 아래 get_count 함수에서 횟수를 세지 않도록 합니다.
            add_record("💦 소변(시간수정) (통계제외)", custom_time=final_dt_p)
            
        if st.button("💧 소변 타이머 리셋(끄기)", use_container_width=True):
            # ★ 핵심: '끄기' 문구를 남겨 get_timer_state가 이를 인식하고 타이머를 None으로 만듭니다.
            add_record("💦 소변 타이머 끄기 (통계제외)")

with edit_col2:
    with st.expander("⏱️ 대변 시간 수정/종료"):
        new_time_d = st.time_input("대변 시각 선택", now_kst().time(), key="time_d")
        if st.button("수정된 시각으로 기록", key="btn_d"):
            final_dt_d = f"{target_date_str} {new_time_d.strftime('%H:%M:%S')}"
            add_record("💩 대변(시간수정) (통계제외)", custom_time=final_dt_d)
            
        if st.button("💩 대변 타이머 리셋(끄기)", use_container_width=True):
            add_record("💩 대변 타이머 끄기 (통계제외)")

# ==========================================
# 4. 퀵 컨트롤 패널
# ==========================================
st.divider()
st.header("🔘 퀵 컨트롤 패널")
col_in1, col_in2 = st.columns(2)
with col_in1: 
    if st.button("💦 집에서 소변", use_container_width=True): add_record("💦 집에서 소변")
with col_in2: 
    if st.button("💩 집에서 대변", use_container_width=True): add_record("💩 집에서 대변")

st.write("🌳 **야외 산책**")
row1_col1, row1_col2 = st.columns(2)
with row1_col1: 
    if st.button("🦮 일반 산책", use_container_width=True): add_record("🦮 일반 산책")
with row1_col2: 
    if st.button("🦮+💦 산책 중 소변", use_container_width=True): add_record("🦮+💦 산책 중 소변")

row2_col1, row2_col2 = st.columns(2)
with row2_col1: 
    if st.button("🦮+💩 산책 중 대변", use_container_width=True): add_record("🦮+💩 산책 중 대변")
with row2_col2: 
    if st.button("🦮+💦+💩 소변과 대변", use_container_width=True): add_record("🦮+💦+💩 산책 중 소변과 대변")

# ==========================================
# 5. 기록 관리 (취소 및 수동 조정)
# ==========================================
st.divider()
st.header("🕒 기록 관리")
if not target_df.empty:
    last_idx = target_df.index[-1]
    st.success(f"✔️ 직전 기록: {target_df.loc[last_idx, '시간'][11:16]} | {target_df.loc[last_idx, '활동']}")
    if st.button("❌ 방금 기록 취소", use_container_width=True):
        st.session_state.pet_logs = st.session_state.pet_logs.drop(last_idx)
        st.rerun()

st.write("🔢 **누적 횟수 수동 조정**")
adj_col1, adj_col2, adj_col3 = st.columns(3)
with adj_col1:
    if st.button("💦 소변 -1", use_container_width=True): add_record("💦 소변 차감 (-1)")
with adj_col2:
    if st.button("💩 대변 -1", use_container_width=True): add_record("💩 대변 차감 (-1)")
with adj_col3:
    if st.button("🦮 산책 -1", use_container_width=True): add_record("🦮 산책 차감 (-1)")

# ==========================================
# 6. 누적 데이터 현황
# ==========================================
st.divider()
st.header(f"📊 {target_date_str} 누적 현황")

def get_count(label):
    if target_df.empty: return 0
    # '통계제외', '차감', '끄기'가 포함된 기록은 세지 않습니다.
    plus = len(target_df[
        target_df['활동'].str.contains(label) & 
        ~target_df['활동'].str.contains('차감|끄기|통계제외')
    ])
    # '-1' 버튼을 누른 횟수
    minus = len(target_df[
        target_df['활동'].str.contains(label) & 
        target_df['활동'].str.contains('차감')
    ])
    return max(0, plus - minus)

counts = [("소변", get_count("소변"), "#E3F2FD", "#1565C0"),
          ("대변", get_count("대변"), "#FFF3E0", "#E65100"),
          ("산책", get_count("산책"), "#E8F5E9", "#2E7D32")]

metrics_html = '<div style="display: flex; gap: 10px; justify-content: center; text-align: center; margin-bottom: 50px;">'
for label, count, bg, text_c in counts:
    metrics_html += f'<div style="flex: 1; background-color: {bg}; padding: 15px; border-radius: 12px; border: 1px solid {text_c}33;"><div style="font-size: 1rem; font-weight: bold; color: {text_c};">{label}</div><div style="font-size: 1.8rem; font-weight: 900; color: {text_c};">{count}</div></div>'
metrics_html += "</div>"
st.markdown(metrics_html, unsafe_allow_html=True)

# ==========================================
# 7. 하단 고정 꼬리말 (버전 정보)
# ==========================================
footer_html = f"""
<div class="footer notranslate" translate="no">
    Smart Pet Care Center <strong>{APP_VERSION}</strong> | Last Update: {APP_UPDATE_DATE}
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)

# ==========================================
# END OF CODE - v8.3
# ==========================================

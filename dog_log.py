import streamlit as st
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

# ==========================================
# 0. 한국 표준시(KST) 세팅
# ==========================================
KST = timezone(timedelta(hours=9))
def now_kst():
    return datetime.now(KST)

st.set_page_config(page_title="스마트 관제 센터", layout="centered", page_icon="🐾")

# ==========================================
# 1. 사이드바: 로그인(ID) 및 설정
# ==========================================
st.sidebar.header("🔐 로그인 및 설정")
st.sidebar.info("ID를 다르게 입력하면 각자의 데이터가 분리되어 저장됩니다.")

user_id = st.sidebar.text_input("👤 사용자 ID (영어/숫자 권장)", value="7475")
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
        font-size: {1.1 * ui_scale}rem !important; height: {3.5 * ui_scale}rem !important;
        border-radius: {10 * ui_scale}px !important; font-weight: bold !important; width: 100% !important;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.markdown('<div class="notranslate" translate="no">', unsafe_allow_html=True)

# ==========================================
# 2. 구글 시트 데이터베이스 연동 엔진
# ==========================================
# 에러 처리: Secrets 설정이 없거나 잘못되었을 때를 대비
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"⚠️ 구글 시트 연결 설정에 문제가 있습니다. Secrets 설정을 확인해주세요: {e}")
    st.stop()

@st.cache_data(ttl=2) 
def load_data(uid):
    try:
        df = conn.read(worksheet=uid, ttl=0)
        if df.empty or "시간" not in df.columns:
            return pd.DataFrame(columns=["시간", "활동"])
        return df.dropna(subset=["시간", "활동"])
    except Exception as e:
        # 시트 탭이 없거나 읽기 권한이 없을 때
        st.warning(f"⚠️ 데이터를 불러오지 못했습니다. '{uid}' 시트가 없거나 권한 문제가 있을 수 있습니다. 새 시트를 생성합니다.")
        return pd.DataFrame(columns=["시간", "활동"])

def save_data(df, uid):
    try:
        conn.update(worksheet=uid, data=df)
        st.cache_data.clear() 
    except Exception as e:
        # 쓰기 권한이 없거나 다른 오류가 발생했을 때 앱이 멈추지 않도록 에러 메시지 출력
        st.error(f"🚨 구글 시트 저장 실패! 권한 설정을 확인하세요: {e}")

df = load_data(user_id)

selected_date = st.date_input("📅 날짜 선택 (과거 로그 조회)", now_kst().date())
target_date_str = selected_date.strftime("%Y-%m-%d")

if not df.empty:
    df['날짜'] = df['시간'].apply(lambda x: str(x)[:10])
    target_df = df[df['날짜'] == target_date_str]
else:
    target_df = pd.DataFrame(columns=["시간", "활동", "날짜"]) # 날짜 컬럼 추가

st.markdown(f"### 📊 {pet_name} 스마트 관제 센터 (ID: {user_id})")

def add_record(act, custom_time=None):
    global df
    t = custom_time if custom_time else now_kst().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df, user_id) 
    st.rerun()

# ==========================================
# 3. 실시간 배변 모니터링 (타이머)
# ==========================================
st.subheader("💡 실시간 배변 모니터링")
timer_scale = st.slider("↕️ 타이머 크기 조절", 50, 150, 100, label_visibility="collapsed") / 100.0

def get_timer_state(activity_name):
    # target_df가 비어있지 않고, '활동' 컬럼이 존재하는지 확인
    if not target_df.empty and '활동' in target_df.columns:
        records = target_df[
            (target_df['활동'].str.contains(activity_name, na=False)) & 
            (~target_df['활동'].str.contains('누적', na=False)) & 
            (~target_df['활동'].str.contains('차감', na=False))
        ]
        if not records.empty:
            last_record = records.iloc[-1]
            if "타이머 끄기" in last_record['활동'] or "리셋" in last_record['활동']:
                return None
            return str(last_record['시간'])
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
    if st.button("💧 소변 타이머 끄기", use_container_width=True): add_record("💦 소변 타이머 끄기 (통계제외)")
with col_t2:
    if st.button("💩 대변 타이머 끄기", use_container_width=True): add_record("💩 대변 타이머 끄기 (통계제외)")

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
# 5. 기록 취소 및 삭제
# ==========================================
st.divider()
st.header("🕒 직전 기록 취소")

if not target_df.empty and '시간' in target_df.columns and '활동' in target_df.columns:
    last_target_idx = target_df.index[-1]
    st.success(f"✔️ 직전 기록: {str(target_df.loc[last_target_idx, '시간'])[11:16]} | {target_df.loc[last_target_idx, '활동']}")
    
    if st.button("❌ 방금 누른 기록 지우기", use_container_width=True):
        df = df.drop(last_target_idx)
        save_data(df, user_id)
        st.rerun()
else:
    st.info("해당 날짜에 남긴 기록이 없습니다.")

# ==========================================
# 6. 누적 데이터
# ==========================================
st.divider()
st.header(f"📊 {target_date_str} 누적 데이터")

metrics_html = f"""<div style="display: flex; flex-wrap: wrap; gap: {8 * ui_scale}px; justify-content: center; text-align: center; margin-bottom: 20px;">"""
colors = [("소변", "#E3F2FD", "#1565C0"), ("대변", "#FFF3E0", "#E65100"), ("산책", "#E8F5E9", "#2E7D32")]

for label, bg, text_c in colors:
    if not target_df.empty and '활동' in target_df.columns:
        base_logs = target_df[target_df['활동'].str.contains(label, na=False)]
        plus_count = len(base_logs[(~base_logs['활동'].str.contains('타이머 끄기|리셋', na=False)) & (~base_logs['활동'].str.contains('통계제외', na=False)) & (~base_logs['활동'].str.contains('차감', na=False))])
        minus_count = len(base_logs[base_logs['활동'].str.contains('차감', na=False)])
        final_count = max(0, plus_count - minus_count)
    else:
        final_count = 0
    
    metrics_html += f"""
    <div style="flex: 1 1 calc(30% - 10px); min-width: {80 * ui_scale}px; background-color: {bg}; padding: {15 * ui_scale}px 5px; border-radius: {12 * ui_scale}px; box-shadow: 0px 2px 4px rgba(0,0,0,0.08); border: 1px solid {text_c}33;">
    <div style="font-size: {1.0 * ui_scale}rem; font-weight: bold; color: {text_c}; margin-bottom: 5px;">{label}</div>
    <div style="font-size: {1.8 * ui_scale}rem; font-weight: 900; color: {text_c};">{final_count}</div>
    </div>
    """
metrics_html += "</div>"
st.markdown(metrics_html, unsafe_allow_html=True)

# ==========================================
# 🛑 안전 종료 버튼 (모바일 호환)
# ==========================================
safe_close_html = """
<style>
    .floating-close-btn { position: fixed; bottom: 40px; right: 20px; width: 55px; height: 55px; background-color: #E53935; color: white !important; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; box-shadow: 2px 4px 8px rgba(0,0,0,0.3); border-radius: 10px; z-index: 999998; text-decoration: none !important; }
    #safe-close-screen { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: #111; color: white; z-index: 9999999; text-align: center; }
    #safe-close-screen:target { display: flex; flex-direction: column; justify-content: center; align-items: center; }
</style>
<a href="#safe-close-screen" class="floating-close-btn" title="앱 화면 차단">✖</a>
<div id="safe-close-screen">
    <h2 style="color:white; margin-bottom: 20px; font-size: 24px;">🔒 앱이 잠겼습니다</h2>
    <p style="color:#aaa; font-size: 16px; line-height: 1.6;">모든 버튼 터치가 차단되었습니다.<br>스마트폰의 [홈 버튼]을 눌러 종료해 주세요.</p>
</div>
"""
st.markdown(safe_close_html, unsafe_allow_html=True)

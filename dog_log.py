# ==========================================
# [ 말티푸 스마트 관제 센터 (구글 시트 클라우드 버전) ]
# 
# 📝 수정 이력 (Change Log)
# - v9.5 (2026-03-18): 구글 시트 영구 저장 엔진 결합.
# - v9.5.1 (2026-03-18): 기록 취소 파이썬 문법 에러 수정.
# - v9.5.2 (2026-03-18): 침묵의 에러(Silent Failure) 완벽 차단. 
#                      저장 실패 시 강제 새로고침을 막고 정확한 에러 원인(탭 없음 등)을 출력하도록 개선.
# ==========================================

import streamlit as st
import streamlit.components.v1 as components  # ★ 절대 지우지 마세요! 타이머 전광판 도구입니다.
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timezone, timedelta
import urllib.parse

# ==========================================
# 0. 앱 기본 설정 및 버전 정보
# ==========================================
APP_VERSION = "v9.5.2(클라우드 안전판)"
APP_UPDATE_DATE = "2026-03-18"

KST = timezone(timedelta(hours=9))
def now_kst():
    return datetime.now(KST)

st.set_page_config(page_title=f"스마트 관제 센터 {APP_VERSION}", layout="centered", page_icon="🐾")

# ==========================================
# 1. 사이드바: 설정 및 이름/ID 관리
# ==========================================
st.sidebar.header("⚙️ 설정")
st.sidebar.caption(f"🚀 현재 버전: **{APP_VERSION}**") 

# 사용자 ID (구글 시트 탭 이름으로 사용됨)
user_id = st.sidebar.text_input("👤 데이터 저장 ID (구글 시트 탭 이름)", value="7475")
st.sidebar.caption("※ 주의: 여기에 입력한 ID와 똑같은 이름의 '탭'이 구글 시트에 있어야 저장이 됩니다!")

# 이름 URL 파라미터 로직
query_params = st.query_params
default_name = "말티푸"
if "name" in query_params:
    default_name = urllib.parse.unquote(query_params["name"])

if 'pet_name' not in st.session_state:
    st.session_state.pet_name = default_name

pet_name_input = st.sidebar.text_input("🐶 반려동물 이름", value=st.session_state.pet_name)
if pet_name_input != st.session_state.pet_name:
    st.session_state.pet_name = pet_name_input
    st.query_params["name"] = urllib.parse.quote(pet_name_input)
    st.sidebar.success(f"이름이 변경되었습니다! 스마트폰 [홈 화면에 추가]를 다시 해주세요.")

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
# 2. 구글 시트 데이터베이스 연동 엔진 
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️ 구글 시트 연결 설정(Secrets)에 문제가 있습니다.")
    st.stop()

@st.cache_data(ttl=2) 
def load_data(uid):
    try:
        loaded_df = conn.read(worksheet=uid, ttl=0)
        if loaded_df.empty or "시간" not in loaded_df.columns:
            return pd.DataFrame(columns=["시간", "활동"])
        return loaded_df.dropna(subset=["시간", "활동"])
    except Exception as e:
        # 데이터를 읽지 못했을 때의 안내 문구 강화
        st.warning(f"⚠️ 구글 시트에서 '{uid}' 탭을 찾을 수 없거나 데이터가 비어있습니다. 버튼을 눌러 저장을 시도해보세요.")
        return pd.DataFrame(columns=["시간", "활동"])

def save_data(data_to_save, uid):
    """안전장치가 추가된 저장 함수. 성공 여부와 메시지를 반환합니다."""
    try:
        conn.update(worksheet=uid, data=data_to_save)
        st.cache_data.clear() 
        return True, "저장 성공"
    except Exception as e:
        err_msg = str(e).lower()
        if "not found" in err_msg or "worksheet" in err_msg:
            return False, f"🚨 저장 실패: 구글 시트에 '{uid}'(이)라는 이름의 탭이 없습니다! 구글 시트를 열고 맨 아래 [+] 버튼을 눌러 '{uid}' 탭을 먼저 만들어주세요."
        else:
            return False, f"🚨 저장 실패: 시트 공유 권한을 확인해주세요. (에러: {e})"

# 데이터 불러오기
df = load_data(user_id)
selected_date = st.date_input("📅 날짜 선택", now_kst().date())
target_date_str = selected_date.strftime("%Y-%m-%d")

if not df.empty:
    df['날짜'] = df['시간'].apply(lambda x: str(x)[:10])
    target_df = df[df['날짜'] == target_date_str]
else:
    target_df = pd.DataFrame(columns=["시간", "활동", "날짜"])

st.markdown(f"### 📊 {st.session_state.pet_name} 스마트 관제 센터 <span style='font-size: 0.5em; color: gray;'>{APP_VERSION}</span>", unsafe_allow_html=True)

def add_record(act, custom_time=None):
    t = custom_time if custom_time else now_kst().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    
    # 임시로 합친 데이터를 먼저 만듭니다 (에러가 날 경우 기존 데이터 보호)
    new_df = pd.concat([df, new_row], ignore_index=True)
    
    # 구글 시트에 저장 시도 (백그라운드)
    success, msg = save_data(new_df, user_id)
    
    if success:
        st.rerun() # 성공 시에만 화면 새로고침 (수치 갱신)
    else:
        st.error(msg) # 실패 시 새로고침을 멈추고 에러 메시지를 화면에 띄웁니다!

# ==========================================
# 3. 실시간 배변 모니터링 (타이머 & 시간수정)
# ==========================================
st.subheader("💡 실시간 배변 모니터링")

def get_timer_state(activity_name):
    if not target_df.empty:
        records = target_df[
            target_df['활동'].str.contains(activity_name, na=False) & 
            ~target_df['활동'].str.contains('차감', na=False)
        ]
        if not records.empty:
            last_record = records.iloc[-1]
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
components.html(timer_html, height=150)

# --- 시간 수정 및 끄기 버튼 영역 ---
edit_col1, edit_col2 = st.columns(2)
with edit_col1:
    with st.expander("⏱️ 소변 시간 수정/종료"):
        new_time_p = st.time_input("소변 시각 선택", now_kst().time(), key="time_p")
        if st.button("수정된 시각으로 기록", key="btn_p"):
            final_dt_p = f"{target_date_str} {new_time_p.strftime('%H:%M:%S')}"
            add_record("💦 소변(시간수정) (통계제외)", custom_time=final_dt_p)
            
        if st.button("💧 소변 타이머 리셋(끄기)", use_container_width=True):
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
# 5. 누적 데이터 현황 및 수동 조정
# ==========================================
st.divider()
st.header(f"📊 {target_date_str} 누적 현황")

def get_count(label):
    if target_df.empty: return 0
    plus = len(target_df[
        target_df['활동'].str.contains(label, na=False) & 
        ~target_df['활동'].str.contains('차감|끄기|통계제외', na=False)
    ])
    minus = len(target_df[
        target_df['활동'].str.contains(label, na=False) & 
        target_df['활동'].str.contains('차감', na=False)
    ])
    return max(0, plus - minus)

counts = [("소변", get_count("소변"), "#E3F2FD", "#1565C0"),
          ("대변", get_count("대변"), "#FFF3E0", "#E65100"),
          ("산책", get_count("산책"), "#E8F5E9", "#2E7D32")]

metrics_html = '<div style="display: flex; gap: 10px; justify-content: center; text-align: center; margin-bottom: 20px;">'
for label, count, bg, text_c in counts:
    metrics_html += f'<div style="flex: 1; background-color: {bg}; padding: 15px; border-radius: 12px; border: 1px solid {text_c}33;"><div style="font-size: 1rem; font-weight: bold; color: {text_c};">{label}</div><div style="font-size: 1.8rem; font-weight: 900; color: {text_c};">{count}</div></div>'
metrics_html += "</div>"
st.markdown(metrics_html, unsafe_allow_html=True)

st.write("🔢 **누적 횟수 수동 조정**")
adj_col1, adj_col2, adj_col3 = st.columns(3)
with adj_col1:
    if st.button("💦 소변 -1", use_container_width=True): add_record("💦 소변 차감 (-1)")
with adj_col2:
    if st.button("💩 대변 -1", use_container_width=True): add_record("💩 대변 차감 (-1)")
with adj_col3:
    if st.button("🦮 산책 -1", use_container_width=True): add_record("🦮 산책 차감 (-1)")

# ==========================================
# 6. 기록 관리 (취소 전용)
# ==========================================
st.divider()
st.header("🕒 기록 관리")
if not target_df.empty:
    last_idx = target_df.index[-1]
    st.success(f"✔️ 직전 기록: {target_df.loc[last_idx, '시간'][11:16]} | {target_df.loc[last_idx, '활동']}")
    if st.button("❌ 방금 기록 취소", use_container_width=True):
        new_df = df.drop(last_idx)
        success, msg = save_data(new_df, user_id)
        if success:
            st.rerun()
        else:
            st.error(msg)

# ==========================================
# 7. 안전 종료 버튼
# ==========================================
st.divider()
st.markdown("---")
close_html = """
<style>
    #close-screen {
        display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: rgba(0,0,0,0.9); color: white; z-index: 9999999;
        text-align: center; flex-direction: column; justify-content: center; align-items: center;
    }
    #close-screen:target { display: flex; }
    .close-btn {
        background-color: #FF8A65; 
        color: white; padding: 15px 30px; border-radius: 8px;
        text-decoration: none; font-size: 1.2rem; font-weight: bold; width: 80%; max-width: 300px;
        text-align: center; margin: 20px auto; display: block; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 2px solid #FF5722; 
    }
</style>
<a href="#close-screen" class="close-btn">🚪 앱 안전 종료</a>

<div id="close-screen">
    <h1 style="color: white; margin-bottom: 10px;">🔒 화면 보호 모드</h1>
    <p style="color: #ccc; margin-bottom: 30px; font-size: 1.1rem; line-height: 1.5;">
        모든 버튼 터치가 차단되었습니다.<br>
        데이터는 구글 클라우드에 안전하게 보존 중입니다.<br><br>
        <strong>스마트폰의 [홈 버튼]을 눌러<br>바탕화면으로 나가주세요.</strong>
    </p>
    <a href="#" style="color: #666; text-decoration: underline; font-size: 0.9rem;">다시 앱으로 돌아가기</a>
</div>
"""
st.markdown(close_html, unsafe_allow_html=True)

# ==========================================
# 8. 하단 고정 꼬리말
# ==========================================
footer_html = f"""
<div class="footer notranslate" translate="no" style="margin-bottom: 50px;">
    Smart Pet Care Center <strong>{APP_VERSION}</strong> | Last Update: {APP_UPDATE_DATE}
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)

# ==========================================
# END OF CODE - v9.5.2
# ==========================================

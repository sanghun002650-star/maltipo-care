import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import requests
import extra_streamlit_components as stx
import time

# ==========================================
# 0. 기본 설정
# ==========================================
APP_VERSION = "v13.3.0"
UPDATE_DATE = "2026-03-30"  # 🚀 버전 업데이트 시 이 두 변수만 수정하세요!

KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)
FIREBASE_URL = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/"

# initial_sidebar_state="collapsed"를 통해 앱 실행 시 무조건 사이드바를 닫아둡니다.
st.set_page_config(page_title="🐾 관제 센터", layout="centered", page_icon="🐾", initial_sidebar_state="collapsed")

# --- 쿠키 매니저 ---
cookie_manager = stx.CookieManager(key="pet_cookie_manager")
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'force_logout' not in st.session_state: st.session_state.force_logout = False

# ==========================================
# 🚪 로그인 화면
# ==========================================
saved_user = cookie_manager.get(cookie="saved_username")
if saved_user and not st.session_state.logged_in and not st.session_state.force_logout:
    st.session_state.logged_in = True
    st.session_state.username = saved_user
    st.rerun()

if not st.session_state.logged_in:
    st.markdown("""
    <div style='text-align:center; padding: 30px 0 10px;'>
        <div style='font-size:3.5rem;'>🐾</div>
        <div style='font-size:1.5rem; font-weight:900; color:#1e293b; margin-top:8px;'>스마트 관제 센터</div>
        <div style='font-size:0.8rem; color:#94a3b8; margin-top:4px;'>가족 전용 클라우드 플랫폼</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 로그인", "📝 새 계정 만들기"])
    with tab1:
        login_id = st.text_input("아이디", key="l_id", placeholder="아이디 입력")
        login_pw = st.text_input("비밀번호", type="password", key="l_pw", placeholder="비밀번호 입력")
        auto_login = st.checkbox("로그인 유지 (6개월)", value=True)
        if st.button("접속하기 🚀", use_container_width=True, type="primary"):
            if login_id and login_pw:
                try:
                    res = requests.get(f"{FIREBASE_URL}users/{login_id}/password.json", timeout=5)
                    if res.status_code == 200 and res.json() == login_pw:
                        if auto_login:
                            cookie_manager.set("saved_username", login_id, expires_at=datetime.now() + timedelta(days=180))
                        else:
                            cookie_manager.delete("saved_username")
                        st.session_state.force_logout = False
                        st.session_state.logged_in = True
                        st.session_state.username = login_id
                        time.sleep(0.3); st.rerun()
                    else:
                        st.error("❌ 아이디 또는 비밀번호가 틀렸습니다.")
                except requests.exceptions.RequestException:
                    st.error("⚠️ 네트워크 오류. 인터넷 연결을 확인해주세요.")
            else:
                st.warning("아이디와 비밀번호를 모두 입력하세요.")
                
    with tab2:
        reg_id = st.text_input("아이디", key="r_id", placeholder="사용할 아이디")
        reg_pw = st.text_input("비밀번호", type="password", key="r_pw", placeholder="비밀번호")
        if st.button("계정 생성 💾", use_container_width=True):
            if reg_id and reg_pw:
                try:
                    res = requests.get(f"{FIREBASE_URL}users/{reg_id}.json", timeout=5)
                    if res.status_code == 200 and res.json() is not None:
                        st.error("❌ 이미 존재하는 아이디입니다.")
                    else:
                        requests.put(f"{FIREBASE_URL}users/{reg_id}/password.json", json=reg_pw, timeout=5)
                        default_prof = {"pet_name": "강아지", "birth": "", "weight": "", "gender": "수컷", "memo": ""}
                        requests.put(f"{FIREBASE_URL}users/{reg_id}/profile.json", json=default_prof, timeout=5)
                        default_settings = {
                            "btn_h": 4.2, "hdr_color": "#94a3b8",
                            "order": {"타이머":1, "누적데이터":2, "배변기록":3, "산책기록":4, "건강미용":5, "수동조절":6, "기록차감":7, "활동로그":8, "주간통계":9}
                        }
                        requests.put(f"{FIREBASE_URL}users/{reg_id}/settings.json", json=default_settings, timeout=5)
                        st.success("✅ 계정 생성 완료! 로그인 탭에서 접속하세요.")
                except requests.exceptions.RequestException:
                    st.error("⚠️ 네트워크 오류.")
            else:
                st.warning("모든 항목을 입력하세요.")
    st.stop()

# ==========================================
# ☁️ 클라우드 엔진 & 설정 로더
# ==========================================
username = st.session_state.username

def _unique_ts(base_time=None):
    t = base_time if base_time else now_kst()
    return t.strftime("%Y-%m-%d %H:%M:%S.%f")

def load_profile():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/profile.json", timeout=5)
        if res.status_code == 200 and res.json(): return res.json()
    except: pass
    return {"pet_name": "강아지", "birth": "", "weight": "", "gender": "수컷", "memo": ""}

def load_settings():
    default_settings = {
        "btn_h": 4.2, "hdr_color": "#94a3b8",
        "order": {"타이머":1, "누적데이터":2, "배변기록":3, "산책기록":4, "건강미용":5, "수동조절":6, "기록차감":7, "활동로그":8, "주간통계":9}
    }
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/settings.json", timeout=5)
        if res.status_code == 200 and res.json():
            loaded = res.json()
            for k in default_settings:
                if k not in loaded: loaded[k] = default_settings[k]
            if "식사건강" in loaded.get("order", {}):
                loaded["order"]["건강미용"] = loaded["order"].pop("식사건강")
            return loaded
    except: pass
    return default_settings

def save_profile(profile):
    try: requests.put(f"{FIREBASE_URL}users/{username}/profile.json", json=profile, timeout=5)
    except: st.error("⚠️ 저장 실패")

def save_settings(settings_data):
    try: requests.put(f"{FIREBASE_URL}users/{username}/settings.json", json=settings_data, timeout=5)
    except: st.error("⚠️ 설정 저장 실패")

def load_data():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/logs.json", timeout=5)
        if res.status_code == 200 and res.json():
            records = [{"시간": k, "활동": v} for k, v in res.json().items()]
            return pd.DataFrame(records).sort_values("시간").reset_index(drop=True)
    except: st.warning("⚠️ 데이터 로드 실패")
    return pd.DataFrame(columns=["시간", "활동"])

def add_record(act, c_time=None):
    t = c_time if c_time else _unique_ts()
    try: requests.patch(f"{FIREBASE_URL}users/{username}/logs.json", json={t: act}, timeout=5)
    except:
        st.error("⚠️ 기록 저장 실패"); return
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, new_row], ignore_index=True)
    st.rerun()

if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'settings' not in st.session_state: st.session_state.settings = load_settings()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()

# ==========================================
# 🎨 동적 CSS 인젝션 (설정값 기반)
# ==========================================
DYNAMIC_BTN_H = st.session_state.settings.get("btn_h", 4.2)
DYNAMIC_HDR_COLOR = st.session_state.settings.get("hdr_color", "#94a3b8")

st.markdown(f"""
<style>
.block-container {{ padding: 0.5rem 0.75rem 6rem 0.75rem !important; max-width: 500px !important; }}
::-webkit-scrollbar {{ width: 0px; }}

.header-card {{
    display:flex; justify-content:space-between; align-items:center; 
    background:linear-gradient(135deg,#667eea,#764ba2); 
    border-radius:18px; padding:18px 20px; margin-bottom:15px; color:white;
    min-height: 85px; line-height: 1.4; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}}

div.stButton > button {{
    height: {DYNAMIC_BTN_H}rem !important;
    border-radius: 16px !important; font-weight: 900 !important; font-size: 1.05rem !important;
    letter-spacing: -0.3px !important; border: none !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important; transition: transform 0.1s, box-shadow 0.1s !important;
    touch-action: manipulation !important; -webkit-tap-highlight-color: transparent !important; user-select: none !important;
}}
div.stButton > button:active {{ transform: scale(0.97) !important; box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important; }}

div[data-testid="column"]:nth-child(1) div.stButton > button, .btn-pee button {{ background: linear-gradient(135deg,#22c55e,#16a34a) !important; color:white !important; }}
div[data-testid="column"]:nth-child(2) div.stButton > button, .btn-poo button {{ background: linear-gradient(135deg,#f97316,#ea580c) !important; color:white !important; }}

input[type="text"], input[type="password"], .stTextInput input, .stTextArea textarea {{ font-size: 16px !important; }}

/* 가로 나열 강제 CSS Flexbox */
.horizontal-metrics {{
    display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px;
}}
.metric-box {{
    flex: 1; background: #ffffff; border-radius: 16px; padding: 12px 5px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; border: 1px solid #f1f5f9;
}}
.metric-label {{ font-size: 0.8rem; font-weight: 700; color: #64748b; margin-bottom: 4px; }}
.metric-value {{ font-size: 1.8rem; font-weight: 900; color: #0f172a; line-height: 1.1; }}

.section-header {{
    font-size: 0.85rem; font-weight: 800; color: {DYNAMIC_HDR_COLOR};
    letter-spacing: 1.5px; text-transform: uppercase; margin: 20px 0 10px 2px;
}}

.health-row {{
    display: flex; justify-content: space-between; align-items: center;
    background: #f8fafc; padding: 10px 15px; border-radius: 12px; margin-bottom: 8px;
    border: 1px solid #e2e8f0;
}}
.last-date {{ font-size: 0.75rem; color: #64748b; font-weight: 600; }}

.stTabs [data-baseweb="tab"] {{ height: 2.6rem !important; font-weight: 700 !important; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 2px !important; }}
hr {{ margin: 12px 0 !important; }}
.streamlit-expanderHeader {{ font-weight: 700 !important; font-size: 0.95rem !important; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 사이드바 (정보 수정 및 UI 설정)
# ==========================================
with st.sidebar:
    st.markdown(f"### ⚙️ {username}님")
    if st.button("🔒 로그아웃", use_container_width=True):
        cookie_manager.delete("saved_username")
        st.session_state.force_logout = True
        st.session_state.logged_in = False
        st.session_state.username = ""
        for k in ['pet_logs', 'profile', 'settings']:
            if k in st.session_state: del st.session_state[k]
        time.sleep(0.3); st.rerun()
    
    st.caption(f"📌 버전: {APP_VERSION} (업데이트: {UPDATE_DATE})")
    st.divider()
    
    with st.expander("🎨 UI 및 화면 순서 설정", expanded=False):
        new_btn_h = st.slider("버튼 높이 (rem)", 3.0, 6.0, float(st.session_state.settings.get('btn_h', 4.2)), 0.1)
        new_hdr_c = st.color_picker("섹션 헤더 색상", st.session_state.settings.get('hdr_color', '#94a3b8'))
        
        st.markdown("**화면 배치 순서 (낮은 숫자 우선)**")
        new_order = {}
        for k, v in st.session_state.settings.get('order', {}).items():
            new_order[k] = st.number_input(k, min_value=1, max_value=20, value=int(v), step=1)
            
        if st.button("설정 저장 및 적용", use_container_width=True, type="primary"):
            st.session_state.settings['btn_h'] = new_btn_h
            st.session_state.settings['hdr_color'] = new_hdr_c
            st.session_state.settings['order'] = new_order
            save_settings(st.session_state.settings)
            st.success("✅ UI 설정이 반영되었습니다!")
            time.sleep(0.5); st.rerun()

    with st.expander("📝 반려견 정보 수정"):
        p_name   = st.text_input("🐶 이름",    value=st.session_state.profile.get('pet_name',''))
        p_birth  = st.text_input("🎂 생년월일", value=st.session_state.profile.get('birth',''))
        p_weight = st.text_input("⚖️ 몸무게",  value=st.session_state.profile.get('weight',''))
        gender_options = ["수컷","암컷","중성화 수컷","중성화 암컷","기타"]
        curr_g = st.session_state.profile.get('gender','수컷')
        p_gender = st.selectbox("🐾 성별", gender_options, index=gender_options.index(curr_g) if curr_g in gender_options else 0)
        p_memo = st.text_area("🗒️ 기타", value=st.session_state.profile.get('memo',''), height=80)
        if st.button("☁️ 정보 저장", use_container_width=True):
            st.session_state.profile.update({"pet_name":p_name,"birth":p_birth, "weight":p_weight,"gender":p_gender,"memo":p_memo})
            save_profile(st.session_state.profile)
            st.success("✅ 저장 완료!")
            st.rerun()

# ==========================================
# 📊 데이터 준비 (헬퍼 함수)
# ==========================================
t_date = now_kst().strftime("%Y-%m-%d")
df = st.session_state.pet_logs
target_df = df[df['시간'].astype(str).str.startswith(t_date, na=False)].copy() if not df.empty else pd.DataFrame(columns=["시간","활동"])
last_upload_time = str(df.iloc[-1]['시간']) if not df.empty else "없음"

def get_iso(act_keyword, check_df):
    if check_df.empty: return ""
    for i in range(len(check_df)-1, -1, -1):
        act = str(check_df.iloc[i]['활동'])
        t   = str(check_df.iloc[i]['시간']).split('.')[0]
        if '차감' in act: continue
        if act_keyword in act:
            if '끄기' in act or '리셋' in act: return ""
            return t.replace(" ","T") + "+09:00"
    return ""

def get_real_count(keyword, check_df):
    if check_df.empty: return 0
    plus, minus = 0, 0
    for act in check_df['활동'].astype(str):
        if keyword in act:
            if '차감' in act: minus += 1
            elif any(x in act for x in ['리셋','끄기','통계제외']): pass
            else: plus += 1
    return max(0, plus - minus)

p_iso = get_iso("소변", target_df)
d_iso = get_iso("대변", target_df)
p_time_str = p_iso[11:16] if p_iso else "--:--"
d_time_str = d_iso[11:16] if d_iso else "--:--"

# 마지막 날짜 추출 (통합 키워드 지원)
def get_last_date(keyword):
    if df.empty: return "기록 없음"
    matches = df[df['활동'].str.contains(keyword, na=False)]
    if matches.empty: return "기록 없음"
    return matches.iloc[-1]['시간'][:10]

# ==========================================
# 🧱 UI 컴포넌트 모듈 (CDUI 렌더링용)
# ==========================================
def render_timer():
    components.html(f"""
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-family:sans-serif; margin-bottom:4px;">
        <div style="background:linear-gradient(160deg,#dcfce7,#bbf7d0); border-radius:20px; padding:16px 10px; text-align:center; box-shadow:0 4px 15px rgba(34,197,94,0.25); border: 2px solid #86efac;">
            <div style="font-size:0.8rem; font-weight:900; color:#15803d; letter-spacing:0.5px;">💧 소변 경과</div>
            <div id="p_tm" style="font-size:2.6rem; font-weight:900; color:#14532d; letter-spacing:2px; line-height:1.1; margin:6px 0;">--:--</div>
            <div style="background:rgba(255,255,255,0.6); border-radius:8px; padding:3px 6px; font-size:0.72rem; font-weight:800; color:#166534;">마지막 {p_time_str}</div>
        </div>
        <div style="background:linear-gradient(160deg,#fff7ed,#fed7aa); border-radius:20px; padding:16px 10px; text-align:center; box-shadow:0 4px 15px rgba(249,115,22,0.25); border: 2px solid #fdba74;">
            <div style="font-size:0.8rem; font-weight:900; color:#c2410c; letter-spacing:0.5px;">💩 대변 경과</div>
            <div id="d_tm" style="font-size:2.6rem; font-weight:900; color:#7c2d12; letter-spacing:2px; line-height:1.1; margin:6px 0;">--:--</div>
            <div style="background:rgba(255,255,255,0.6); border-radius:8px; padding:3px 6px; font-size:0.72rem; font-weight:800; color:#9a3412;">마지막 {d_time_str}</div>
        </div>
    </div>
    <script>
        function upP(){{ const el=document.getElementById('p_tm'), iso="{p_iso}"; if(!iso){{el.innerText="--:--";return;}} const diff=new Date()-new Date(iso); if(diff<0)return; const m=Math.floor(diff/60000); el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0'); }}
        function upD(){{ const el=document.getElementById('d_tm'), iso="{d_iso}"; if(!iso){{el.innerText="--:--";return;}} const diff=new Date()-new Date(iso); if(diff<0)return; const m=Math.floor(diff/60000); el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0'); }}
        setInterval(()=>{{upP();upD();}},1000); upP(); upD();
    </script>
    """, height=145)

def render_summary():
    st.markdown("<div class='section-header'>📈 오늘의 누적 데이터 현황</div>", unsafe_allow_html=True)
    # 🚨 강제 가로 나열을 위한 Custom HTML 적용 (모바일 화면 깨짐 완벽 방지)
    p_cnt = get_real_count('소변', target_df)
    d_cnt = get_real_count('대변', target_df)
    w_cnt = get_real_count('산책', target_df)
    
    st.markdown(f"""
    <div class="horizontal-metrics">
        <div class="metric-box">
            <div class="metric-label">💧 소변</div>
            <div class="metric-value">{p_cnt}회</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">💩 대변</div>
            <div class="metric-value">{d_cnt}회</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">🦮 산책</div>
            <div class="metric-value">{w_cnt}회</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_poo_pee():
    st.markdown("<div class='section-header'>🚨 배변 기록</div>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💧 집에서\n소변", use_container_width=True): add_record("💦 집에서 소변")
    with b2:
        if st.button("💩 집에서\n대변", use_container_width=True): add_record("💩 집에서 대변")

def render_walk():
    st.markdown("<div class='section-header'>🌳 산책 기록</div>", unsafe_allow_html=True)
    w1, w2 = st.columns(2)
    with w1:
        if st.button("🦮 일반 산책", use_container_width=True): add_record("🦮 일반 산책")
    with w2:
        if st.button("🦮+💧 산책소변", use_container_width=True): add_record("🦮+💦 산책 중 소변")
    w3, w4 = st.columns(2)
    with w3:
        if st.button("🦮+💩 산책대변", use_container_width=True): add_record("🦮+💩 산책 중 대변")
    with w4:
        if st.button("🦮+💧+💩\n모두 해결", use_container_width=True): add_record("🦮+💦+💩 산책 중 소변과 대변")

def render_health_beauty():
    st.markdown("<div class='section-header'>🏥 건강 / 미용 관리</div>", unsafe_allow_html=True)
    
    # 마지막 날짜 파싱 (통합 키워드)
    last_med_hosp = get_last_date("🏥 병원/약")
    last_groom = get_last_date("✂️ 미용")

    with st.expander("✨ 상세 기록 관리 (약/병원/미용 메모)", expanded=False):
        current_time_str = now_kst().strftime("%H:%M:%S.%f")

        # 1. 통합 약 복용 / 병원 방문 (메모 입력 포함)
        st.markdown(f"<div class='health-row'><span>🏥 약 복용 / 병원 방문</span><span class='last-date'>최근: {last_med_hosp}</span></div>", unsafe_allow_html=True)
        col1_1, col1_2 = st.columns([1, 1.5])
        with col1_1:
            d_mh = st.date_input("날짜", value=datetime.strptime(last_med_hosp, "%Y-%m-%d").date() if last_med_hosp != "기록 없음" else now_kst().date(), key="d_mh")
        with col1_2:
            txt_mh = st.text_input("내용 (예: 심장사상충, 접종)", key="t_mh", placeholder="음성/키보드 입력")
        
        if st.button("🏥 병원/약 기록 저장 💾", key="b_mh", use_container_width=True):
            activity_text = f"🏥 병원/약: {txt_mh}" if txt_mh.strip() else "🏥 병원/약 (내용없음)"
            add_record(activity_text, f"{d_mh} {current_time_str}")

        st.markdown("<hr style='margin: 15px 0 10px 0;'>", unsafe_allow_html=True)

        # 2. 미용/목욕 (메모 입력 포함)
        st.markdown(f"<div class='health-row'><span>✂️ 미용 / 목욕 기록</span><span class='last-date'>최근: {last_groom}</span></div>", unsafe_allow_html=True)
        col2_1, col2_2 = st.columns([1, 1.5])
        with col2_1:
            d_groom = st.date_input("날짜", value=datetime.strptime(last_groom, "%Y-%m-%d").date() if last_groom != "기록 없음" else now_kst().date(), key="d_groom")
        with col2_2:
            txt_groom = st.text_input("내용 (예: 전체미용, 발톱)", key="t_groom", placeholder="음성/키보드 입력")
            
        if st.button("✂️ 미용/목욕 기록 저장 💾", key="b_groom", use_container_width=True):
            activity_text = f"✂️ 미용: {txt_groom}" if txt_groom.strip() else "✂️ 미용 및 목욕"
            add_record(activity_text, f"{d_groom} {current_time_str}")

def render_manual():
    with st.expander("⚙️ 타이머 수동 조절 / 리셋"):
        t1, t2 = st.tabs(["💧 소변", "💩 대변"])
        with t1:
            tw1, tk1 = st.tabs(["⏱️ 휠", "⌨️ 키보드"])
            with tw1:
                p_wheel = st.time_input("시간 선택", now_kst().time(), key="p_wheel")
                if st.button("소변 시간 수정", key="bp_w", use_container_width=True): add_record("💦 소변(수정) (통계제외)", f"{t_date} {p_wheel.strftime('%H:%M:%S')}")
            with tk1:
                p_txt = st.text_input("시간 입력 (HH:MM)", value=now_kst().strftime("%H:%M"), key="p_txt")
                if st.button("소변 시간 수정", key="bp_k", use_container_width=True):
                    try: add_record("💦 소변(수정) (통계제외)", f"{t_date} {datetime.strptime(p_txt, '%H:%M').strftime('%H:%M:00')}")
                    except: st.error("HH:MM 형식!")
            if st.button("🔄 소변 타이머 리셋", use_container_width=True, key="bp_r", type="secondary"): add_record("💦 소변 리셋 (통계제외)")
        with t2:
            tw2, tk2 = st.tabs(["⏱️ 휠", "⌨️ 키보드"])
            with tw2:
                d_wheel = st.time_input("시간 선택", now_kst().time(), key="d_wheel")
                if st.button("대변 시간 수정", key="bd_w", use_container_width=True): add_record("💩 대변(수정) (통계제외)", f"{t_date} {d_wheel.strftime('%H:%M:%S')}")
            with tk2:
                d_txt = st.text_input("시간 입력 (HH:MM)", value=now_kst().strftime("%H:%M"), key="d_txt")
                if st.button("대변 시간 수정", key="bd_k", use_container_width=True):
                    try: add_record("💩 대변(수정) (통계제외)", f"{t_date} {datetime.strptime(d_txt, '%H:%M').strftime('%H:%M:00')}")
                    except: st.error("HH:MM 형식!")
            if st.button("🔄 대변 타이머 리셋", use_container_width=True, key="bd_r", type="secondary"): add_record("💩 대변 리셋 (통계제외)")

def render_deduct():
    with st.expander("➖ 잘못 누른 기록 차감"):
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("💧 소변\n-1", use_container_width=True): add_record("💦 소변 차감 (-1)")
        with a2:
            if st.button("💩 대변\n-1", use_container_width=True): add_record("💩 대변 차감 (-1)")
        with a3:
            if st.button("🦮 산책\n-1", use_container_width=True): add_record("🦮 산책 차감 (-1)")

def render_log():
    with st.expander(f"📋 오늘 활동 로그 ({len(target_df)}건)"):
        if target_df.empty: st.info("오늘의 기록이 없습니다.")
        else:
            log_display = target_df.copy()
            log_display['시간'] = log_display['시간'].astype(str).str[11:19]
            log_display = log_display.sort_values('시간', ascending=False).reset_index(drop=True)
            log_display.index += 1
            st.dataframe(log_display, use_container_width=True, column_config={"시간": st.column_config.TextColumn("🕐 시간", width="small"), "활동": st.column_config.TextColumn("📝 활동")})

def render_stats():
    with st.expander("📊 주간 배변 통계"):
        if df.empty: st.info("데이터가 없습니다.")
        else:
            week_dates = [(now_kst() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            week_data = [{"날짜": d[5:], "소변": get_real_count('소변', df[df['시간'].astype(str).str.startswith(d, na=False)]), "대변": get_real_count('대변', df[df['시간'].astype(str).str.startswith(d, na=False)]), "산책": get_real_count('산책', df[df['시간'].astype(str).str.startswith(d, na=False)])} for d in week_dates]
            wdf = pd.DataFrame(week_data).set_index("날짜")
            st.bar_chart(wdf, color=["#22c55e","#f97316","#3b82f6"])
            st.caption("최근 7일 소변(녹)/대변(주)/산책(청)")
            st.dataframe(pd.DataFrame(wdf.sum().rename("7일 합계")).T, use_container_width=True)

# ==========================================
# 🏠 메인 화면 시작 (설정 기반 동적 렌더링)
# ==========================================
pet_n = st.session_state.profile.get('pet_name','강아지')

st.markdown(f"""
<div class="header-card">
    <div>
        <div style="font-size:1.4rem; font-weight:900;">🐾 {pet_n} 센터</div>
        <div style="font-size:0.8rem; opacity:0.9; margin-top:2px;">{now_kst().strftime("%m월 %d일 (%a) %H:%M")}</div>
    </div>
    <div style="text-align:right; font-size:0.75rem; opacity:0.8;">
        <div>☁️ {last_upload_time[5:19] if last_upload_time != '없음' else '없음'}</div>
        <div style="margin-top:4px;">{APP_VERSION} ({UPDATE_DATE[5:]})</div>
    </div>
</div>
""", unsafe_allow_html=True)

ui_order = st.session_state.settings.get('order', {})
sorted_modules = sorted(ui_order.items(), key=lambda x: int(x[1]))

for mod_name, _ in sorted_modules:
    if mod_name == "타이머": render_timer()
    elif mod_name == "누적데이터": render_summary()
    elif mod_name == "배변기록": render_poo_pee()
    elif mod_name == "산책기록": render_walk()
    elif mod_name in ["건강미용", "식사건강"]: render_health_beauty()
    elif mod_name == "수동조절": render_manual()
    elif mod_name == "기록차감": render_deduct()
    elif mod_name == "활동로그": render_log()
    elif mod_name == "주간통계": render_stats()

# ==========================================
# ❌ 직전 기록 취소
# ==========================================
st.divider()
if not target_df.empty:
    last_act = str(target_df.iloc[-1]['활동'])
    last_t   = str(target_df.iloc[-1]['시간'])[11:19]
    if st.button(f"❌ 직전 취소: [{last_t}] {last_act}", use_container_width=True):
        last_idx  = target_df.index[-1]
        last_time = target_df.loc[last_idx, '시간']
        try:
            requests.delete(f"{FIREBASE_URL}users/{username}/logs/{last_time}.json", timeout=5)
            st.session_state.pet_logs = st.session_state.pet_logs.drop(index=last_idx).reset_index(drop=True)
            st.rerun()
        except:
            st.error("⚠️ 삭제 실패")

# --- 꼬리말 ---
st.markdown(f"""
<div style="text-align:center; color:#94a3b8; font-size:0.75rem; padding:10px 0 20px;">
    🐾 Smart Pet Care Center<br>
    현재 버전: <strong>{APP_VERSION}</strong> | 📅 업데이트: {UPDATE_DATE}<br>
    ☁️ CDUI Render Engine Active
</div>
""", unsafe_allow_html=True)

# END

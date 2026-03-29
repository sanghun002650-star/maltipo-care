
# *********************************************************************
# 🐾 스마트 관제 센터 (Smart Pet Care Center)
# * 현재 버전   : v12.1.0 (스마트폰 UI 전면 재설계)
# *   - 모바일 퍼스트 디자인: 큰 버튼, 선명한 색상, 한눈에 파악
# *   - 핵심 버튼 최상단 배치 (엄지손가락 존)
# *   - 상태 카드 대형화 (소변/대변 경과시간)
# *   - 섹션별 색상 코딩 (녹색=소변, 주황=대변, 파랑=산책, 보라=식사)
# *   - 신규: 식사/간식/약 기록, 오늘 로그, 주간 통계
# *   - 버그수정: 타임스탬프 충돌, 삭제 인덱스, Firebase 에러처리
# *********************************************************************
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import requests
import extra_streamlit_components as stx
import time
import random
import string
# ==========================================
# 0. 기본 설정
# ==========================================
APP_VERSION = "v12.1.0 (스마트폰 최적화)"
KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)
FIREBASE_URL = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/"
st.set_page_config(page_title="🐾 관제 센터", layout="centered", page_icon="🐾",
                   initial_sidebar_state="collapsed")
st.markdown("""
<style>
/* =============================================
   모바일 퍼스트 글로벌 스타일
   ============================================= */
/* 전체 여백 최소화 */
.block-container {
    padding: 0.5rem 0.75rem 6rem 0.75rem !important;
    max-width: 480px !important;
}
/* 스크롤바 숨기기 */
::-webkit-scrollbar { width: 0px; }
/* =============================================
   버튼 - 엄지 친화 대형 디자인
   ============================================= */
div.stButton > button {
    height: 4.2rem !important;
    border-radius: 16px !important;
    font-weight: 900 !important;
    font-size: 1.05rem !important;
    letter-spacing: -0.3px !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
    transition: transform 0.1s, box-shadow 0.1s !important;
    touch-action: manipulation !important;
    -webkit-tap-highlight-color: transparent !important;
    user-select: none !important;
}
div.stButton > button:active {
    transform: scale(0.97) !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
}
/* 소변 버튼 - 초록 */
div[data-testid="column"]:nth-child(1) div.stButton > button,
.btn-pee button { background: linear-gradient(135deg,#22c55e,#16a34a) !important; color:white !important; }
/* 대변 버튼 - 주황 */
div[data-testid="column"]:nth-child(2) div.stButton > button,
.btn-poo button { background: linear-gradient(135deg,#f97316,#ea580c) !important; color:white !important; }
/* =============================================
   입력창 - iOS 줌 방지
   ============================================= */
input[type="text"], input[type="password"],
.stTextInput input, .stTextArea textarea { font-size: 16px !important; }
/* =============================================
   메트릭 카드 - 대형 숫자
   ============================================= */
div[data-testid="metric-container"] {
    background: #ffffff;
    border-radius: 16px;
    padding: 12px 8px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    text-align: center;
    border: none !important;
}
div[data-testid="metric-container"] label {
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    color: #64748b !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] > div {
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    color: #0f172a !important;
    line-height: 1.1 !important;
}
/* =============================================
   컬럼 레이아웃
   ============================================= */
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] {
        gap: 8px !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        min-width: 0 !important;
        flex: 1 !important;
    }
}
/* =============================================
   섹션 헤더
   ============================================= */
.section-header {
    font-size: 0.8rem;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin: 18px 0 8px 2px;
}
/* 탭 */
.stTabs [data-baseweb="tab"] { height: 2.6rem !important; font-weight: 700 !important; }
.stTabs [data-baseweb="tab-list"] { gap: 2px !important; }
/* divider 간격 */
hr { margin: 12px 0 !important; }
/* expander */
.streamlit-expanderHeader { font-weight: 700 !important; font-size: 0.95rem !important; }
</style>
""", unsafe_allow_html=True)
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
                            cookie_manager.set("saved_username", login_id,
                                               expires_at=datetime.now() + timedelta(days=180))
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
                        st.success("✅ 계정 생성 완료! 로그인 탭에서 접속하세요.")
                except requests.exceptions.RequestException:
                    st.error("⚠️ 네트워크 오류.")
            else:
                st.warning("모든 항목을 입력하세요.")
    st.stop()
# ==========================================
# ☁️ 클라우드 엔진
# ==========================================
username = st.session_state.username
def _unique_ts(base_time=None):
    """마이크로초 기반 유니크 타임스탬프 - 충돌 원천 차단"""
    t = base_time if base_time else now_kst()
    return t.strftime("%Y-%m-%d %H:%M:%S.%f")  # 마이크로초 6자리 포함
def load_profile():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/profile.json", timeout=5)
        if res.status_code == 200 and res.json():
            return res.json()
    except: pass
    return {"pet_name": "강아지", "birth": "", "weight": "", "gender": "수컷", "memo": ""}
def save_profile(profile):
    try:
        requests.put(f"{FIREBASE_URL}users/{username}/profile.json", json=profile, timeout=5)
    except:
        st.error("⚠️ 저장 실패")
def load_data():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/logs.json", timeout=5)
        if res.status_code == 200 and res.json():
            records = [{"시간": k, "활동": v} for k, v in res.json().items()]
            return pd.DataFrame(records).sort_values("시간").reset_index(drop=True)
    except:
        st.warning("⚠️ 데이터 로드 실패")
    return pd.DataFrame(columns=["시간", "활동"])
def add_record(act, c_time=None):
    t = c_time if c_time else _unique_ts()
    try:
        requests.patch(f"{FIREBASE_URL}users/{username}/logs.json", json={t: act}, timeout=5)
    except:
        st.error("⚠️ 기록 저장 실패"); return
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, new_row], ignore_index=True)
    st.rerun()
if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()
t_date = now_kst().strftime("%Y-%m-%d")
df = st.session_state.pet_logs
target_df = df[df['시간'].astype(str).str.startswith(t_date, na=False)].copy() if not df.empty else pd.DataFrame(columns=["시간","활동"])
last_upload_time = str(df.iloc[-1]['시간']) if not df.empty else "없음"
# ==========================================
# ⚙️ 사이드바
# ==========================================
with st.sidebar:
    st.markdown(f"### ⚙️ {username}님")
    if st.button("🔒 로그아웃", use_container_width=True):
        cookie_manager.delete("saved_username")
        st.session_state.force_logout = True
        st.session_state.logged_in = False
        st.session_state.username = ""
        for k in ['pet_logs', 'profile']:
            if k in st.session_state: del st.session_state[k]
        time.sleep(0.3); st.rerun()
    st.caption(f"버전: {APP_VERSION}")
    st.divider()
    with st.expander("📝 반려견 정보 수정"):
        p_name   = st.text_input("🐶 이름",    value=st.session_state.profile.get('pet_name',''))
        p_birth  = st.text_input("🎂 생년월일", value=st.session_state.profile.get('birth',''))
        p_weight = st.text_input("⚖️ 몸무게",  value=st.session_state.profile.get('weight',''))
        gender_options = ["수컷","암컷","중성화 수컷","중성화 암컷","기타"]
        curr_g = st.session_state.profile.get('gender','수컷')
        p_gender = st.selectbox("🐾 성별", gender_options,
                                index=gender_options.index(curr_g) if curr_g in gender_options else 0)
        p_memo = st.text_area("🗒️ 기타", value=st.session_state.profile.get('memo',''), height=80)
        if st.button("☁️ 저장", use_container_width=True, type="primary"):
            st.session_state.profile.update({"pet_name":p_name,"birth":p_birth,
                                              "weight":p_weight,"gender":p_gender,"memo":p_memo})
            save_profile(st.session_state.profile)
            st.success("✅ 저장 완료!")
            st.rerun()
# ==========================================
# 📊 헬퍼 함수
# ==========================================
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
# ==========================================
# 🏠 메인 화면 시작
# ==========================================
pet_n = st.session_state.profile.get('pet_name','강아지')
# --- 상단 헤더 바 ---
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center;
            background:linear-gradient(135deg,#667eea,#764ba2);
            border-radius:16px; padding:12px 16px; margin-bottom:12px; color:white;">
    <div>
        <div style="font-size:1.3rem; font-weight:900;">🐾 {pet_n}</div>
        <div style="font-size:0.75rem; opacity:0.85; margin-top:1px;">{now_kst().strftime("%m월 %d일 (%a) %H:%M")}</div>
    </div>
    <div style="text-align:right; font-size:0.7rem; opacity:0.8;">
        <div>☁️ {last_upload_time[5:19] if last_upload_time != '없음' else '없음'}</div>
        <div style="margin-top:2px;">{APP_VERSION}</div>
    </div>
</div>
""", unsafe_allow_html=True)
# ==========================================
# ⏱️ 배변 타이머 카드 (대형)
# ==========================================
components.html(f"""
<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-family:sans-serif; margin-bottom:4px;">
    <!-- 소변 카드 -->
    <div style="background:linear-gradient(160deg,#dcfce7,#bbf7d0); border-radius:20px;
                padding:16px 10px; text-align:center; box-shadow:0 4px 15px rgba(34,197,94,0.25);
                border: 2px solid #86efac;">
        <div style="font-size:0.8rem; font-weight:900; color:#15803d; letter-spacing:0.5px;">💧 소변 경과</div>
        <div id="p_tm" style="font-size:2.6rem; font-weight:900; color:#14532d;
                               letter-spacing:2px; line-height:1.1; margin:6px 0;">--:--</div>
        <div style="background:rgba(255,255,255,0.6); border-radius:8px; padding:3px 6px;
                    font-size:0.72rem; font-weight:800; color:#166534;">
            마지막 {p_time_str}
        </div>
    </div>
    <!-- 대변 카드 -->
    <div style="background:linear-gradient(160deg,#fff7ed,#fed7aa); border-radius:20px;
                padding:16px 10px; text-align:center; box-shadow:0 4px 15px rgba(249,115,22,0.25);
                border: 2px solid #fdba74;">
        <div style="font-size:0.8rem; font-weight:900; color:#c2410c; letter-spacing:0.5px;">💩 대변 경과</div>
        <div id="d_tm" style="font-size:2.6rem; font-weight:900; color:#7c2d12;
                               letter-spacing:2px; line-height:1.1; margin:6px 0;">--:--</div>
        <div style="background:rgba(255,255,255,0.6); border-radius:8px; padding:3px 6px;
                    font-size:0.72rem; font-weight:800; color:#9a3412;">
            마지막 {d_time_str}
        </div>
    </div>
</div>
<script>
    function upP(){{
        const el=document.getElementById('p_tm'), iso="{p_iso}";
        if(!iso){{el.innerText="--:--";return;}}
        const diff=new Date()-new Date(iso); if(diff<0)return;
        const m=Math.floor(diff/60000);
        el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0');
    }}
    function upD(){{
        const el=document.getElementById('d_tm'), iso="{d_iso}";
        if(!iso){{el.innerText="--:--";return;}}
        const diff=new Date()-new Date(iso); if(diff<0)return;
        const m=Math.floor(diff/60000);
        el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0');
    }}
    setInterval(()=>{{upP();upD();}},1000); upP(); upD();
</script>
""", height=145)
# ==========================================
# 🔢 오늘의 누적 데이터 현황 (가로 배치)
# ==========================================
p_cnt = get_real_count('소변', target_df)
d_cnt = get_real_count('대변', target_df)
w_cnt = get_real_count('산책', target_df)
f_cnt = get_real_count('식사', target_df)
st.markdown("<div class='section-header'>📈 오늘의 누적 데이터 현황</div>", unsafe_allow_html=True)
mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("💧 소변", f"{p_cnt}회")
mc2.metric("💩 대변", f"{d_cnt}회")
mc3.metric("🦮 산책", f"{w_cnt}회")
mc4.metric("🍚 식사", f"{f_cnt}회")
# ==========================================
# 🔘 핵심 액션 버튼 (배변)
# ==========================================
st.markdown("<div class='section-header'>🚨 배변 기록</div>", unsafe_allow_html=True)
b1, b2 = st.columns(2)
with b1:
    if st.button("💧 집에서\n소변", use_container_width=True): add_record("💦 집에서 소변")
with b2:
    if st.button("💩 집에서\n대변", use_container_width=True): add_record("💩 집에서 대변")
# ==========================================
# 🌳 산책 버튼
# ==========================================
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
# ==========================================
# 🍽️ 식사/건강 버튼
# ==========================================
st.markdown("<div class='section-header'>🍽️ 식사 / 건강</div>", unsafe_allow_html=True)
f1, f2 = st.columns(2)
with f1:
    if st.button("🍚 아침 식사", use_container_width=True): add_record("🍚 아침 식사")
    if st.button("🍚 저녁 식사", use_container_width=True): add_record("🍚 저녁 식사")
    if st.button("💊 약 복용", use_container_width=True): add_record("💊 약 복용")
with f2:
    if st.button("🍚 점심 식사", use_container_width=True): add_record("🍚 점심 식사")
    if st.button("🦴 간식 제공", use_container_width=True): add_record("🦴 간식 제공")
    if st.button("💉 병원/미용", use_container_width=True): add_record("💉 병원/미용 방문")
# ==========================================
# ⚙️ 수동 조절 (접기)
# ==========================================
with st.expander("⚙️ 타이머 수동 조절 / 리셋"):
    t1, t2 = st.tabs(["💧 소변", "💩 대변"])
    with t1:
        tw1, tk1 = st.tabs(["⏱️ 휠", "⌨️ 키보드"])
        with tw1:
            p_wheel = st.time_input("시간 선택", now_kst().time(), key="p_wheel")
            if st.button("소변 시간 수정", key="bp_w", use_container_width=True):
                add_record("💦 소변(수정) (통계제외)", f"{t_date} {p_wheel.strftime('%H:%M:%S')}")
        with tk1:
            p_txt = st.text_input("시간 입력 (HH:MM)", value=now_kst().strftime("%H:%M"), key="p_txt")
            if st.button("소변 시간 수정", key="bp_k", use_container_width=True):
                try:
                    vt = datetime.strptime(p_txt, "%H:%M").strftime("%H:%M:00")
                    add_record("💦 소변(수정) (통계제외)", f"{t_date} {vt}")
                except: st.error("HH:MM 형식!")
        if st.button("🔄 소변 타이머 리셋", use_container_width=True, key="bp_r", type="secondary"):
            add_record("💦 소변 리셋 (통계제외)")
    with t2:
        tw2, tk2 = st.tabs(["⏱️ 휠", "⌨️ 키보드"])
        with tw2:
            d_wheel = st.time_input("시간 선택", now_kst().time(), key="d_wheel")
            if st.button("대변 시간 수정", key="bd_w", use_container_width=True):
                add_record("💩 대변(수정) (통계제외)", f"{t_date} {d_wheel.strftime('%H:%M:%S')}")
        with tk2:
            d_txt = st.text_input("시간 입력 (HH:MM)", value=now_kst().strftime("%H:%M"), key="d_txt")
            if st.button("대변 시간 수정", key="bd_k", use_container_width=True):
                try:
                    vt = datetime.strptime(d_txt, "%H:%M").strftime("%H:%M:00")
                    add_record("💩 대변(수정) (통계제외)", f"{t_date} {vt}")
                except: st.error("HH:MM 형식!")
        if st.button("🔄 대변 타이머 리셋", use_container_width=True, key="bd_r", type="secondary"):
            add_record("💩 대변 리셋 (통계제외)")
# ==========================================
# ➖ 차감 (접기)
# ==========================================
with st.expander("➖ 잘못 누른 기록 차감"):
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("💧 소변\n-1", use_container_width=True): add_record("💦 소변 차감 (-1)")
    with a2:
        if st.button("💩 대변\n-1", use_container_width=True): add_record("💩 대변 차감 (-1)")
    with a3:
        if st.button("🦮 산책\n-1", use_container_width=True): add_record("🦮 산책 차감 (-1)")
# ==========================================
# 📋 오늘의 활동 로그 (접기)
# ==========================================
with st.expander(f"📋 오늘 활동 로그 ({len(target_df)}건)"):
    if target_df.empty:
        st.info("오늘의 기록이 없습니다.")
    else:
        log_display = target_df.copy()
        log_display['시간'] = log_display['시간'].astype(str).str[11:19]
        log_display = log_display.sort_values('시간', ascending=False).reset_index(drop=True)
        log_display.index += 1
        st.dataframe(log_display, use_container_width=True,
                     column_config={"시간": st.column_config.TextColumn("🕐 시간", width="small"),
                                    "활동": st.column_config.TextColumn("📝 활동")})
# ==========================================
# 📊 주간 통계 (접기)
# ==========================================
with st.expander("📊 주간 배변 통계"):
    if df.empty:
        st.info("데이터가 없습니다.")
    else:
        week_dates = [(now_kst() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        week_data = []
        for d in week_dates:
            day_df = df[df['시간'].astype(str).str.startswith(d, na=False)]
            week_data.append({
                "날짜": d[5:],
                "소변": get_real_count('소변', day_df),
                "대변": get_real_count('대변', day_df),
                "산책": get_real_count('산책', day_df),
            })
        wdf = pd.DataFrame(week_data).set_index("날짜")
        st.bar_chart(wdf, color=["#22c55e","#f97316","#3b82f6"])
        st.caption("최근 7일 소변(녹)/대변(주)/산책(청)")
        total = wdf.sum().rename("7일 합계")
        st.dataframe(pd.DataFrame(total).T, use_container_width=True)
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
    🐾 Smart Pet Care Center · {APP_VERSION}<br>
    ☁️ 마지막 저장: {last_upload_time[:19] if last_upload_time != '없음' else '없음'}
</div>
""", unsafe_allow_html=True)

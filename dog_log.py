# *********************************************************************
# 🐾 스마트 관제 센터 (Smart Pet Care Center)
# * 현재 버전   : v11.8 (Cloud Edition)
# * 코어 엔진   : Streamlit 기반 웹 대시보드 + Firebase 클라우드 직결
# * 주요 기능   : 다중 사용자 로그인(멀티 테넌트), v11.8 듀얼 수동조절, 실시간 배변 모니터링
# *********************************************************************

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import requests
import json

# ==========================================
# 0. 엔진 세팅 및 파이어베이스 클라우드 연결
# ==========================================
APP_VERSION = "v11.8 (Cloud & 멀티유저 에디션)"
KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)

# ★ 상훈님의 전용 파이어베이스 주소 (절대 변경 금지) ★
FIREBASE_URL = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/"

st.set_page_config(page_title="스마트 관제 센터", layout="centered", page_icon="🐾")

st.markdown("""
<style>
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; gap: 5px !important; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { flex: 1 1 48% !important; min-width: 48% !important; }
    }
    div.stButton > button { height: 3.5rem !important; border-radius: 12px !important; font-weight: 800 !important; }
    div[data-testid="metric-container"] { background-color: #ffffff; border: 2px solid #e2e8f0; border-radius: 12px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }
    div[data-testid="metric-container"] label { font-size: 1.1rem !important; font-weight: bold !important; color: #475569 !important; }
    div[data-testid="metric-container"] div { font-size: 2.2rem !important; font-weight: 900 !important; color: #0f172a !important; }
</style>
""", unsafe_allow_html=True)

# 세션(로그인 상태) 초기화
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""

# ==========================================
# 🚪 1. 중앙 현관문 (로그인 및 회원가입 로직)
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🐾 스마트 관제 센터</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>가족/친구 전용 클라우드 플랫폼 (v11.8 Cloud)</p>", unsafe_allow_html=True)
    st.divider()
    
    tab1, tab2 = st.tabs(["🔑 로그인", "📝 새 계정 만들기"])
    
    with tab1:
        st.subheader("로그인")
        login_id = st.text_input("아이디 (ID)", key="l_id")
        login_pw = st.text_input("비밀번호", type="password", key="l_pw")
        if st.button("접속하기 🚀", use_container_width=True, type="primary"):
            if login_id and login_pw:
                # 파이어베이스에서 비밀번호 확인
                res = requests.get(f"{FIREBASE_URL}users/{login_id}/password.json")
                if res.status_code == 200 and res.json() == login_pw:
                    st.session_state.logged_in = True
                    st.session_state.username = login_id
                    st.success(f"환영합니다, {login_id}님!")
                    st.rerun()
                else:
                    st.error("❌ 아이디가 없거나 비밀번호가 틀렸습니다.")
            else:
                st.warning("아이디와 비밀번호를 모두 입력하세요.")
                
    with tab2:
        st.subheader("새 계정 만들기")
        st.info("각자의 아이디를 만들면 데이터가 완벽하게 분리되어 저장됩니다.")
        reg_id = st.text_input("사용할 아이디 (ID)", key="r_id")
        reg_pw = st.text_input("비밀번호", type="password", key="r_pw")
        if st.button("계정 생성 💾", use_container_width=True):
            if reg_id and reg_pw:
                # 아이디 중복 확인
                res = requests.get(f"{FIREBASE_URL}users/{reg_id}.json")
                if res.status_code == 200 and res.json() is not None:
                    st.error("❌ 이미 존재하는 아이디입니다. 다른 아이디를 입력해주세요.")
                else:
                    # 파이어베이스에 새 유저 정보 생성
                    requests.put(f"{FIREBASE_URL}users/{reg_id}/password.json", json=reg_pw)
                    default_prof = {"pet_name": "강아지", "birth": "", "weight": "", "gender": "수컷", "memo": ""}
                    requests.put(f"{FIREBASE_URL}users/{reg_id}/profile.json", json=default_prof)
                    st.success("✅ 계정이 성공적으로 생성되었습니다! [로그인] 탭에서 접속해주세요.")
            else:
                st.warning("아이디와 비밀번호를 모두 입력하세요.")
    
    st.stop() # 로그인을 안 했으면 아래 메인 화면은 그리지 않고 여기서 정지!

# ==========================================
# ☁️ 2. 클라우드 통신 엔진 (v11.8 기능 이식)
# ==========================================
username = st.session_state.username

def load_profile():
    res = requests.get(f"{FIREBASE_URL}users/{username}/profile.json")
    if res.status_code == 200 and res.json(): return res.json()
    return {"pet_name": "강아지", "birth": "", "weight": "", "gender": "수컷", "memo": ""}

def save_profile(profile):
    requests.put(f"{FIREBASE_URL}users/{username}/profile.json", json=profile)

def load_data():
    res = requests.get(f"{FIREBASE_URL}users/{username}/logs.json")
    if res.status_code == 200 and res.json():
        data = res.json()
        # 파이어베이스 딕셔너리를 v11.8 판다스 데이터프레임으로 변환
        records = [{"시간": k, "활동": v} for k, v in data.items()]
        return pd.DataFrame(records).sort_values("시간").reset_index(drop=True)
    return pd.DataFrame(columns=["시간", "활동"])

def add_record(act, c_time=None):
    t = c_time if c_time else now_kst().strftime("%Y-%m-%d %H:%M:%S")
    # 파이어베이스에 기록 쏘기 (patch는 추가, put은 덮어쓰기)
    requests.patch(f"{FIREBASE_URL}users/{username}/logs.json", json={t: act})
    # 화면 갱신
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, new_row], ignore_index=True)
    st.rerun()

# 세션 데이터 로드 (클라우드에서 가져오기)
if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()

# 오늘 날짜 타겟 데이터만 필터링
t_date = now_kst().strftime("%Y-%m-%d")
df = st.session_state.pet_logs
if not df.empty and "시간" in df.columns:
    target_df = df[df['시간'].astype(str).str.startswith(t_date, na=False)]
else:
    target_df = pd.DataFrame(columns=["시간", "활동"])

last_upload_time = str(df.iloc[-1]['시간']) if not df.empty else "입력된 데이터 없음"

# ==========================================
# ⚙️ 3. 사이드바 (프로필 설정 & 로그아웃)
# ==========================================
st.sidebar.header(f"⚙️ {username}님의 설정")
if st.sidebar.button("🔒 로그아웃", type="secondary"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

st.sidebar.success(f"🚀 {APP_VERSION}")

with st.sidebar.expander("📝 반려견 기본 정보 설정", expanded=True):
    p_name = st.text_input("🐶 이름", value=st.session_state.profile['pet_name'])
    p_birth = st.text_input("🎂 생년월일 (예: 250101)", value=st.session_state.profile['birth'])
    p_weight = st.text_input("⚖️ 몸무게 (예: 5.2kg)", value=st.session_state.profile['weight'])
    
    gender_options = ["수컷", "암컷", "중성화 수컷", "중성화 암컷", "기타"]
    curr_gender = st.session_state.profile.get('gender', '수컷')
    g_idx = gender_options.index(curr_gender) if curr_gender in gender_options else 0
    p_gender = st.selectbox("🐾 성별", gender_options, index=g_idx)
    
    p_memo = st.text_area("🗒️ 기타사항 (건강상태 등)", value=st.session_state.profile['memo'], height=100)

    if st.button("☁️ 클라우드에 프로필 영구 저장", use_container_width=True, type="primary"):
        st.session_state.profile.update({
            "pet_name": p_name, "birth": p_birth, "weight": p_weight, "gender": p_gender, "memo": p_memo
        })
        save_profile(st.session_state.profile)
        st.success("✅ 클라우드 서버에 안전하게 저장되었습니다!")
        st.rerun()

# ==========================================
# 📊 4. 메인 대시보드 (v11.8 UI 완벽 유지)
# ==========================================
pet_n = st.session_state.profile['pet_name']
st.markdown(f"<div style='text-align:center; font-size: 1.6rem; font-weight: 900; color:#333; padding-bottom: 5px;'>📊 {pet_n} 관제 센터 (Cloud)</div>", unsafe_allow_html=True)

clock_weather_html = """
<div style="background-color: #f1f5f9; border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 20px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); font-family: sans-serif;">
    <div id="live_clock" style="font-size: 1.1rem; font-weight: 900; color: #1e293b; letter-spacing: 0.5px;"></div>
    <div id="weather_info" style="font-size: 0.85rem; font-weight: bold; color: #475569; margin-top: 5px;">기상 데이터 연결 중... ⏳</div>
</div>
<script>
    function updateClock() {
        const now = new Date();
        const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
        document.getElementById('live_clock').innerText = now.toLocaleString('ko-KR', options);
    }
    setInterval(updateClock, 1000); updateClock();

    async function updateWeather() {
        try {
            const res = await fetch('https://api.open-meteo.com/v1/forecast?latitude=35.8562&longitude=129.2247&current_weather=true&timezone=Asia%2FSeoul');
            const data = await res.json();
            const current = data.current_weather;
            const icon = current.is_day === 1 ? "☀️ 낮" : "🌙 밤";
            document.getElementById('weather_info').innerHTML = `${icon} ｜ 🌡️ 현재 온도: ${current.temperature}℃`;
        } catch(e) {
            const h = new Date().getHours();
            const icon = (h >= 6 && h < 18) ? "☀️ 낮" : "🌙 밤";
            document.getElementById('weather_info').innerHTML = `${icon} ｜ 🌡️ 연결 대기중...`;
        }
    }
    updateWeather(); setInterval(updateWeather, 1800000);
</script>
"""
components.html(clock_weather_html, height=85)

def get_iso(act_keyword, check_df):
    if check_df.empty: return ""
    for i in range(len(check_df)-1, -1, -1):
        act = str(check_df.iloc[i]['활동'])
        t = str(check_df.iloc[i]['시간'])
        if '차감' in act: continue 
        if act_keyword in act:
            if '끄기' in act or '리셋' in act: return ""
            return t.replace(" ", "T") + "+09:00"
    return ""

def get_real_count(keyword, check_df):
    if check_df.empty: return 0
    plus_count, minus_count = 0, 0
    for act in check_df['활동'].astype(str):
        if keyword in act:
            if '차감' in act: minus_count += 1
            elif any(x in act for x in ['리셋', '끄기', '통계제외']): pass 
            else: plus_count += 1
    return max(0, plus_count - minus_count)

p_iso = get_iso("소변", target_df)
d_iso = get_iso("대변", target_df)
p_time_str = p_iso[11:16] if p_iso else "--:--"
d_time_str = d_iso[11:16] if d_iso else "--:--"

st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color:#444; margin-bottom: 8px;'>💡 실시간 배변 모니터링</div>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    components.html(f"""
    <div style="border-radius:12px; border:2px solid #4CAF50; font-family:sans-serif; overflow:hidden;">
        <div style="background:#E8F5E9; padding: 12px 5px; text-align:center;">
            <div style="color:#2E7D32; font-weight:900; font-size: 0.85rem; margin-bottom:5px;">💧 소변 경과시간</div>
            <div style="font-size:2.0rem; font-weight:900; color:#1B5E20; letter-spacing: 1px;" id="p_tm">00:00</div>
        </div>
        <div style="background:#A5D6A7; padding: 6px; text-align:center; border-top: 2px solid #81C784;">
            <div style="color:#1B5E20; font-size: 0.75rem; font-weight:bold;">발생 시각 {p_time_str}</div>
        </div>
    </div>
    <script>
        function upP(){{
            const el=document.getElementById('p_tm'); const iso="{p_iso}";
            if(!iso){{ el.innerText="--:--"; return; }}
            const diff=new Date()-new Date(iso); if(diff<0) return;
            const m=Math.floor(diff/60000); el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0');
        }}
        setInterval(upP,1000); upP();
    </script>
    """, height=125)

with c2:
    components.html(f"""
    <div style="border-radius:12px; border:2px solid #FF9800; font-family:sans-serif; overflow:hidden;">
        <div style="background:#FFF3E0; padding: 12px 5px; text-align:center;">
            <div style="color:#E65100; font-weight:900; font-size: 0.85rem; margin-bottom:5px;">💩 대변 경과시간</div>
            <div style="font-size:2.0rem; font-weight:900; color:#BF360C; letter-spacing: 1px;" id="d_tm">00:00</div>
        </div>
        <div style="background:#FFCC80; padding: 6px; text-align:center; border-top: 2px solid #FFB74D;">
            <div style="color:#BF360C; font-size: 0.75rem; font-weight:bold;">발생 시각 {d_time_str}</div>
        </div>
    </div>
    <script>
        function upD(){{
            const el=document.getElementById('d_tm'); const iso="{d_iso}";
            if(!iso){{ el.innerText="--:--"; return; }}
            const diff=new Date()-new Date(iso); if(diff<0) return;
            const m=Math.floor(diff/60000); el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0');
        }}
        setInterval(upD,1000); upD();
    </script>
    """, height=125)

# ==========================================
# 5. 수동기록 및 리셋 (v11.8 듀얼 탭 모드)
# ==========================================
e1, e2 = st.columns(2)
with e1:
    with st.expander("⚙️ 소변 수동조절"):
        t_w1, t_k1 = st.tabs(["⏱️ 휠(시계)", "⌨️ 키보드"])
        with t_w1:
            p_wheel = st.time_input("현재 시간 기준 변경", now_kst().time(), key="p_wheel")
            if st.button("확인(휠)", key="bp_w", use_container_width=True): 
                add_record("💦 소변(수정) (통계제외)", f"{t_date} {p_wheel.strftime('%H:%M:%S')}")
        with t_k1:
            p_txt = st.text_input("시간 입력", value=now_kst().strftime("%H:%M"), key="p_txt", help="예: 14:30")
            if st.button("확인(키보드)", key="bp_k", use_container_width=True): 
                try:
                    valid_time = datetime.strptime(p_txt, "%H:%M").strftime("%H:%M:00")
                    add_record("💦 소변(수정) (통계제외)", f"{t_date} {valid_time}")
                except: st.error("HH:MM 형식으로 입력!")
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        if st.button("💧 소변 타이머 리셋", use_container_width=True, key="bp_r"): add_record("💦 소변 리셋 (통계제외)")

with e2:
    with st.expander("⚙️ 대변 수동조절"):
        t_w2, t_k2 = st.tabs(["⏱️ 휠(시계)", "⌨️ 키보드"])
        with t_w2:
            d_wheel = st.time_input("현재 시간 기준 변경", now_kst().time(), key="d_wheel")
            if st.button("확인(휠)", key="bd_w", use_container_width=True): 
                add_record("💩 대변(수정) (통계제외)", f"{t_date} {d_wheel.strftime('%H:%M:%S')}")
        with t_k2:
            d_txt = st.text_input("시간 입력", value=now_kst().strftime("%H:%M"), key="d_txt", help="예: 14:30")
            if st.button("확인(키보드)", key="bd_k", use_container_width=True): 
                try:
                    valid_time = datetime.strptime(d_txt, "%H:%M").strftime("%H:%M:00")
                    add_record("💩 대변(수정) (통계제외)", f"{t_date} {valid_time}")
                except: st.error("HH:MM 형식으로 입력!")
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        if st.button("💩 대변 타이머 리셋", use_container_width=True, key="bd_r"): add_record("💩 대변 리셋 (통계제외)")

# ==========================================
# 6. 배변 컨트롤 패널
# ==========================================
st.divider()
st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color:#444; margin-bottom: 12px;'>🔘 배변 컨트롤 패널</div>", unsafe_allow_html=True)
q1, q2 = st.columns(2)
with q1:
    if st.button("💦 집에서 소변", use_container_width=True): add_record("💦 집에서 소변")
with q2:
    if st.button("💩 집에서 대변", use_container_width=True): add_record("💩 집에서 대변")
st.write("🌳 **야외 산책 활동**")
s1, s2 = st.columns(2)
with s1:
    if st.button("🦮 일반 산책", use_container_width=True): add_record("🦮 일반 산책")
with s2:
    if st.button("🦮+💦 산책 중 소변", use_container_width=True): add_record("🦮+💦 산책 중 소변")
s3, s4 = st.columns(2)
with s3:
    if st.button("🦮+💩 산책 중 대변", use_container_width=True): add_record("🦮+💩 산책 중 대변")
with s4:
    if st.button("🦮+💦+💩 모두 해결", use_container_width=True): add_record("🦮+💦+💩 산책 중 소변과 대변")

# ==========================================
# 7. 누적 데이터 현황 보드
# ==========================================
st.divider()
st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color:#444; margin-bottom: 12px;'>📈 오늘의 누적 데이터 현황</div>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("💧 총 소변", f"{get_real_count('소변', target_df)}회")
m2.metric("💩 총 대변", f"{get_real_count('대변', target_df)}회")
m3.metric("🦮 총 산책", f"{get_real_count('산책', target_df)}회")

with st.expander("➖ 잘못 누른 횟수 변경 (차감하기)"):
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("소변 -1", use_container_width=True): add_record("💦 소변 차감 (-1)")
    with a2:
        if st.button("대변 -1", use_container_width=True): add_record("💩 대변 차감 (-1)")
    with a3:
        if st.button("산책 -1", use_container_width=True): add_record("🦮 산책 차감 (-1)")

# ==========================================
# 8. 취소 기능 (클라우드 동기화)
# ==========================================
st.divider()
if not target_df.empty:
    if st.button("❌ 직전 기록 취소", use_container_width=True):
        last_time = target_df.iloc[-1]['시간']
        # 클라우드에서 해당 시간 데이터 삭제
        requests.delete(f"{FIREBASE_URL}users/{username}/logs/{last_time}.json")
        # 로컬 세션에서도 삭제
        st.session_state.pet_logs = st.session_state.pet_logs.drop(target_df.index[-1])
        st.rerun()

# ==========================================
# 9. 앱 안전 종료 버튼 (드래그 이동)
# ==========================================
st.markdown("""
<a href="#lock" id="drag-btn">✖</a>
<div id="lock">
    <h2>🔒 안전하게 잠겼습니다</h2><p>스마트폰의 [홈 버튼]을 눌러 바탕화면으로 나가주세요.</p>
    <a href="#" style="color: gray; font-size: 1.2rem; padding: 10px; border: 1px solid gray; border-radius: 5px;">화면 다시 켜기</a>
</div>
<style>
    #drag-btn {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        width: 40px; height: 40px; background-color: #FF2A2A; color: white !important;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-size: 20px; font-weight: bold; text-decoration: none;
        box-shadow: 2px 4px 12px rgba(0,0,0,0.5); z-index: 9999; border: 2px solid white;
        cursor: grab; touch-action: none;
    }
    #drag-btn:active { cursor: grabbing; }
    #lock { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.95); z-index: 10000; color: white; text-align: center; padding-top: 35vh; }
    #lock:target { display: block; }
</style>
""", unsafe_allow_html=True)

drag_js = """
<script>
    const parent = window.parent.document;
    const btn = parent.getElementById('drag-btn');
    if (btn && !btn.dataset.draggable) {
        btn.dataset.draggable = "true";
        let isDown = false; let offset = [0,0];
        btn.addEventListener('touchstart', function(e) {
            isDown = true; let touch = e.touches[0];
            offset = [btn.offsetLeft - touch.clientX, btn.offsetTop - touch.clientY];
            btn.style.transform = 'none';
        }, {passive: false});
        parent.addEventListener('touchend', function() { isDown = false; }, true);
        parent.addEventListener('touchmove', function(e) {
            if(isDown) {
                e.preventDefault(); let touch = e.touches[0];
                btn.style.left = (touch.clientX + offset[0]) + 'px';
                btn.style.top  = (touch.clientY + offset[1]) + 'px';
                btn.style.bottom = 'auto';
            }
        }, {passive: false});
        btn.addEventListener('mousedown', function(e) {
            isDown = true; offset = [btn.offsetLeft - e.clientX, btn.offsetTop - e.clientY];
            btn.style.transform = 'none';
        }, true);
        parent.addEventListener('mouseup', function() { isDown = false; }, true);
        parent.addEventListener('mousemove', function(e) {
            if(isDown) {
                e.preventDefault();
                btn.style.left = (e.clientX + offset[0]) + 'px';
                btn.style.top  = (e.clientY + offset[1]) + 'px';
                btn.style.bottom = 'auto';
            }
        }, true);
    }
</script>
"""
components.html(drag_js, height=0, width=0)

# ==========================================
# 10. 웹 화면 하단 꼬리말 
# ==========================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 0.8rem; padding: 10px 0; margin-bottom: 50px;">
        Powered by Smart Pet Care Center (Multi-Tenant)<br>
        <strong>Current Version: {APP_VERSION}</strong><br>
        <span style="color: #2563eb; font-weight: bold;">[최종 클라우드 동기화] {last_upload_time}</span>
    </div>
""", unsafe_allow_html=True)

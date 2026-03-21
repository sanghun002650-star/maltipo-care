# *********************************************************************
# 🐾 스마트 관제 센터 소스 코드 (Smart Pet Care Center)
# 
# * 현재 버전   : v11.2 (실시간 경주 날씨/온도 API 연동판)
# * 최종 수정일 : 2026-03-22
# * 개발 및 유지보수 : Lee Sang-hoon (30년차 수석 엔지니어)
# *********************************************************************

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import os

# ==========================================
# 0. 엔진 세팅 및 KST 시간 설정
# ==========================================
APP_VERSION = "v11.2 (실시간 날씨 대시보드)"
KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)

DATA_FILE = "pet_care_data.csv"

VERSION_LOGS = {
    "v11.2": "대시보드에 글로벌 기상청 API 연동 (경주 지역 실시간 온도 및 낮/밤 자동 구분 기능 추가)",
    "v11.1": "메인 타이틀 및 각 패널 제목 글자 크기 2/3로 축소, 실시간 시계 위젯 추가",
    "v11.0": "누적 카운터 무결점 엔진(Pure Python 1:1 카운팅) 적용 완료",
    "v10.9": "CSV 데이터 로드 시 빈칸(NaN) 필터링 방어 코드 적용",
    "v10.8": "갤럭시 노트20 UI 최적화, 모니터링 창 투톤 분할 적용"
}

st.set_page_config(page_title="스마트 관제 센터", layout="centered", page_icon="🐾")

st.markdown("""
<style>
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: wrap !important; gap: 5px !important; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { flex: 1 1 48% !important; min-width: 48% !important; }
    }
    div.stButton > button { height: 3.5rem !important; border-radius: 12px !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. 사이드바 (설정)
# ==========================================
st.sidebar.header("⚙️ 관제 센터 설정")
st.sidebar.success(f"🚀 {APP_VERSION}")

with st.sidebar.expander("📝 버전 업데이트 이력 (Log)", expanded=False):
    for ver, desc in VERSION_LOGS.items():
        st.markdown(f"**{ver}** : {desc}")

if 'pet_name' not in st.session_state: st.session_state.pet_name = "말티푸"
new_name = st.sidebar.text_input("🐶 타이틀 이름 변경", value=st.session_state.pet_name)
if new_name != st.session_state.pet_name:
    st.session_state.pet_name = new_name
    st.rerun()

# ==========================================
# 2. 블랙박스 영구 데이터베이스
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE): return pd.read_csv(DATA_FILE)
    else: return pd.DataFrame(columns=["시간", "활동"])

if 'pet_logs' not in st.session_state:
    st.session_state.pet_logs = load_data()

def add_record(act, c_time=None):
    t = c_time if c_time else now_kst().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, new_row], ignore_index=True)
    st.session_state.pet_logs.to_csv(DATA_FILE, index=False) 
    st.rerun()

t_date = now_kst().strftime("%Y-%m-%d")
df = st.session_state.pet_logs
if not df.empty and "시간" in df.columns:
    target_df = df[df['시간'].astype(str).str.startswith(t_date, na=False)]
else:
    target_df = pd.DataFrame(columns=["시간", "활동"])

# ==========================================
# 3. 메인 타이틀 & 실시간 날씨/시간 대시보드
# ==========================================
st.markdown(f"<div style='text-align:center; font-size: 1.6rem; font-weight: 900; color:#333; padding-bottom: 5px;'>📊 {st.session_state.pet_name} 스마트 관제 센터</div>", unsafe_allow_html=True)

# [엔지니어 추가] Open-Meteo API를 사용해 경주(위도 35.85, 경도 129.22)의 실시간 온도와 낮/밤 여부를 가져옵니다.
clock_weather_html = """
<div style="background-color: #f1f5f9; border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 20px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); font-family: sans-serif;">
    <div id="live_clock" style="font-size: 1.1rem; font-weight: 900; color: #1e293b; letter-spacing: 0.5px;"></div>
    <div id="weather_info" style="font-size: 0.85rem; font-weight: bold; color: #475569; margin-top: 5px;">
        📍 경북 경주시 ｜ 날씨 정보 불러오는 중... ⏳
    </div>
</div>
<script>
    // 시계 업데이트 (1초마다)
    function updateClock() {
        const now = new Date();
        const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
        document.getElementById('live_clock').innerText = now.toLocaleString('ko-KR', options);
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 경주 지역 실시간 날씨 API 호출
    async function updateWeather() {
        try {
            // 경주시청 기준 위도/경도
            const res = await fetch('https://api.open-meteo.com/v1/forecast?latitude=35.8562&longitude=129.2247&current_weather=true&timezone=Asia%2FSeoul');
            const data = await res.json();
            const current = data.current_weather;
            const temp = current.temperature;
            
            // is_day: 1이면 낮, 0이면 밤
            const isDay = current.is_day === 1;
            const icon = isDay ? "☀️ 낮" : "🌙 밤";
            
            let desc = "맑음";
            if(current.weathercode >= 1 && current.weathercode <= 3) desc = "구름/흐림";
            else if(current.weathercode >= 50 && current.weathercode <= 69) desc = "비☔";
            else if(current.weathercode >= 71) desc = "눈❄️";

            document.getElementById('weather_info').innerHTML = 
                `📍 경북 경주시 ｜ ${icon} ｜ 🌡️ 현재 온도: ${temp}℃ (${desc})`;
        } catch(e) {
            // 인터넷 연결이 안될 때의 비상용 (시간으로 낮밤 계산)
            const h = new Date().getHours();
            const icon = (h >= 6 && h < 18) ? "☀️ 낮" : "🌙 밤";
            document.getElementById('weather_info').innerHTML = 
                `📍 경북 경주시 ｜ ${icon} ｜ 🌡️ 온도 센서 연결 대기중...`;
        }
    }
    // 날씨는 처음에 한 번 부르고 30분마다 갱신
    updateWeather();
    setInterval(updateWeather, 1800000);
</script>
"""
components.html(clock_weather_html, height=85)

# ==========================================
# 4. 실시간 배변 모니터링 
# ==========================================
def get_iso(act_keyword):
    if target_df.empty: return ""
    for i in range(len(target_df)-1, -1, -1):
        act = str(target_df.iloc[i]['활동'])
        t = str(target_df.iloc[i]['시간'])
        if '차감' in act: continue 
        if act_keyword in act:
            if '끄기' in act or '리셋' in act: return ""
            return t.replace(" ", "T") + "+09:00"
    return ""

p_iso = get_iso("소변")
d_iso = get_iso("대변")
p_time_str = p_iso[11:16] if p_iso else "--:--"
d_time_str = d_iso[11:16] if d_iso else "--:--"

st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color:#444; margin-bottom: 8px;'>💡 실시간 배변 모니터링</div>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    components.html(f"""
    <div style="border-radius:12px; border:2px solid #4CAF50; font-family:sans-serif; overflow:hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="background:#E8F5E9; padding: 12px 5px; text-align:center;">
            <div style="color:#2E7D32; font-weight:900; font-size: 0.85rem; margin-bottom:5px;">💧 소변 경과시간</div>
            <div style="font-size:2.0rem; font-weight:900; color:#1B5E20; letter-spacing: 1px;" id="p_tm">00:00</div>
        </div>
        <div style="background:#A5D6A7; padding: 6px; text-align:center; border-top: 2px solid #81C784;">
            <div style="color:#1B5E20; font-size: 0.75rem; font-weight:bold; margin-bottom:2px;">발생 시각</div>
            <div style="color:#004D40; font-size:1.1rem; font-weight:900;">{p_time_str}</div>
        </div>
    </div>
    <script>
        function upP(){{
            const el=document.getElementById('p_tm'); const iso="{p_iso}";
            if(!iso){{ el.innerText="--:--"; return; }}
            const diff=new Date()-new Date(iso); if(diff<0) return;
            const m=Math.floor(diff/60000);
            el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0');
        }}
        setInterval(upP,1000); upP();
    </script>
    """, height=140)

with c2:
    components.html(f"""
    <div style="border-radius:12px; border:2px solid #FF9800; font-family:sans-serif; overflow:hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="background:#FFF3E0; padding: 12px 5px; text-align:center;">
            <div style="color:#E65100; font-weight:900; font-size: 0.85rem; margin-bottom:5px;">💩 대변 경과시간</div>
            <div style="font-size:2.0rem; font-weight:900; color:#BF360C; letter-spacing: 1px;" id="d_tm">00:00</div>
        </div>
        <div style="background:#FFCC80; padding: 6px; text-align:center; border-top: 2px solid #FFB74D;">
            <div style="color:#BF360C; font-size: 0.75rem; font-weight:bold; margin-bottom:2px;">발생 시각</div>
            <div style="color:#3E2723; font-size:1.1rem; font-weight:900;">{d_time_str}</div>
        </div>
    </div>
    <script>
        function upD(){{
            const el=document.getElementById('d_tm'); const iso="{d_iso}";
            if(!iso){{ el.innerText="--:--"; return; }}
            const diff=new Date()-new Date(iso); if(diff<0) return;
            const m=Math.floor(diff/60000);
            el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0');
        }}
        setInterval(upD,1000); upD();
    </script>
    """, height=140)

# ==========================================
# 5. 수동기록 및 리셋
# ==========================================
e1, e2 = st.columns(2)
with e1:
    with st.expander("⚙️ 소변 수동조절"):
        np = st.time_input("시각 선택", now_kst().time(), key="tp")
        if st.button("시간 수정", key="bp", use_container_width=True): 
            add_record("💦 소변(수정) (통계제외)", f"{t_date} {np.strftime('%H:%M:%S')}")
        if st.button("💧 소변 타이머 리셋", use_container_width=True): 
            add_record("💦 소변 리셋 (통계제외)")

with e2:
    with st.expander("⚙️ 대변 수동조절"):
        nd = st.time_input("시각 선택", now_kst().time(), key="td")
        if st.button("시간 수정", key="bd", use_container_width=True): 
            add_record("💩 대변(수정) (통계제외)", f"{t_date} {nd.strftime('%H:%M:%S')}")
        if st.button("💩 대변 타이머 리셋", use_container_width=True): 
            add_record("💩 대변 리셋 (통계제외)")

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
# 7. 누적 데이터 현황 보드 (무결점 엔진 유지)
# ==========================================
st.divider()
st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color:#444; margin-bottom: 12px;'>📈 오늘의 누적 데이터 현황</div>", unsafe_allow_html=True)

def get_real_count(keyword):
    if target_df.empty: return 0
    plus_count = 0
    minus_count = 0
    for act in target_df['활동'].astype(str):
        if keyword in act:
            if '차감' in act: minus_count += 1
            elif any(x in act for x in ['리셋', '끄기', '통계제외']): pass 
            else: plus_count += 1
    return max(0, plus_count - minus_count)

st.info(f"💧 총 소변: **{get_real_count('소변')}회** ｜ 💩 총 대변: **{get_real_count('대변')}회** ｜ 🦮 총 산책: **{get_real_count('산책')}회**")

a1, a2, a3 = st.columns(3)
with a1:
    if st.button("소변 횟수 -1", use_container_width=True): add_record("💦 소변 차감 (-1)")
with a2:
    if st.button("대변 횟수 -1", use_container_width=True): add_record("💩 대변 차감 (-1)")
with a3:
    if st.button("산책 횟수 -1", use_container_width=True): add_record("🦮 산책 차감 (-1)")

# ==========================================
# 8. 취소 기능 
# ==========================================
st.divider()
if not target_df.empty:
    if st.button("❌ 직전 기록 취소", use_container_width=True):
        st.session_state.pet_logs = st.session_state.pet_logs.drop(target_df.index[-1])
        st.session_state.pet_logs.to_csv(DATA_FILE, index=False)
        st.rerun()

# ==========================================
# 9. 앱 안전 종료 버튼
# ==========================================
st.markdown("""
<style>
    .exit-btn {
        position: fixed; bottom: 30px; right: 20px; width: 60px; height: 60px;
        background-color: #FF2A2A; color: white !important; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 32px; font-weight: bold; text-decoration: none;
        box-shadow: 2px 4px 12px rgba(0,0,0,0.4); z-index: 9999; border: 3px solid white;
    }
    #lock {
        display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.95); z-index: 10000; color: white; text-align: center; padding-top: 35vh;
    }
    #lock:target { display: block; }
</style>
<a href="#lock" class="exit-btn">✖</a>
<div id="lock">
    <h2>🔒 안전하게 잠겼습니다</h2><p>스마트폰의 [홈 버튼]을 눌러 바탕화면으로 나가주세요.</p>
    <a href="#" style="color: gray; font-size: 1.2rem; padding: 10px; border: 1px solid gray; border-radius: 5px;">화면 다시 켜기</a>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 10. 최하단 버전 정보 꼬리말
# ==========================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 0.8rem; padding: 10px 0; margin-bottom: 50px;">
        Powered by Smart Pet Care Center<br>
        <strong>Current Version: {APP_VERSION}</strong>
    </div>
""", unsafe_allow_html=True)

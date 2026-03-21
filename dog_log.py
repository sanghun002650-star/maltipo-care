# *********************************************************************
# 🐾 스마트 관제 센터 소스 코드 (Smart Pet Care Center)
# 
# * 현재 버전   : v10.7 (영구 저장 및 시각 표시 탑재)
# * 최종 수정일 : 2026-03-21
# * 개발 및 유지보수 : Lee Sang-hoon
# *********************************************************************

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import os # 파일 저장/불러오기를 위한 모듈 추가

# ==========================================
# 0. 엔진 세팅 및 KST 시간 설정
# ==========================================
APP_VERSION = "v10.7 (블랙박스 영구저장판)"
KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)

# 데이터가 영구 저장될 엑셀(CSV) 파일 이름
DATA_FILE = "pet_care_data.csv"

print(f"\n=========================================")
print(f"🚀 스마트 관제 센터 엔진 가동 준비 완료!")
print(f"📦 로드된 시스템 버전 : {APP_VERSION}")
print(f"⏰ 엔진 구동 시간 : {now_kst().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"=========================================\n")

VERSION_LOGS = {
    "v10.7": "CSV 영구 저장 기능 추가(앱 종료 시 데이터 보존) 및 모니터링 창에 마지막 발생 시각 명시",
    "v10.6": "소스코드 상단에 버전 명세서 추가 및 터미널(콘솔) 구동 로그 출력",
    "v10.5": "앱 화면 최하단에 현재 버전 정보(Footer)가 항상 표시되도록 고정",
    "v10.4": "집에서 소변/대변 버튼 색상을 무색(기본 테마)으로 변경",
    "v10.3": "사이드바에 버전 업데이트 유지보수 이력(Log) 기능 추가",
    "v10.2": "누적 현황과 배변 컨트롤 패널 위치 맞교환 (동선 최적화)",
    "v10.1": "소변/대변 모니터링 창 완벽 분리 및 에러 없는 로컬 환경 적용"
}

st.set_page_config(page_title="스마트 관제 센터", layout="centered", page_icon="🐾")

# ==========================================
# 1. 사이드바 (설정)
# ==========================================
st.sidebar.header("⚙️ 관제 센터 설정")
st.sidebar.success(f"🚀 현재 버전: {APP_VERSION}")

with st.sidebar.expander("📝 버전 업데이트 이력 (Log)", expanded=False):
    for ver, desc in VERSION_LOGS.items():
        st.markdown(f"**{ver}** : {desc}")

if 'pet_name' not in st.session_state: 
    st.session_state.pet_name = "말티푸"

new_name = st.sidebar.text_input("🐶 타이틀 이름 변경", value=st.session_state.pet_name)
if new_name != st.session_state.pet_name:
    st.session_state.pet_name = new_name
    st.rerun()

# ==========================================
# 2. 블랙박스 영구 데이터베이스 (Load & Write)
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["시간", "활동"])

# 앱 시작 시 CSV 파일에서 기존 기록을 불러옴
if 'pet_logs' not in st.session_state:
    st.session_state.pet_logs = load_data()

def add_record(act, c_time=None):
    t = c_time if c_time else now_kst().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, new_row], ignore_index=True)
    
    # 메모리에 추가된 데이터를 파일(하드디스크)에 즉시 덮어쓰기 저장 (영구 보존)
    st.session_state.pet_logs.to_csv(DATA_FILE, index=False) 
    st.rerun()

# [중요] 화면에 보여지는 데이터는 '오늘(00시~24시)' 데이터로만 필터링!
t_date = now_kst().strftime("%Y-%m-%d")
df = st.session_state.pet_logs
target_df = df[df['시간'].str.contains(t_date)] if not df.empty else pd.DataFrame()

# ==========================================
# 3. 메인 타이틀
# ==========================================
st.markdown(f"<h2 style='text-align:center; padding-bottom: 20px;'>📊 {st.session_state.pet_name} 스마트 관제 센터</h2>", unsafe_allow_html=True)

# ==========================================
# 4. 실시간 배변 모니터링 (시각 표시 추가)
# ==========================================
def get_iso(act):
    if target_df.empty: return ""
    recs = target_df[target_df['활동'].str.contains(act) & ~target_df['활동'].str.contains('차감')]
    if recs.empty: return ""
    last = recs.iloc[-1]
    return "" if ("끄기" in last['활동'] or "리셋" in last['활동']) else str(last['시간']).replace(" ", "T") + "+09:00"

p_iso = get_iso("소변")
d_iso = get_iso("대변")

# 정확한 시간(HH:MM)만 추출
p_time_str = p_iso[11:16] if p_iso else "--:--"
d_time_str = d_iso[11:16] if d_iso else "--:--"

st.subheader("💡 실시간 배변 모니터링")
c1, c2 = st.columns(2)

with c1:
    components.html(f"""
    <div style="background:#E8F5E9; padding:20px; border-radius:15px; border:3px solid #4CAF50; text-align:center; font-family:sans-serif;">
        <div style="color:#2E7D32; font-weight:bold; margin-bottom:5px;">💧 마지막 소변 경과</div>
        <div style="color:#1B5E20; font-size:1.1rem; font-weight:bold; margin-bottom:10px; background:#C8E6C9; display:inline-block; padding:2px 10px; border-radius:5px;">발생 시각 {p_time_str}</div>
        <div style="font-size:2.5rem; font-weight:900; color:#1B5E20;" id="p_tm">00:00</div>
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
    """, height=160)

with c2:
    components.html(f"""
    <div style="background:#FFF3E0; padding:20px; border-radius:15px; border:3px solid #FF9800; text-align:center; font-family:sans-serif;">
        <div style="color:#E65100; font-weight:bold; margin-bottom:5px;">💩 마지막 대변 경과</div>
        <div style="color:#BF360C; font-size:1.1rem; font-weight:bold; margin-bottom:10px; background:#FFE0B2; display:inline-block; padding:2px 10px; border-radius:5px;">발생 시각 {d_time_str}</div>
        <div style="font-size:2.5rem; font-weight:900; color:#BF360C;" id="d_tm">00:00</div>
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
    """, height=160)

# ==========================================
# 5. 수동기록 및 리셋 
# ==========================================
e1, e2 = st.columns(2)
with e1:
    with st.expander("⚙️ 소변 수동기록 / 리셋"):
        np = st.time_input("시각 선택", now_kst().time(), key="tp")
        if st.button("시간 수정", key="bp", use_container_width=True): 
            add_record("💦 소변(수정) (통계제외)", f"{t_date} {np.strftime('%H:%M:%S')}")
        if st.button("💧 소변 타이머 리셋", use_container_width=True): 
            add_record("💦 소변 리셋 (통계제외)")

with e2:
    with st.expander("⚙️ 대변 수동기록 / 리셋"):
        nd = st.time_input("시각 선택", now_kst().time(), key="td")
        if st.button("시간 수정", key="bd", use_container_width=True): 
            add_record("💩 대변(수정) (통계제외)", f"{t_date} {nd.strftime('%H:%M:%S')}")
        if st.button("💩 대변 타이머 리셋", use_container_width=True): 
            add_record("💩 대변 리셋 (통계제외)")

# ==========================================
# 6. 배변 컨트롤 패널
# ==========================================
st.divider()
st.header("🔘 배변 컨트롤 패널")
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
st.header("📈 오늘의 누적 데이터 현황")

def g_cnt(l):
    if target_df.empty: return 0
    p = len(target_df[target_df['활동'].str.contains(l) & ~target_df['활동'].str.contains('차감|리셋|통계제외')])
    m = len(target_df[target_df['활동'].str.contains(l) & target_df['활동'].str.contains('차감')])
    return max(0, p-m)

st.info(f"💧 총 소변: **{g_cnt('소변')}회** ｜ 💩 총 대변: **{g_cnt('대변')}회** ｜ 🦮 총 산책: **{g_cnt('산책')}회**")

a1, a2, a3 = st.columns(3)
with a1:
    if st.button("소변 횟수 -1", use_container_width=True): add_record("💦 소변 차감 (-1)")
with a2:
    if st.button("대변 횟수 -1", use_container_width=True): add_record("💩 대변 차감 (-1)")
with a3:
    if st.button("산책 횟수 -1", use_container_width=True): add_record("🦮 산책 차감 (-1)")

# ==========================================
# 8. 취소 기능 (취소 시에도 파일에 반영)
# ==========================================
st.divider()
if not target_df.empty:
    if st.button("❌ 직전 기록 취소", use_container_width=True):
        st.session_state.pet_logs = st.session_state.pet_logs.drop(target_df.index[-1])
        st.session_state.pet_logs.to_csv(DATA_FILE, index=False) # 취소된 상태로 파일 다시 덮어쓰기
        st.rerun()

# ==========================================
# 9. 앱 안전 종료 버튼
# ==========================================
st.markdown("""
<style>
    .exit-btn {
        position: fixed; bottom: 25px; right: 25px; width: 65px; height: 65px;
        background-color: #FF2A2A; color: white !important; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 35px; font-weight: bold; text-decoration: none;
        box-shadow: 2px 4px 12px rgba(0,0,0,0.4); z-index: 9999; border: 3px solid white;
    }
    #lock {
        display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.95); z-index: 10000; color: white; text-align: center; padding-top: 40vh;
    }
    #lock:target { display: block; }
</style>
<a href="#lock" class="exit-btn">✖</a>
<div id="lock">
    <h2>🔒 안전하게 잠겼습니다</h2><p>스마트폰의 [홈 버튼]을 눌러 바탕화면으로 나가주세요.</p>
    <a href="#" style="color: gray; font-size: 1.2rem;">[ 화면 다시 켜기 ]</a>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 10. 최하단 버전 정보 꼬리말 (Footer)
# ==========================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #888; font-size: 0.85rem; padding: 10px 0; margin-bottom: 50px;">
        Powered by Smart Pet Care Center<br>
        <strong>Current Version: {APP_VERSION}</strong>
    </div>
""", unsafe_allow_html=True)

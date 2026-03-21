# *********************************************************************
# 🐾 스마트 관제 센터 (Smart Pet Care Center)
# * 버전 : v12.0 (안정성 + 성능 + 구조 개선 통합판)
# *********************************************************************

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import os

# ==========================================
# 0. 기본 설정
# ==========================================
APP_VERSION = "v12.0 (안정성 + 성능 개선)"
KST = timezone(timedelta(hours=9))
DATA_FILE = "pet_care_data.csv"

def now_kst():
    return datetime.now(KST)

# ==========================================
# 1. 안전 저장 함수 (중요)
# ==========================================
def safe_save(df, file_path):
    tmp_path = file_path + ".tmp"
    df.to_csv(tmp_path, index=False)
    os.replace(tmp_path, file_path)

# ==========================================
# 2. 데이터 로드 (캐싱)
# ==========================================
@st.cache_data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['시간'] = pd.to_datetime(df['시간'], errors='coerce')
        return df
    return pd.DataFrame(columns=["시간", "활동"])

# ==========================================
# 3. 초기 세팅
# ==========================================
st.set_page_config(page_title="스마트 관제 센터", layout="centered", page_icon="🐾")

if 'pet_logs' not in st.session_state:
    st.session_state.pet_logs = load_data()

if 'pet_name' not in st.session_state:
    st.session_state.pet_name = "말티푸"

# ==========================================
# 4. 기록 추가 함수
# ==========================================
def add_record(act, c_time=None):
    t = pd.to_datetime(c_time) if c_time else now_kst()
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, new_row], ignore_index=True)

    safe_save(st.session_state.pet_logs, DATA_FILE)
    st.toast("기록 완료")
    st.rerun()

# ==========================================
# 5. 오늘 데이터 필터
# ==========================================
df = st.session_state.pet_logs
today = now_kst().date()

if not df.empty:
    target_df = df[df['시간'].dt.date == today]
else:
    target_df = pd.DataFrame(columns=["시간", "활동"])

# ==========================================
# 6. 메인 UI
# ==========================================
st.markdown(f"<div style='text-align:center; font-size:1.6rem; font-weight:900;'>📊 {st.session_state.pet_name} 스마트 관제 센터</div>", unsafe_allow_html=True)

# ==========================================
# 7. 시계
# ==========================================
clock_html = """
<div style="text-align:center; padding:10px;">
<div id="clock" style="font-size:1.2rem; font-weight:900;"></div>
</div>
<script>
function updateClock(){
    const now = new Date();
    document.getElementById('clock').innerText = now.toLocaleString('ko-KR');
}
setInterval(updateClock,1000);
updateClock();
</script>
"""
components.html(clock_html, height=60)

# ==========================================
# 8. 최근 기록 시간 계산
# ==========================================
def get_last_time(keyword):
    df_f = target_df[
        target_df['활동'].str.contains(keyword, na=False) &
        ~target_df['활동'].str.contains('차감|리셋', na=False)
    ]
    if df_f.empty:
        return None
    return df_f.iloc[-1]['시간']

def elapsed_str(last_time):
    if last_time is None:
        return "--:--"
    diff = now_kst() - last_time
    m = int(diff.total_seconds() // 60)
    return f"{m//60:02}:{m%60:02}"

# ==========================================
# 9. 모니터링
# ==========================================
st.subheader("💡 실시간 배변 모니터링")

p_time = get_last_time("소변")
d_time = get_last_time("대변")

c1, c2 = st.columns(2)

with c1:
    st.metric("💧 소변 경과", elapsed_str(p_time))

with c2:
    st.metric("💩 대변 경과", elapsed_str(d_time))

# ==========================================
# 10. 버튼
# ==========================================
st.subheader("🔘 컨트롤")

col1, col2 = st.columns(2)

with col1:
    if st.button("💧 소변"):
        add_record("소변")

with col2:
    if st.button("💩 대변"):
        add_record("대변")

if st.button("🦮 산책"):
    add_record("산책")

# ==========================================
# 11. 카운트
# ==========================================
def count(keyword):
    return len(target_df[target_df['활동'].str.contains(keyword, na=False)])

st.subheader("📈 오늘 통계")
st.info(f"💧 {count('소변')}회 | 💩 {count('대변')}회 | 🦮 {count('산책')}회")

# ==========================================
# 12. 취소
# ==========================================
if not target_df.empty:
    if st.button("❌ 마지막 기록 삭제"):
        st.session_state.pet_logs = st.session_state.pet_logs.drop(target_df.index[-1])
        safe_save(st.session_state.pet_logs, DATA_FILE)
        st.rerun()

# ==========================================
# 13. 하단
# ==========================================
st.markdown("---")
st.caption(f"버전: {APP_VERSION}")

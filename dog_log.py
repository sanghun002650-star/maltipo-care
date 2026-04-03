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
APP_VERSION = "v13.7.4 (조회 날짜 연동 및 폰트 균등화)"
UPDATE_DATE = "2026-04-03" 

KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)
FIREBASE_URL = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/" 

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
        <div style='font-size:1.5rem; font-weight:900; color:#1e293b; margin-top:8px;'>스마트 관제 센터 프로젝트</div>
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
# ☁️ 클라우드 엔진
# ==========================================
username = st.session_state.username 

def _unique_ts(base_time=None):
    t = base_time if base_time else now_kst()
    return t.strftime("%Y-%m-%d %H:%M:%S_%f") 

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
    try: 
        res = requests.put(f"{FIREBASE_URL}users/{username}/profile.json", json=profile, timeout=5)
        res.raise_for_status()
    except: st.error("⚠️ 저장 실패") 

def save_settings(settings_data):
    try: 
        res = requests.put(f"{FIREBASE_URL}users/{username}/settings.json", json=settings_data, timeout=5)
        res.raise_for_status()
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
    try: 
        res = requests.patch(f"{FIREBASE_URL}users/{username}/logs.json", json={t: act}, timeout=5)
        res.raise_for_status()
    except:
        st.error(f"⚠️ 클라우드 저장 실패"); return
    
    new_row = pd.DataFrame([{"시간": t, "활동": act}])
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, new_row], ignore_index=True)
    st.rerun() 

if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'settings' not in st.session_state: st.session_state.settings = load_settings()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data() 

# ==========================================
# 🎨 동적 CSS 인젝션
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
    border-radius:18px; 
    padding: 40px 20px 14px 20px; 
    margin-bottom:15px; color:white;
    min-height: 85px; line-height: 1.4; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}} 

div.stButton > button {{
    height: {DYNAMIC_BTN_H}rem !important;
    border-radius: 16px !important; font-weight: 900 !important; font-size: 1.05rem !important;
    letter-spacing: -0.3px !important; border: none !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important; transition: transform 0.1s, box-shadow 0.1s !important;
}} 

.horizontal-metrics {{ display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }}
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
.last-date {{ font-size: 0.72rem; color: #64748b; font-weight: 600; text-align: right; }}
.d-day-badge {{
    background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 6px;
    font-size: 0.7rem; margin-left: 5px; font-weight: 800;
}} 

/* 메모장 인라인 스타일 적용으로 인한 클래스 삭제 (요청사항 반영) */

.stTabs [data-baseweb="tab-list"] {{ 
    gap: 25px !important; 
    justify-content: center !important; 
}}
.stTabs [data-baseweb="tab"] {{ 
    height: 3.2rem !important; 
    font-weight: 800 !important; 
    padding: 0 15px !important; 
}}
hr {{ margin: 12px 0 !important; }}
.streamlit-expanderHeader {{ font-weight: 700 !important; font-size: 0.95rem !important; }} 

/* 모바일 환경에서 컬럼이 세로로 꺾이지 않게 강제 가로 배열 설정 */
@media (max-width: 768px) {{
    div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important;
        gap: 10px !important;
    }}
}}
</style>
""", unsafe_allow_html=True) 

# ==========================================
# ⚙️ 사이드바
# ==========================================
with st.sidebar:
    st.markdown(f"### ⚙️ {username}님")
    if st.button("🔒 로그아웃", use_container_width=True):
        cookie_manager.delete("saved_username")
        st.session_state.force_logout = True
        st.session_state.logged_in = False
        time.sleep(0.3); st.rerun()
    
    st.caption(f"📌 버전: {APP_VERSION}")
    st.divider()
    
    with st.expander("🎨 UI 설정", expanded=False):
        new_btn_h = st.slider("버튼 높이", 3.0, 6.0, float(st.session_state.settings.get('btn_h', 4.2)), 0.1)
        new_hdr_c = st.color_picker("섹션 헤더 색상", st.session_state.settings.get('hdr_color', '#94a3b8'))
        
        st.markdown("**배치 순서**")
        new_order = {}
        for k, v in st.session_state.settings.get('order', {}).items():
            new_order[k] = st.number_input(k, min_value=1, max_value=20, value=int(v), step=1)
            
        if st.button("설정 저장", use_container_width=True, type="primary"):
            st.session_state.settings.update({'btn_h': new_btn_h, 'hdr_color': new_hdr_c, 'order': new_order})
            save_settings(st.session_state.settings)
            st.rerun() 

    with st.expander("📝 반려견 정보 수정"):
        p_name   = st.text_input("🐶 이름",   value=st.session_state.profile.get('pet_name',''))
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
# 📊 데이터 헬퍼
# ==========================================
t_date = now_kst().strftime("%Y-%m-%d")
df = st.session_state.pet_logs
target_df = df[df['시간'].astype(str).str.startswith(t_date, na=False)].copy() if not df.empty else pd.DataFrame(columns=["시간","활동"]) 

def get_iso(act_keyword, check_df):
    if check_df.empty: return ""
    for i in range(len(check_df)-1, -1, -1):
        act = str(check_df.iloc[i]['활동'])
        t   = str(check_df.iloc[i]['시간'])
        
        if '_' in t: t = t.split('_')[0]
        elif '.' in t: t = t.split('.')[0]
        
        if '차감' in act: continue
        
        if act_keyword in act:
            if '끄기' in act or '리셋' in act: return ""
            if '(수정)' in act and '[' in act and ']' in act:
                try:
                    extracted_time = act.split('[')[1].split(']')[0]
                    date_part = t.split(' ')[0]
                    return f"{date_part}T{extracted_time}+09:00"
                except:
                    pass
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

def get_d_day_info(keyword):
    if df.empty: return "기록 없음", "", "기록 없음"
    
    matches = df[df['활동'].str.contains(keyword, na=False)].copy()
    if matches.empty: return "기록 없음", "", "기록 없음"
    
    matches = matches.sort_values(by='시간', ascending=True)
    
    last_record = matches.iloc[-1]
    last_dt_full = str(last_record['시간'])
    last_dt_str = last_dt_full[:10]
    last_act = str(last_record['활동'])
    
    if ":" in last_act:
        last_memo = last_act.split(":", 1)[1].strip()
    else:
        last_memo = last_act
        
    last_dt = datetime.strptime(last_dt_str, "%Y-%m-%d").date()
    diff = (now_kst().date() - last_dt).days
    d_day_str = f"<span class='d-day-badge'>{diff}일 경과</span>" if diff > 0 else "<span class='d-day-badge'>오늘 완료</span>"
    
    return last_dt_str, d_day_str, last_memo

# 🔥 추가된 헬퍼 함수: 특정 날짜의 기록만 정확히 타겟팅하여 추출
def get_record_for_date(keyword, target_date_str):
    if df.empty: return target_date_str, "해당 날짜 기록 없음"
    matches = df[df['시간'].astype(str).str.startswith(target_date_str) & df['활동'].str.contains(keyword, na=False)].copy()
    if matches.empty: return target_date_str, "해당 날짜 기록 없음"
    
    matches = matches.sort_values(by='시간', ascending=True)
    last_act = str(matches.iloc[-1]['활동'])
    
    if ":" in last_act:
        memo = last_act.split(":", 1)[1].strip()
    else:
        memo = last_act
    return target_date_str, memo

p_iso = get_iso("소변", target_df)
d_iso = get_iso("대변", target_df)
p_time_str = p_iso[11:16] if p_iso else "--:--"
d_time_str = d_iso[11:16] if d_iso else "--:--" 

# ==========================================
# 🧱 UI 모듈
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
    p, d, w = get_real_count('소변', target_df), get_real_count('대변', target_df), get_real_count('산책', target_df)
    st.markdown(f"""
    <div class="horizontal-metrics">
        <div class="metric-box"><div class="metric-label">💧 소변</div><div class="metric-value">{p}회</div></div>
        <div class="metric-box"><div class="metric-label">💩 대변</div><div class="metric-value">{d}회</div></div>
        <div class="metric-box"><div class="metric-label">🦮 산책</div><div class="metric-value">{w}회</div></div>
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

# 🔥 집중 수정된 함수: 상태 보존 및 인라인 CSS 폰트 강제 적용
def render_health_beauty():
    st.markdown("<div class='section-header'>🏥 건강 / 미용 관리</div>", unsafe_allow_html=True)
    
    # 상단 뱃지는 기존처럼 전체 데이터의 '최근'을 유지합니다.
    l_mh, d_mh, _ = get_d_day_info("🏥 병원/약")
    l_gr, d_gr, _ = get_d_day_info("✂️ 미용") 

    with st.expander("✨ 상세 기록 관리 (약/병원/미용 메모)", expanded=False):
        ts = now_kst().strftime("%H:%M:%S_%f")
        
        # 1. 파이어베이스(settings)에서 마지막 조회 날짜 로드 (없으면 오늘)
        saved_d_mh_str = st.session_state.settings.get("sel_date_mh", now_kst().strftime("%Y-%m-%d"))
        saved_d_gr_str = st.session_state.settings.get("sel_date_gr", now_kst().strftime("%Y-%m-%d"))
        
        saved_d_mh = datetime.strptime(saved_d_mh_str, "%Y-%m-%d").date()
        saved_d_gr = datetime.strptime(saved_d_gr_str, "%Y-%m-%d").date()
        
        # [병원/약 파트]
        st.markdown(f"<div class='health-row'><span>🏥 병원/약</span><span class='last-date'>전체최근: {l_mh} {d_mh}</span></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1.2, 1])
        with c1:
            d_val = st.date_input("날짜", value=saved_d_mh, key="d_mh")
            
            # 2. 날짜 변경 감지 시 파이어베이스 즉각 동기화 (앱 재실행 대비)
            if d_val != saved_d_mh:
                st.session_state.settings["sel_date_mh"] = d_val.strftime("%Y-%m-%d")
                save_settings(st.session_state.settings)
                st.rerun()
                
            t_val = st.text_input("메모 (예: 심장사상충)", key="t_mh", placeholder="음성/키보드 입력")
            if st.button("🏥 기록 저장", use_container_width=True):
                add_record(f"🏥 병원/약: {t_val}" if t_val else "🏥 병원/약", f"{d_val} {ts}")
        with c2:
            date_mh, memo_mh = get_record_for_date("🏥 병원/약", d_val.strftime("%Y-%m-%d"))
            # 3. 다른 곳에 영향 없도록 인라인(Inline) 스타일만 사용, 날짜와 메모 텍스트 사이즈를 1.1rem으로 완벽 동일화
            st.markdown(f"""
            <div style='padding: 18px 15px; border-radius: 12px; min-height: 110px; display: flex; flex-direction: column; justify-content: center; border: 2px solid #e2e8f0; margin-bottom: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.05); background-color: #fefce8; border-left: 6px solid #facc15;'>
                <div style='font-size: 0.85rem; font-weight: 900; margin-bottom: 8px; color: #a16207;'>📌 선택일 진료/약 기록</div>
                <div style='font-size: 1.1rem; font-weight: 900; color: #52525b; margin-bottom: 4px;'>📅 {date_mh}</div>
                <div style='font-size: 1.1rem; font-weight: 900; color: #422006; word-break: break-all; line-height: 1.4;'>📝 {memo_mh}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # [미용 파트]
        st.markdown(f"<div class='health-row'><span>✂️ 미용/목욕</span><span class='last-date'>전체최근: {l_gr} {d_gr}</span></div>", unsafe_allow_html=True)
        c3, c4 = st.columns([1.2, 1])
        with c3:
            d_grv = st.date_input("날짜", value=saved_d_gr, key="d_gr")
            if d_grv != saved_d_gr:
                st.session_state.settings["sel_date_gr"] = d_grv.strftime("%Y-%m-%d")
                save_settings(st.session_state.settings)
                st.rerun()
                
            t_grv = st.text_input("메모 (예: 전체미용)", key="t_gr", placeholder="음성/키보드 입력")
            if st.button("✂️ 기록 저장", use_container_width=True):
                add_record(f"✂️ 미용: {t_grv}" if t_grv else "✂️ 미용 및 목욕", f"{d_grv} {ts}")
        with c4:
            date_gr, memo_gr = get_record_for_date("✂️ 미용", d_grv.strftime("%Y-%m-%d"))
            st.markdown(f"""
            <div style='padding: 18px 15px; border-radius: 12px; min-height: 110px; display: flex; flex-direction: column; justify-content: center; border: 2px solid #e2e8f0; margin-bottom: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.05); background-color: #fdf2f8; border-left: 6px solid #f472b6;'>
                <div style='font-size: 0.85rem; font-weight: 900; margin-bottom: 8px; color: #be185d;'>📌 선택일 미용 기록</div>
                <div style='font-size: 1.1rem; font-weight: 900; color: #52525b; margin-bottom: 4px;'>📅 {date_gr}</div>
                <div style='font-size: 1.1rem; font-weight: 900; color: #831843; word-break: break-all; line-height: 1.4;'>📝 {memo_gr}</div>
            </div>
            """, unsafe_allow_html=True) 

def render_manual():
    with st.expander("⚙️ 타이머 수 초 수동 조절 / 리셋"):
        st.info("오늘 날짜를 기준으로 시간을 수정합니다.")
        t1, t2 = st.tabs(["💧 소변", "💩 대변"])
        with t1:
            tw1, tk1 = st.tabs(["⏱️ 휠", "⌨️ 키보드"])
            with tw1:
                p_wheel = st.time_input("시간 선택", now_kst().time(), key="p_wheel")
                if st.button("소변 시간 수정", key="bp_w", use_container_width=True): 
                    add_record(f"💦 소변(수정) [{p_wheel.strftime('%H:%M:%S')}] (통계제외)")
            with tk1:
                p_txt = st.text_input("시간 입력 (HH:MM)", value=now_kst().strftime("%H:%M"), key="p_txt")
                if st.button("소변 시간 수정", key="bp_k", use_container_width=True):
                    try: 
                        vt = datetime.strptime(p_txt, '%H:%M').strftime('%H:%M:00')
                        add_record(f"💦 소변(수정) [{vt}] (통계제외)")
                    except: st.error("HH:MM 형식!")
            if st.button("🔄 소변 타이머 리셋", use_container_width=True, key="bp_r", type="secondary"): add_record("💦 소변 리셋 (통계제외)")
        with t2:
            tw2, tk2 = st.tabs(["⏱️ 휠", "⌨️ 키보드"])
            with tw2:
                d_wheel = st.time_input("시간 선택", now_kst().time(), key="d_wheel")
                if st.button("대변 시간 수정", key="bd_w", use_container_width=True): 
                    add_record(f"💩 대변(수정) [{d_wheel.strftime('%H:%M:%S')}] (통계제외)")
            with tk2:
                d_txt = st.text_input("시간 입력 (HH:MM)", value=now_kst().strftime("%H:%M"), key="d_txt")
                if st.button("대변 시간 수정", key="bd_k", use_container_width=True):
                    try: 
                        vt = datetime.strptime(d_txt, '%H:%M').strftime('%H:%M:00')
                        add_record(f"💩 대변(수정) [{vt}] (통계제외)")
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
    with st.expander(f"📋 오늘 활동 로그 ({len(target_df)}건)", expanded=False):
        search = st.text_input("🔍 검색 (예: 산책, 병원)", key="log_search")
        if target_df.empty: st.info("기록 없음")
        else:
            log_display = target_df.copy()
            if search:
                log_display = log_display[log_display['활동'].str.contains(search, na=False)]
            log_display['시간'] = log_display['시간'].astype(str).str[11:19]
            log_display = log_display.sort_values('시간', ascending=False).reset_index(drop=True)
            log_display.index += 1
            st.dataframe(log_display, use_container_width=True, column_config={"시간": st.column_config.TextColumn("🕐 시간", width="small"), "활동": st.column_config.TextColumn("📝 활동")}) 

def render_stats():
    with st.expander("📊 주간 배변 통계"):
        if df.empty: st.info("데이터 없음")
        else:
            w_dates = [(now_kst() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            w_data = [{"날짜": d[5:], "소변": get_real_count('소변', df[df['시간'].astype(str).str.startswith(d)]), "대변": get_real_count('대변', df[df['시간'].astype(str).str.startswith(d)]), "산책": get_real_count('산책', df[df['시간'].astype(str).str.startswith(d)])} for d in w_dates]
            st.bar_chart(pd.DataFrame(w_data).set_index("날짜"), color=["#22c55e","#f97316","#3b82f6"]) 

# ==========================================
# 🏠 메인 렌더링
# ==========================================
pet_n = st.session_state.profile.get('pet_name','강아지')
last_up = str(df.iloc[-1]['시간'])[:19] if not df.empty else "없음" 

st.markdown(f"""
<div class="header-card">
    <div><div style="font-size:1.4rem; font-weight:900;">🐾 {pet_n} 센터</div><div style="font-size:0.8rem; opacity:0.9;">{now_kst().strftime("%m월 %d일 (%a) %H:%M")}</div></div>
    <div style="text-align:right; font-size:0.75rem; opacity:0.8;"><div>☁️ {last_up}</div><div>{APP_VERSION[:7]} ({UPDATE_DATE[5:]})</div></div>
</div>
""", unsafe_allow_html=True) 

ui_order = st.session_state.settings.get('order', {})
for mod_name, _ in sorted(ui_order.items(), key=lambda x: int(x[1])):
    if mod_name == "타이머": render_timer()
    elif mod_name == "누적데이터": render_summary()
    elif mod_name == "배변기록": render_poo_pee()
    elif mod_name == "산책기록": render_walk()
    elif mod_name == "건강미용": render_health_beauty()
    elif mod_name == "수동조절": render_manual()
    elif mod_name == "기록차감": render_deduct()
    elif mod_name == "활동로그": render_log()
    elif mod_name == "주간통계": render_stats() 

st.divider()
if not target_df.empty:
    last_act = str(target_df.iloc[-1]['활동'])
    last_t   = str(target_df.iloc[-1]['시간'])[11:19]
    if st.button(f"❌ 직전 취소: [{last_t}] {last_act}", use_container_width=True):
        try:
            requests.delete(f"{FIREBASE_URL}users/{username}/logs/{target_df.iloc[-1]['시간']}.json", timeout=5).raise_for_status()
            st.rerun()
        except: st.error("취소 실패") 

st.markdown(f"""
<div style="text-align:center; color:#94a3b8; font-size:0.75rem; padding:10px 0 20px;">
    🐾 Smart Pet Care Center<br>
    현재 버전: <strong>{APP_VERSION}</strong> | 📅 업데이트: {UPDATE_DATE}
</div>
""", unsafe_allow_html=True) 
# END

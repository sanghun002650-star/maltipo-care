import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import requests
import extra_streamlit_components as stx
import time
import threading

# ==========================================
# 0. 기본 설정
# ==========================================
APP_VERSION = "v14.4.0 (취침 DND 모드 & 자정 교차 계산 적용)"
UPDATE_DATE = "2026-04-09"

KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)
FIREBASE_URL = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/" 

st.set_page_config(page_title="🐾 관제 센터", layout="centered", page_icon="🐾", initial_sidebar_state="collapsed") 

# --- 쿠키 매니저 ---
cookie_manager = stx.CookieManager(key="pet_cookie_manager_v14")
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
    <div style='text-align:center; padding: 40px 0 20px;'>
        <div style='font-size:4rem;'>🐾</div>
        <div style='font-size:1.6rem; font-weight:900; color:#1e293b; margin-top:10px;'>Smart Pet Care</div>
        <div style='font-size:0.9rem; color:#64748b; margin-top:4px;'>프리미엄 가족 관제 클라우드</div>
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
                        # 취침 시간 기본값 추가
                        default_settings = {
                            "btn_h": 4.2, "hdr_color": "#64748b", "pee_interval": 5.0,
                            "sleep_start": "22:00", "sleep_end": "05:00",
                            "tg_enabled": True, "tg_token": "8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0", "tg_chat_id": "8124116628",
                            "order": {"타이머":1, "누적데이터":2, "배변기록":3, "산책기록":4, "건강미용":5, "수동조절":6, "기록차감":7, "활동로그":8, "주간통계":9, "가계부":10}
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
        "btn_h": 4.2, "hdr_color": "#64748b", "pee_interval": 5.0,
        "sleep_start": "22:00", "sleep_end": "05:00",
        "tg_enabled": True, "tg_token": "8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0", "tg_chat_id": "8124116628",
        "order": {"타이머":1, "누적데이터":2, "배변기록":3, "산책기록":4, "건강미용":5, "수동조절":6, "기록차감":7, "활동로그":8, "주간통계":9, "가계부":10}
    }
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/settings.json", timeout=5)
        if res.status_code == 200 and res.json():
            loaded = res.json()
            for k in default_settings:
                if k not in loaded: loaded[k] = default_settings[k]
            if "식사건강" in loaded.get("order", {}):
                loaded["order"]["건강미용"] = loaded["order"].pop("식사건강")
            if "가계부" not in loaded.get("order", {}):
                loaded["order"]["가계부"] = 10
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

def load_ledger():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/ledger.json", timeout=5)
        if res.status_code == 200 and res.json():
            records = [{"키": k, "날짜": v.get("date",""), "카테고리": v.get("category",""), "금액": int(v.get("amount", 0)), "메모": v.get("memo","")} for k, v in res.json().items()]
            return pd.DataFrame(records).sort_values("날짜").reset_index(drop=True)
    except: pass
    return pd.DataFrame(columns=["키","날짜","카테고리","금액","메모"])

def add_ledger_entry(date_str, category, amount, memo):
    ts = _unique_ts()
    entry = {"date": date_str, "category": category, "amount": amount, "memo": memo}
    try:
        res = requests.patch(f"{FIREBASE_URL}users/{username}/ledger.json", json={ts: entry}, timeout=5)
        res.raise_for_status()
    except:
        st.error("⚠️ 가계부 저장 실패"); return
    new_row = pd.DataFrame([{"키": ts, "날짜": date_str, "카테고리": category, "금액": amount, "메모": memo}])
    st.session_state.pet_ledger = pd.concat([st.session_state.pet_ledger, new_row], ignore_index=True)
    st.rerun()

def delete_ledger_entry(key):
    try:
        requests.delete(f"{FIREBASE_URL}users/{username}/ledger/{key}.json", timeout=5).raise_for_status()
        st.session_state.pet_ledger = st.session_state.pet_ledger[st.session_state.pet_ledger["키"] != key].reset_index(drop=True)
        st.rerun()
    except:
        st.error("⚠️ 삭제 실패")

if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'settings' not in st.session_state: st.session_state.settings = load_settings()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()
if 'pet_ledger' not in st.session_state: st.session_state.pet_ledger = load_ledger()

# 🚀 텔레그램 백그라운드 모니터링 데몬 (DND 취침 모드 적용)
def send_tg_msg(token, chat_id, text):
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: 
        requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e: 
        pass

# 취침 시간 판별 헬퍼 함수
def is_sleeping_time(now_dt, start_str, end_str):
    try:
        n_m = now_dt.hour * 60 + now_dt.minute
        sh, sm = map(int, start_str.split(':'))
        eh, em = map(int, end_str.split(':'))
        s_m = sh * 60 + sm
        e_m = eh * 60 + em
        
        if s_m <= e_m: # 같은 날 (예: 01:00 ~ 05:00)
            return s_m <= n_m <= e_m
        else: # 자정 교차 (예: 22:00 ~ 05:00)
            return n_m >= s_m or n_m <= e_m
    except: return False

@st.cache_resource
def start_bg_monitor(user_id):
    def job():
        last_alerted_ts = ""
        while True:
            try:
                time.sleep(30)
                s_res = requests.get(f"{FIREBASE_URL}users/{user_id}/settings.json", timeout=5)
                if s_res.status_code != 200 or not s_res.json(): continue
                settings = s_res.json()
                
                if not settings.get("tg_enabled") or not settings.get("tg_token") or not settings.get("tg_chat_id"): 
                    continue
                
                now_tz = datetime.now(timezone(timedelta(hours=9)))
                s_start = settings.get("sleep_start", "22:00")
                s_end = settings.get("sleep_end", "05:00")
                
                # 🌙 현재가 취침 시간대라면 알람 스레드는 무시(Pass)
                if is_sleeping_time(now_tz, s_start, s_end):
                    continue
                
                interval_h = float(settings.get("pee_interval", 5.0))
                
                l_res = requests.get(f"{FIREBASE_URL}users/{user_id}/logs.json", timeout=5)
                if l_res.status_code != 200 or not l_res.json(): continue
                logs = l_res.json()
                
                p_ts = ""
                for k in sorted(logs.keys(), reverse=True):
                    act = str(logs[k])
                    if "소변" in act and not any(x in act for x in ["차감", "리셋", "끄기", "알림 발송"]):
                        if '(수정)' in act and '[' in act and ']' in act:
                            try:
                                ext_time = act.split('[')[1].split(']')[0]
                                date_part = k.split(' ')[0]
                                p_ts = f"{date_part} {ext_time}"
                            except: p_ts = k.split('_')[0]
                        else: p_ts = k.split('_')[0]
                        break
                
                if p_ts and p_ts != last_alerted_ts:
                    diff_h = (now_tz - datetime.strptime(p_ts, "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600.0
                    if diff_h >= interval_h:
                        h = int(diff_h)
                        m = int((diff_h * 60) % 60)
                        pet_name = settings.get("pet_name", "강아지")
                        time_str = f"{h}시간 {m}분" if h > 0 else f"{m}분"
                        msg = f"🚨 [Smart Pet Care] {pet_name} 소변 알람!\n\n마지막 소변 후 {time_str}이 경과했습니다.\n아이의 상태를 확인해 주세요!"
                        
                        send_tg_msg(settings["tg_token"], settings["tg_chat_id"], msg)
                        last_alerted_ts = p_ts 
                        
                        try:
                            alert_ts = now_tz.strftime("%Y-%m-%d %H:%M:%S_%f")
                            alert_act = f"📱 알림 발송 (소변 후 {time_str} 초과)"
                            requests.patch(f"{FIREBASE_URL}users/{user_id}/logs.json", json={alert_ts: alert_act}, timeout=5)
                        except: pass

            except Exception: pass 
    t = threading.Thread(target=job, daemon=True)
    t.start()
    return t

start_bg_monitor(username)

# ==========================================
# 🎨 프리미엄 UI / 동적 CSS 인젝션
# ==========================================
DYNAMIC_BTN_H = st.session_state.settings.get("btn_h", 4.0)
DYNAMIC_HDR_COLOR = st.session_state.settings.get("hdr_color", "#475569")

st.markdown(f"""
<style>
.stApp {{ background-color: #f8fafc !important; }}
.block-container {{ padding: 1.5rem 1rem 6rem 1rem !important; max-width: 550px !important; }}
::-webkit-scrollbar {{ width: 0px; }} 

.header-card {{
    display:flex; justify-content:space-between; align-items:center; 
    background:linear-gradient(135deg, #f0f9ff, #e0f2fe); 
    border-radius:24px; 
    padding: 30px 25px 25px 25px; 
    margin-bottom:20px; color:#0f172a;
    min-height: 95px; line-height: 1.4; 
    box-shadow: 0 10px 30px rgba(149, 157, 165, 0.15);
}} 

div[data-testid="stExpander"] {{
    background-color: #ffffff !important;
    border: none !important;
    border-radius: 20px !important;
    box-shadow: 0 8px 24px rgba(149, 157, 165, 0.08) !important;
    margin-bottom: 18px !important;
    overflow: hidden !important;
}}
div[data-testid="stExpander"] details {{ border: none !important; }}

div.stButton > button {{
    height: {DYNAMIC_BTN_H}rem !important;
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 18px !important; 
    font-weight: 800 !important; 
    font-size: 1.05rem !important;
    color: #334155 !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important; 
    transition: all 0.2s ease !important;
}} 
div.stButton > button:active {{
    transform: scale(0.97) !important;
    background-color: #f1f5f9 !important;
}}

/* 🚨 [중요] 차트 툴팁 잔상 방지 패치 🚨 */
#vg-tooltip-element, .vg-tooltip, .vega-bindings {{ display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important; }}
canvas {{ pointer-events: none !important; }}

.section-header {{ font-size: 0.9rem; font-weight: 800; color: {DYNAMIC_HDR_COLOR}; letter-spacing: 0.5px; margin: 15px 0 12px 5px; }} 
.health-row {{ display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 12px 18px; border-radius: 14px; margin-bottom: 10px; border: 1px solid #f1f5f9; }}
.last-date {{ font-size: 0.75rem; color: #64748b; font-weight: 700; text-align: right; }}
.d-day-badge {{ background: #e2e8f0; color: #334155; padding: 4px 8px; border-radius: 8px; font-size: 0.75rem; margin-left: 8px; font-weight: 800; }} 
.stTabs [data-baseweb="tab-list"] {{ gap: 20px !important; justify-content: center !important; }}
.stTabs [data-baseweb="tab"] {{ height: 3.2rem !important; font-weight: 800 !important; padding: 0 15px !important; }}
hr {{ margin: 15px 0 !important; border-color: #f1f5f9 !important; }}
.streamlit-expanderHeader {{ font-weight: 800 !important; font-size: 1rem !important; color: #1e293b !important; padding: 15px 20px !important; }} 
.save-btn-col button {{ height: 2.8rem !important; padding: 0 !important; font-size: 0.95rem !important; background-color: #f1f5f9 !important; }}
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

    with st.expander("📱 텔레그램 알림 설정", expanded=False):
        tg_enabled = st.checkbox("백그라운드 텔레그램 알람 켜기", value=st.session_state.settings.get('tg_enabled', True))
        tg_token = st.text_input("Bot Token", value=st.session_state.settings.get('tg_token', '8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0'))
        tg_chat_id = st.text_input("Chat ID", value=st.session_state.settings.get('tg_chat_id', '8124116628'))
        if st.button("텔레그램 설정 저장", use_container_width=True, type="primary"):
            st.session_state.settings.update({'tg_enabled': tg_enabled, 'tg_token': tg_token, 'tg_chat_id': tg_chat_id})
            save_settings(st.session_state.settings)
            st.success("텔레그램 설정 저장됨!")
            st.rerun()
    
    with st.expander("⏰ 소변 알람 및 취침 설정", expanded=False):
        st.markdown("<div style='font-size:0.85rem; font-weight:800; color:#475569; margin-bottom:5px;'>소변 알람 간격 (시간 단위)</div>", unsafe_allow_html=True)
        col1, col2 = st.columns([7, 3])
        with col1:
            new_interval = st.number_input("간격(시간)", min_value=0.5, max_value=24.0, value=float(st.session_state.settings.get('pee_interval', 5.0)), step=0.5, label_visibility="collapsed")
        
        st.markdown("<div style='font-size:0.85rem; font-weight:800; color:#475569; margin: 15px 0 5px 0;'>🌙 강아지 취침 시간 (알람 무음)</div>", unsafe_allow_html=True)
        def_start = datetime.strptime(st.session_state.settings.get('sleep_start', '22:00'), "%H:%M").time()
        def_end = datetime.strptime(st.session_state.settings.get('sleep_end', '05:00'), "%H:%M").time()
        c_s, c_e = st.columns(2)
        with c_s: new_s_start = st.time_input("시작", value=def_start)
        with c_e: new_s_end = st.time_input("종료", value=def_end)

        if st.button("⏰ 시간/취침 설정 저장", key="btn_save_int", use_container_width=True, type="primary"):
            st.session_state.settings['pee_interval'] = new_interval
            st.session_state.settings['sleep_start'] = new_s_start.strftime("%H:%M")
            st.session_state.settings['sleep_end'] = new_s_end.strftime("%H:%M")
            save_settings(st.session_state.settings)
            st.rerun()
    
    with st.expander("🎨 화면 테마 및 배치 순서 설정", expanded=False):
        new_btn_h = st.slider("버튼 높이", 3.0, 6.0, float(st.session_state.settings.get('btn_h', 4.0)), 0.1)
        new_hdr_c = st.color_picker("섹션 헤더 색상", st.session_state.settings.get('hdr_color', '#475569'))
        st.markdown("<div style='font-size:0.85rem; font-weight:800; color:#475569; margin: 10px 0 5px 0;'>메뉴 배치 순서</div>", unsafe_allow_html=True)
        new_order = {}
        order_items = list(st.session_state.settings.get('order', {}).items())
        c1, c2 = st.columns(2)
        for i, (k, v) in enumerate(order_items):
            if i % 2 == 0:
                with c1: new_order[k] = st.number_input(k, min_value=1, max_value=20, value=int(v), step=1)
            else:
                with c2: new_order[k] = st.number_input(k, min_value=1, max_value=20, value=int(v), step=1)
        if st.button("UI/배치 설정 저장", use_container_width=True, type="primary"):
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

    ldg_data = st.session_state.pet_ledger
    cur_month_str = now_kst().strftime("%Y-%m")
    if not ldg_data.empty:
        monthly_total_val = int(ldg_data[ldg_data["날짜"].astype(str).str.startswith(cur_month_str)]["금액"].sum())
    else:
        monthly_total_val = 0
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #ffffff, #f1f5f9); border: 1px solid #e2e8f0; border-radius: 20px; padding: 18px; margin-top: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.04);'>
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
            <span style='font-size: 1.2rem;'>💰</span>
            <span style='font-size: 0.95rem; font-weight: 800; color: #64748b;'>{now_kst().strftime("%m월")} 총지출</span>
        </div>
        <div style='font-size: 1.4rem; font-weight: 900; color: #1e293b; letter-spacing: -0.5px;'>
            {monthly_total_val:,}<span style='font-size: 1rem; margin-left: 2px;'>원</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 📊 데이터 헬퍼 (수동 시간 동기화 패치 적용)
# ==========================================
t_date = now_kst().strftime("%Y-%m-%d")
df = st.session_state.pet_logs
target_df = df[df['시간'].astype(str).str.startswith(t_date, na=False)].copy() if not df.empty else pd.DataFrame(columns=["시간","활동"])

def get_event_time(kw):
    if df.empty: return None, ""
    for i in range(len(df)-1, -1, -1):
        act = str(df.iloc[i]['활동'])
        t = str(df.iloc[i]['시간'])
        if kw in act:
            if any(x in act for x in ['차감', '리셋', '끄기', '알림']): continue
            if '(수정)' in act and '[' in act and ']' in act:
                try:
                    ext_time = act.split('[')[1].split(']')[0]
                    date_part = t.split(' ')[0]
                    return f"{date_part} {ext_time}", act
                except: pass
            return t.split('_')[0], act
    return None, ""

def get_real_count(keyword, check_df):
    if check_df.empty: return 0
    plus, minus = 0, 0
    for act in check_df['활동'].astype(str):
        if keyword in act:
            if '차감' in act: minus += 1
            elif any(x in act for x in ['리셋','끄기','통계제외', '알림']): pass
            else: plus += 1
    return max(0, plus - minus)

def get_d_day_info(keyword):
    if df.empty: return "기록 없음", "", "기록 없음"
    matches = df[df['활동'].str.contains(keyword, na=False)].copy()
    if matches.empty: return "기록 없음", "", "기록 없음"
    matches = matches.sort_values(by='시간', ascending=True)
    last_record = matches.iloc[-1]
    last_dt_str = str(last_record['시간'])[:10]
    last_act = str(last_record['활동'])
    memo = last_act.split(":", 1)[1].strip() if ":" in last_act else last_act
    last_dt = datetime.strptime(last_dt_str, "%Y-%m-%d").date()
    diff = (now_kst().date() - last_dt).days
    d_day_str = f"<span class='d-day-badge'>{diff}일 경과</span>" if diff > 0 else "<span class='d-day-badge'>오늘 완료</span>"
    return last_dt_str, d_day_str, memo

def get_record_for_date(keyword, target_date_str):
    if df.empty: return target_date_str, "해당 날짜 기록 없음"
    matches = df[df['시간'].astype(str).str.startswith(target_date_str) & df['활동'].str.contains(keyword, na=False)].copy()
    if matches.empty: return target_date_str, "해당 날짜 기록 없음"
    matches = matches.sort_values(by='시간', ascending=True)
    last_act = str(matches.iloc[-1]['활동'])
    memo = last_act.split(":", 1)[1].strip() if ":" in last_act else last_act
    return target_date_str, memo

# 타이머 구동을 위한 최신 시간 변수 할당
p_time_raw, _ = get_event_time("소변")
a_time_raw, _ = get_event_time("알림 발송")
d_time_raw, _ = get_event_time("대변")

# 소변 예상 로직 및 상태 연동
p_disp = p_time_raw[11:16] if p_time_raw else "--:--"
p_expect = "--:--"
msg_status = "대기 중"
msg_color = "#64748b"
p_iso = ""

if p_time_raw:
    p_dt = datetime.strptime(p_time_raw, "%Y-%m-%d %H:%M:%S")
    p_iso = p_dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    intv = float(st.session_state.settings.get("pee_interval", 5.0))
    expect_dt = p_dt + timedelta(hours=intv)
    p_expect = expect_dt.strftime("%H:%M")
    
    if a_time_raw and a_time_raw > p_time_raw:
        msg_status = f"발송 완료 ({a_time_raw[11:16]})"
        msg_color = "#10b981"
    else:
        msg_status = "대기 중"
        msg_color = "#f59e0b"

d_disp = d_time_raw[11:16] if d_time_raw else "--:--"
d_iso = d_time_raw.replace(" ","T")+"+09:00" if d_time_raw else ""

s_start = st.session_state.settings.get('sleep_start', '22:00')
s_end = st.session_state.settings.get('sleep_end', '05:00')

# ==========================================
# 🧱 타이머 렌더링 (원형 게이지 + 3:2 배치 + 취침 모드 시각화)
# ==========================================
def render_timer():
    intv_h = float(st.session_state.settings.get("pee_interval", 5.0))
    ALARM_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

    components.html(f"""
    <div style="display:flex; flex-direction:row; gap:15px; font-family:'Malgun Gothic', sans-serif; width: 100%;">
        
        <div id="p_card" style="flex:3; background:#ffffff; border-radius:24px; padding:15px 10px; box-shadow:0 8px 24px rgba(149,157,165,0.08); transition:all 0.5s ease; display:flex; flex-direction:column;">
            <div id="p_title" style="font-size:0.95rem; font-weight:800; color:#0284c7; text-align:center; margin-bottom:10px;">💧 소변 타이머</div>
            
            <div style="display:flex; align-items:center; justify-content:space-evenly; flex:1;">
                <div style="position:relative; width:90px; height:90px;">
                    <svg viewBox="0 0 36 36" style="width:100%; height:100%;">
                        <path d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#f0f9ff" stroke-width="2.5" />
                        <path id="p_circ" d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#38bdf8" stroke-width="3" stroke-dasharray="0, 100" stroke-linecap="round" style="transition: stroke-dasharray 1s ease-out;" />
                    </svg>
                    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width: 100%; text-align:center;">
                        <div id="p_rem_label" style="font-size:0.65rem; font-weight:700; color:#64748b;">남은 시간</div>
                        <div id="p_rem" style="font-size:1.15rem; font-weight:900; color:#0369a1; line-height:1.2;">--:--</div>
                    </div>
                </div>
                
                <div style="border-left: 2px dashed #f1f5f9; padding-left: 12px; display:flex; flex-direction:column; gap:4px; font-size:0.85rem;">
                    <div><span style="color:#64748b;">최근</span> <b style="float:right; color:#334155;">{p_disp}</b></div>
                    <div><span style="color:#0284c7;">예상</span> <b style="float:right; color:#0284c7;">{p_expect}</b></div>
                    <div style="font-size:0.65rem; color:#94a3b8; text-align:right;">(간격 {intv_h}H)</div>
                    <div style="margin-top:2px; font-size:0.75rem; font-weight:800; color:{msg_color}; background:#f8fafc; padding:3px 6px; border-radius:4px; text-align:center;">{msg_status}</div>
                </div>
            </div>
        </div>

        <div id="d_card" style="flex:2; background:#ffffff; border-radius:24px; padding:15px 10px; text-align:center; box-shadow:0 8px 24px rgba(149,157,165,0.08); display:flex; flex-direction:column; justify-content:space-between;">
            <div style="font-size:0.95rem; font-weight:800; color:#c2410c; margin-bottom:5px;">💩 대변 타이머</div>
            <div style="position:relative; width:80px; height:80px; margin:0 auto;">
                <svg viewBox="0 0 36 36" style="width:100%; height:100%;">
                    <path d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#fff7ed" stroke-width="2.5" />
                    <path id="d_circ" d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#fb923c" stroke-width="3" stroke-dasharray="0, 100" stroke-linecap="round" style="transition: stroke-dasharray 1s ease-out;" />
                </svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
                    <div style="font-size:0.6rem; font-weight:700; color:#64748b;">경과</div>
                    <div id="d_elap" style="font-size:1.0rem; font-weight:900; color:#9a3412;">--:--</div>
                </div>
            </div>
            <div style="font-size:0.75rem; color:#64748b; font-weight:700;">최근 발생: {d_disp}</div>
        </div>

    </div>
    <audio id="alarm_sound" src="{ALARM_URL}" preload="auto"></audio>

    <script>
        const P_LIMIT = {intv_h} * 3600000; 
        const D_MAX_MS = 43200000; 
        const s_start = "{s_start}";
        const s_end = "{s_end}";
        let isAlarmed = false;

        function isSleeping(now) {{
            const n_m = now.getHours() * 60 + now.getMinutes();
            const s_arr = s_start.split(':');
            const e_arr = s_end.split(':');
            const sm = parseInt(s_arr[0]) * 60 + parseInt(s_arr[1]);
            const em = parseInt(e_arr[0]) * 60 + parseInt(e_arr[1]);
            
            if (sm <= em) {{ return n_m >= sm && n_m <= em; }} 
            else {{ return n_m >= sm || n_m <= em; }} // 자정 교차
        }}

        function update() {{ 
            const now = new Date();
            const p_rem = document.getElementById('p_rem');
            const p_rem_lbl = document.getElementById('p_rem_label');
            const p_circ = document.getElementById('p_circ');
            const p_card = document.getElementById('p_card');
            const p_title = document.getElementById('p_title');
            const audio = document.getElementById('alarm_sound');
            const p_iso = "{p_iso}"; 
            
            // 🌙 취침 모드 시각화 처리
            if (isSleeping(now)) {{
                p_card.style.background = "#f8fafc"; // 차분한 배경
                p_title.innerText = "🌙 소변 타이머 (취침 중)";
                p_title.style.color = "#64748b";
                p_rem_lbl.innerText = "알람 끔";
                p_rem.innerText = "Zzz";
                p_rem.style.color = "#94a3b8";
                p_circ.setAttribute('stroke-dasharray', '0, 100'); // 게이지 멈춤
            }} else {{
                p_title.innerText = "💧 소변 타이머";
                p_title.style.color = "#0284c7";
                p_rem_lbl.innerText = "남은 시간";
                
                if(p_iso) {{
                    const diff = now - new Date(p_iso);
                    if(diff >= 0) {{
                        const rem = P_LIMIT - diff;
                        const r_abs = Math.abs(rem);
                        const r_h = Math.floor(r_abs/3600000), r_m = Math.floor((r_abs%3600000)/60000);
                        
                        if (rem > 0) {{
                            p_rem.innerText = String(r_h).padStart(2,'0') + ":" + String(r_m).padStart(2,'0');
                            p_rem.style.color = "#0369a1"; p_card.style.background = "#ffffff"; isAlarmed = false;
                        }} else {{
                            p_rem.innerText = "-" + String(r_h).padStart(2,'0') + ":" + String(r_m).padStart(2,'0');
                            p_rem.style.color = "#ef4444"; p_card.style.background = "#fff1f2";
                            if(!isAlarmed) {{ audio.play().catch(e => console.log(e)); isAlarmed = true; }}
                        }}
                        p_circ.setAttribute('stroke-dasharray', Math.min((diff/P_LIMIT)*100, 100) + ', 100');
                    }}
                }}
            }}

            const d_el = document.getElementById('d_elap'), d_circ = document.getElementById('d_circ'), d_iso = "{d_iso}";
            if(d_iso) {{
                const diff = now - new Date(d_iso);
                if(diff >= 0) {{
                    const d_h = Math.floor(diff/3600000), d_m = Math.floor((diff%3600000)/60000);
                    d_el.innerText = String(d_h).padStart(2,'0') + ":" + String(d_m).padStart(2,'0');
                    d_circ.setAttribute('stroke-dasharray', Math.min((diff/D_MAX_MS)*100, 100) + ', 100');
                }}
            }}
        }}
        setInterval(update, 1000); update();
    </script>
    """, height=185)

def render_summary():
    p, d, w = get_real_count('소변', target_df), get_real_count('대변', target_df), get_real_count('산책', target_df)
    st.markdown(f"""
    <div style="background:#ffffff; border-radius:24px; padding:25px 20px; box-shadow:0 8px 24px rgba(149,157,165,0.08); margin-bottom:20px;">
        <div style="font-size:0.9rem; font-weight:800; color:#475569; letter-spacing:0.5px; margin-bottom:18px;">✨ 오늘의 달성 현황</div>
        <div style="display: flex; flex-direction: row; justify-content: space-between; gap: 10px; width: 100%;">
            <div style="flex: 1; border-radius: 18px; padding: 15px 5px; text-align: center; border: 1px solid transparent; background: #f0f9ff; border-color: #e0f2fe;">
                <div style="font-size: 0.8rem; font-weight: 800; margin-bottom: 6px; color: #0284c7;">💧 소변</div>
                <div style="font-size: 1.8rem; font-weight: 900; line-height: 1.1; color: #0369a1;">{p}회</div>
            </div>
            <div style="flex: 1; border-radius: 18px; padding: 15px 5px; text-align: center; border: 1px solid transparent; background: #fff7ed; border-color: #ffedd5;">
                <div style="font-size: 0.8rem; font-weight: 800; margin-bottom: 6px; color: #c2410c;">💩 대변</div>
                <div style="font-size: 1.8rem; font-weight: 900; line-height: 1.1; color: #9a3412;">{d}회</div>
            </div>
            <div style="flex: 1; border-radius: 18px; padding: 15px 5px; text-align: center; border: 1px solid transparent; background: #ecfccb; border-color: #d9f99d;">
                <div style="font-size: 0.8rem; font-weight: 800; margin-bottom: 6px; color: #4d7c0f;">🐾 산책</div>
                <div style="font-size: 1.8rem; font-weight: 900; line-height: 1.1; color: #3f6212;">{w}회</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_poo_pee():
    st.markdown("<div class='section-header'>🚨 실내 배변</div>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💧 실내 소변", use_container_width=True): add_record("💦 집에서 소변")
    with b2:
        if st.button("💩 실내 대변", use_container_width=True): add_record("💩 집에서 대변")

def render_walk():
    st.markdown("<div class='section-header'>🌳 야외 산책</div>", unsafe_allow_html=True)
    w1, w2 = st.columns(2)
    with w1:
        if st.button("🐾 일반 산책", use_container_width=True): add_record("🦮 일반 산책")
    with w2:
        if st.button("🐾+💧 산책 소변", use_container_width=True): add_record("🦮+💦 산책 중 소변")
    w3, w4 = st.columns(2)
    with w3:
        if st.button("🐾+💩 산책 대변", use_container_width=True): add_record("🦮+💩 산책 중 대변")
    with w4:
        if st.button("🌟 모두 해결", use_container_width=True): add_record("🦮+💦+💩 산책 중 소변과 대변")

def render_health_beauty():
    st.markdown("<div class='section-header'>🏥 건강 / 미용</div>", unsafe_allow_html=True)
    l_mh, d_mh, _ = get_d_day_info("🏥 병원/약")
    l_gr, d_gr, _ = get_d_day_info("✂️ 미용") 
    with st.expander("✨ 상세 기록 관리 (약/병원/미용 메모)", expanded=False):
        ts = now_kst().strftime("%H:%M:%S_%f")
        saved_d_mh_str = st.session_state.settings.get("sel_date_mh", now_kst().strftime("%Y-%m-%d"))
        saved_d_gr_str = st.session_state.settings.get("sel_date_gr", now_kst().strftime("%Y-%m-%d"))
        saved_d_mh = datetime.strptime(saved_d_mh_str, "%Y-%m-%d").date()
        saved_d_gr = datetime.strptime(saved_d_gr_str, "%Y-%m-%d").date()
        st.markdown(f"<div class='health-row'><span>🏥 병원/약</span><span class='last-date'>전체최근: {l_mh} {d_mh}</span></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1.2, 1])
        with c1:
            d_val = st.date_input("날짜", value=saved_d_mh, key="d_mh")
            if d_val != saved_d_mh:
                st.session_state.settings["sel_date_mh"] = d_val.strftime("%Y-%m-%d")
                save_settings(st.session_state.settings); st.rerun()
            t_val = st.text_input("메모", key="t_mh", placeholder="예: 심장사상충")
            if st.button("🏥 기록 저장", use_container_width=True):
                add_record(f"🏥 병원/약: {t_val}" if t_val else "🏥 병원/약", f"{d_val} {ts}")
        with c2:
            date_mh, memo_mh = get_record_for_date("🏥 병원/약", d_val.strftime("%Y-%m-%d"))
            st.markdown(f"<div style='padding:18px 15px; border-radius:16px; min-height:110px; background-color:#fefce8; border-left:6px solid #facc15;'><div style='font-size:0.85rem; font-weight:900; margin-bottom:8px; color:#a16207;'>📌 선택일 진료</div><div style='font-size:1.1rem; font-weight:900; color:#52525b;'>📅 {date_mh}</div><div style='font-size:1.1rem; font-weight:900; color:#422006;'>📝 {memo_mh}</div></div>", unsafe_allow_html=True)
        st.divider()
        st.markdown(f"<div class='health-row'><span>✂️ 미용/목욕</span><span class='last-date'>전체최근: {l_gr} {d_gr}</span></div>", unsafe_allow_html=True)
        c3, c4 = st.columns([1.2, 1])
        with c3:
            d_grv = st.date_input("날짜", value=saved_d_gr, key="d_gr")
            if d_grv != saved_d_gr:
                st.session_state.settings["sel_date_gr"] = d_grv.strftime("%Y-%m-%d")
                save_settings(st.session_state.settings); st.rerun()
            t_grv = st.text_input("메모", key="t_gr", placeholder="예: 전체미용")
            if st.button("✂️ 기록 저장", use_container_width=True):
                add_record(f"✂️ 미용: {t_grv}" if t_grv else "✂️ 미용 및 목욕", f"{d_grv} {ts}")
        with c4:
            date_gr, memo_gr = get_record_for_date("✂️ 미용", d_grv.strftime("%Y-%m-%d"))
            st.markdown(f"<div style='padding:18px 15px; border-radius:16px; min-height:110px; background-color:#fdf2f8; border-left:6px solid #f472b6;'><div style='font-size:0.85rem; font-weight:900; margin-bottom:8px; color:#be185d;'>📌 선택일 미용</div><div style='font-size:1.1rem; font-weight:900; color:#52525b;'>📅 {date_gr}</div><div style='font-size:1.1rem; font-weight:900; color:#831843;'>📝 {memo_gr}</div></div>", unsafe_allow_html=True)

def render_manual():
    with st.expander("⚙️ 타이머 수동 조절"):
        t1, t2 = st.tabs(["💧 소변", "💩 대변"])
        with t1:
            p_wheel = st.time_input("시간 선택", now_kst().time(), key="p_wheel")
            if st.button("시간 저장", key="bp_w", use_container_width=True): add_record(f"💦 소변(수정) [{p_wheel.strftime('%H:%M:%S')}] (통계제외)")
            if st.button("🔄 리셋", use_container_width=True, key="bp_r"): add_record("💦 소변 리셋 (통계제외)")
        with t2:
            d_wheel = st.time_input("시간 선택", now_kst().time(), key="d_wheel")
            if st.button("시간 저장", key="bd_w", use_container_width=True): add_record(f"💩 대변(수정) [{d_wheel.strftime('%H:%M:%S')}] (통계제외)")
            if st.button("🔄 리셋", use_container_width=True, key="bd_r"): add_record("💩 대변 리셋 (통계제외)")

def render_deduct():
    with st.expander("➖ 잘못 누른 기록 차감"):
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("💧 -1", use_container_width=True): add_record("💦 소변 차감 (-1)")
        with a2:
            if st.button("💩 -1", use_container_width=True): add_record("💩 대변 차감 (-1)")
        with a3:
            if st.button("🐾 -1", use_container_width=True): add_record("🦮 산책 차감 (-1)")

def render_log():
    with st.expander(f"📋 활동 로그 ({len(target_df)}건)", expanded=False):
        search = st.text_input("🔍 검색", key="log_search")
        if not target_df.empty:
            log_display = target_df.copy()
            if search: log_display = log_display[log_display['활동'].str.contains(search, na=False)]
            log_display['시간'] = log_display['시간'].astype(str).str[11:19]
            log_display = log_display.sort_values('시간', ascending=False).reset_index(drop=True)
            log_display.index += 1
            st.dataframe(log_display, use_container_width=True)

def render_ledger():
    with st.expander("💰 반려견 가계부 (상세)", expanded=False):
        CATS = ["사료", "간식", "배변패드", "의료비", "기타"]
        ldg = st.session_state.pet_ledger
        cur_month = now_kst().strftime("%Y-%m")
        monthly_ldg = ldg[ldg["날짜"].astype(str).str.startswith(cur_month)].copy() if not ldg.empty else pd.DataFrame()
        total = int(monthly_ldg["금액"].sum()) if not monthly_ldg.empty else 0
        st.markdown(f"<div style='background:#1e293b; border-radius:15px; padding:15px; color:white; text-align:center; margin-bottom:15px;'><strong>{now_kst().strftime('%m월')} 합계: {total:,}원</strong></div>", unsafe_allow_html=True)
        lc1, lc2 = st.columns(2)
        with lc1:
            l_date = st.date_input("날짜", value=now_kst().date(), key="l_date")
            l_cat = st.selectbox("카테고리", CATS, key="l_cat")
        with lc2:
            l_amt = st.number_input("금액", min_value=0, step=1000, key="l_amt")
            l_memo = st.text_input("메모", key="l_memo")
        if st.button("💾 지출 저장", use_container_width=True, type="primary"):
            if l_amt > 0: add_ledger_entry(l_date.strftime("%Y-%m-%d"), l_cat, int(l_amt), l_memo)
        if not monthly_ldg.empty:
            st.dataframe(monthly_ldg[["날짜","카테고리","금액","메모"]].sort_values("날짜", ascending=False), use_container_width=True)
            last_row = monthly_ldg.sort_values("날짜", ascending=False).iloc[0]
            if st.button(f"❌ 직전 삭제: {last_row['카테고리']} {int(last_row['금액']):,}원", use_container_width=True):
                delete_ledger_entry(str(last_row["키"]))

def render_stats():
    with st.expander("📊 주간 통계", expanded=False):
        if not df.empty:
            w_dates = [(now_kst() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            w_data = [{"날짜": d[5:], "소변": get_real_count('소변', df[df['시간'].astype(str).str.startswith(d)]), "대변": get_real_count('대변', df[df['시간'].astype(str).str.startswith(d)]), "산책": get_real_count('산책', df[df['시간'].astype(str).str.startswith(d)])} for d in w_dates]
            st.bar_chart(pd.DataFrame(w_data).set_index("날짜"), color=["#bae6fd","#fed7aa","#d9f99d"])

# ==========================================
# 🏠 메인 렌더링
# ==========================================
pet_n = st.session_state.profile.get('pet_name','강아지')
last_up = str(df.iloc[-1]['시간'])[:19] if not df.empty else "없음"

st.markdown(f"""
<div class="header-card">
    <div>
        <div style="font-size:1.6rem; font-weight:900; margin-bottom:5px; color:#0f172a;">🐾 {pet_n} 센터</div>
        <div style="font-size:0.85rem; font-weight:700; color:#475569;">{now_kst().strftime("%m월 %d일 (%a) %H:%M")}</div>
    </div>
    <div style="text-align:right; font-size:0.75rem; color:#64748b; font-weight:600;">
        <div style="margin-bottom:5px;">☁️ {last_up}</div>
        <div>{APP_VERSION[:7]}</div>
    </div>
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
    elif mod_name == "가계부": render_ledger()

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
<div style="text-align:center; color:#94a3b8; font-size:0.75rem; padding:20px 0 30px; font-weight:600;">
    🐾 Smart Pet Care Center<br>
    현재 버전: <strong>{APP_VERSION}</strong> | 업데이트: {UPDATE_DATE}
</div>
""", unsafe_allow_html=True)

# END

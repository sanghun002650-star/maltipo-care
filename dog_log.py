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
APP_VERSION = "v14.9.2 (암호화 롤백 & v14.9.1 기능 완전 보존)"
UPDATE_DATE = "2026-04-12"

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
# 🚪 로그인 화면 (암호화 제거 / 평문 대조 롤백)
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
        if st.button("접속하기 🚀", use_container_width=True, type="primary"):
            try:
                # [복구 포인트 1] 평문 비밀번호 대조
                res = requests.get(f"{FIREBASE_URL}users/{login_id}/password.json", timeout=5)
                if res.status_code == 200 and res.json() == login_pw:
                    cookie_manager.set("saved_username", login_id, expires_at=datetime.now() + timedelta(days=180))
                    st.session_state.force_logout = False
                    st.session_state.logged_in = True
                    st.session_state.username = login_id
                    st.rerun()
                else: st.error("❌ 아이디 또는 비밀번호가 틀렸습니다.")
            except: st.error("⚠️ 네트워크 오류. 인터넷 연결을 확인해주세요.")
                
    with tab2:
        reg_id = st.text_input("아이디", key="r_id", placeholder="사용할 아이디")
        reg_pw = st.text_input("비밀번호", type="password", key="r_pw", placeholder="비밀번호")
        if st.button("계정 생성 💾", use_container_width=True):
            if reg_id and reg_pw:
                try:
                    res = requests.get(f"{FIREBASE_URL}users/{reg_id}.json", timeout=5)
                    if res.status_code == 200 and res.json() is not None: st.error("❌ 이미 존재하는 아이디입니다.")
                    else:
                        # [복구 포인트 2] 비밀번호 평문 저장 (암호화 X)
                        requests.put(f"{FIREBASE_URL}users/{reg_id}/password.json", json=reg_pw, timeout=5)
                        requests.put(f"{FIREBASE_URL}users/{reg_id}/profile.json", json={"pet_name": "강아지", "birth": "", "weight": "", "gender": "수컷", "memo": ""}, timeout=5)
                        requests.put(f"{FIREBASE_URL}users/{reg_id}/settings.json", json={"btn_h": 4.2, "hdr_color": "#64748b", "pee_interval": 5.0, "meal_interval": 8.0, "sleep_start": "22:00", "sleep_end": "05:00", "tg_enabled": True, "tg_token": "8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0", "tg_chat_id": "8124116628", "order": {"타이머":1, "누적데이터":2, "배변기록":3, "식사기록":4, "산책기록":5, "건강미용":6, "수동조절":7, "기록차감":8, "활동로그":9, "주간통계":10, "가계부":11}}, timeout=5)
                        st.success("✅ 계정 생성 완료! 로그인 탭에서 접속하세요.")
                except requests.exceptions.RequestException: st.error("⚠️ 네트워크 오류.")
            else: st.warning("모든 항목을 입력하세요.")
    st.stop()

# ==========================================
# ☁️ 클라우드 엔진 & 핵심 무결성 파서 로직
# ==========================================
username = st.session_state.username

def _unique_ts(base_time=None):
    return (base_time if base_time else now_kst()).strftime("%Y-%m-%d %H:%M:%S_%f")

def load_profile():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/profile.json", timeout=5)
        if res.status_code == 200 and res.json(): return res.json()
    except: pass
    return {"pet_name": "강아지", "birth": "", "weight": "", "gender": "수컷", "memo": ""}

def load_settings():
    def_s = {
        "btn_h": 4.2, "hdr_color": "#64748b", "pee_interval": 5.0, "meal_interval": 8.0, 
        "sleep_start": "22:00", "sleep_end": "05:00", 
        "tg_enabled": True, "tg_token": "8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0", "tg_chat_id": "8124116628", 
        "order": {"타이머":1, "누적데이터":2, "배변기록":3, "식사기록":4, "산책기록":5, "건강미용":6, "수동조절":7, "기록차감":8, "활동로그":9, "주간통계":10, "가계부":11}
    }
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/settings.json", timeout=5)
        if res.status_code == 200 and res.json():
            loaded = res.json()
            for k in def_s:
                if k not in loaded: loaded[k] = def_s[k]
            return loaded
    except: pass
    return def_s

def save_profile(p):
    try: requests.put(f"{FIREBASE_URL}users/{username}/profile.json", json=p, timeout=5)
    except: pass

def save_settings(s):
    try: requests.put(f"{FIREBASE_URL}users/{username}/settings.json", json=s, timeout=5)
    except: pass

def load_data():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/logs.json", timeout=5)
        if res.status_code == 200 and res.json():
            return pd.DataFrame([{"시간": k, "활동": v} for k, v in res.json().items()]).sort_values("시간").reset_index(drop=True)
    except: pass
    return pd.DataFrame(columns=["시간", "활동"])

def add_record(act, c_time=None):
    t = c_time if c_time else _unique_ts()
    try: requests.patch(f"{FIREBASE_URL}users/{username}/logs.json", json={t: act}, timeout=5)
    except: return
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, pd.DataFrame([{"시간": t, "활동": act}])], ignore_index=True)
    st.rerun()

def load_ledger():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/ledger.json", timeout=5)
        if res.status_code == 200 and res.json():
            return pd.DataFrame([{"키": k, "날짜": v.get("date",""), "카테고리": v.get("category",""), "금액": int(v.get("amount", 0)), "메모": v.get("memo","")} for k, v in res.json().items()]).sort_values("날짜").reset_index(drop=True)
    except: pass
    return pd.DataFrame(columns=["키","날짜","카테고리","금액","메모"])

def add_ledger_entry(date_str, category, amount, memo):
    ts = _unique_ts()
    try: requests.patch(f"{FIREBASE_URL}users/{username}/ledger.json", json={ts: {"date": date_str, "category": category, "amount": amount, "memo": memo}}, timeout=5)
    except: return
    st.session_state.pet_ledger = pd.concat([st.session_state.pet_ledger, pd.DataFrame([{"키": ts, "날짜": date_str, "카테고리": category, "금액": amount, "메모": memo}])], ignore_index=True)
    st.rerun()

def delete_ledger_entry(key):
    try: requests.delete(f"{FIREBASE_URL}users/{username}/ledger/{key}.json", timeout=5); st.session_state.pet_ledger = st.session_state.pet_ledger[st.session_state.pet_ledger["키"] != key].reset_index(drop=True); st.rerun()
    except: pass

if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'settings' not in st.session_state: st.session_state.settings = load_settings()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()
if 'pet_ledger' not in st.session_state: st.session_state.pet_ledger = load_ledger()

# ----------------------------------------------------
# 활동 이벤트 파서 및 Anchor Time 알고리즘 (v14.9.1 보존)
# ----------------------------------------------------
def extract_dt(log_key, log_act):
    try:
        if '(수정)' in log_act and '[' in log_act and ']' in log_act:
            ext_time = log_act.split('[')[1].split(']')[0]
            date_part = log_key.split(' ')[0]
            return datetime.strptime(f"{date_part} {ext_time}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=9)))
        return datetime.strptime(log_key.split('_')[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=9)))
    except: return None

def get_anchor_dt(now_tz, end_str):
    try:
        eh, em = map(int, end_str.split(':'))
        anchor = now_tz.replace(hour=eh, minute=em, second=0, microsecond=0)
        if now_tz < anchor: anchor -= timedelta(days=1)
        return anchor
    except: return now_tz.replace(hour=5, minute=0, second=0, microsecond=0)

def is_sleeping_time(now_dt, start_str, end_str):
    try:
        n_m = now_dt.hour * 60 + now_dt.minute
        sh, sm = map(int, start_str.split(':'))
        eh, em = map(int, end_str.split(':'))
        s_m, e_m = sh * 60 + sm, eh * 60 + em
        if s_m <= e_m: return s_m <= n_m <= e_m
        else: return n_m >= s_m or n_m <= e_m
    except: return False

# ==========================================
# 🚀 텔레그램 백그라운드 모니터링 데몬 (소변 & 식사)
# ==========================================
@st.cache_resource
def start_bg_monitor(user_id):
    def job():
        while True:
            try:
                time.sleep(30)
                sett = requests.get(f"{FIREBASE_URL}users/{user_id}/settings.json", timeout=5).json()
                if not sett or not sett.get("tg_enabled"): continue
                
                now_tz = datetime.now(timezone(timedelta(hours=9)))
                
                if is_sleeping_time(now_tz, sett.get("sleep_start", "22:00"), sett.get("sleep_end", "05:00")):
                    continue
                
                anchor_dt = get_anchor_dt(now_tz, sett.get("sleep_end", "05:00"))
                pee_interval_sec = float(sett.get("pee_interval", 5.0)) * 3600.0
                meal_interval_sec = float(sett.get("meal_interval", 8.0)) * 3600.0
                
                logs = requests.get(f"{FIREBASE_URL}users/{user_id}/logs.json", timeout=5).json()
                if not logs: continue
                
                p_dt, p_a_dt = None, None
                m_dt, m_a_dt = None, None
                
                for k in sorted(logs.keys(), reverse=True):
                    act = str(logs[k])
                    # 소변 파싱
                    if "소변" in act and not any(x in act for x in ["차감", "리셋", "끄기", "알림 발송"]):
                        if not p_dt: p_dt = extract_dt(k, act)
                    elif "소변 알림 발송" in act and not "차감" in act:
                        if not p_a_dt: p_a_dt = extract_dt(k, act)
                    # 식사 파싱
                    if ("사료" in act or "식사" in act) and not any(x in act for x in ["차감", "리셋", "알림 발송", "간식"]):
                        if not m_dt: m_dt = extract_dt(k, act)
                    elif "식사 알림 발송" in act and not "차감" in act:
                        if not m_a_dt: m_a_dt = extract_dt(k, act)

                try:
                    p_res = requests.get(f"{FIREBASE_URL}users/{user_id}/profile.json", timeout=5)
                    pet_name = p_res.json().get("pet_name", "강아지") if p_res.status_code == 200 and p_res.json() else "강아지"
                except Exception:
                    pet_name = "강아지"

                # 소변 알람 트리거
                if p_dt and p_dt >= anchor_dt:
                    if not p_a_dt or p_dt > p_a_dt:
                        diff_sec = (now_tz - p_dt).total_seconds()
                        if diff_sec >= pee_interval_sec:
                            h, m = int(diff_sec // 3600), int((diff_sec % 3600) // 60)
                            msg = f"🚨 [Smart Pet] 소변 알람!\n\n마지막 소변 후 {h}시간 {m}분 경과했습니다."
                            requests.post(f"https://api.telegram.org/bot{sett['tg_token']}/sendMessage", data={"chat_id": sett['tg_chat_id'], "text": msg}, timeout=10)
                            requests.patch(f"{FIREBASE_URL}users/{user_id}/logs.json", json={now_tz.strftime("%Y-%m-%d %H:%M:%S_%f"): f"📱 소변 알림 발송 ({h}H {m}M 초과)"}, timeout=5)

                # 식사 알람 트리거
                if m_dt and m_dt >= anchor_dt:
                    if not m_a_dt or m_dt > m_a_dt:
                        diff_sec = (now_tz - m_dt).total_seconds()
                        if diff_sec >= meal_interval_sec:
                            h, m = int(diff_sec // 3600), int((diff_sec % 3600) // 60)
                            msg = f"🍽️ [Smart Pet] 식사 알람!\n\n마지막 식사 후 {h}시간 {m}분 경과했습니다."
                            requests.post(f"https://api.telegram.org/bot{sett['tg_token']}/sendMessage", data={"chat_id": sett['tg_chat_id'], "text": msg}, timeout=10)
                            requests.patch(f"{FIREBASE_URL}users/{user_id}/logs.json", json={now_tz.strftime("%Y-%m-%d %H:%M:%S_%f"): f"📱 식사 알림 발송 ({h}H {m}M 초과)"}, timeout=5)

            except: pass
    t = threading.Thread(target=job, daemon=True); t.start(); return t

start_bg_monitor(username)

# ==========================================
# 🎨 UI / CSS
# ==========================================
DYNAMIC_BTN_H = st.session_state.settings.get("btn_h", 4.0)
DYNAMIC_HDR_COLOR = st.session_state.settings.get("hdr_color", "#475569")

st.markdown(f"""
<style>
.stApp {{ background-color: #f8fafc !important; }}
.block-container {{ padding: 1.5rem 1rem 6rem 1rem !important; max-width: 550px !important; }}
::-webkit-scrollbar {{ width: 0px; }} 
.header-card {{ display:flex; justify-content:space-between; align-items:center; background:linear-gradient(135deg, #f0f9ff, #e0f2fe); border-radius:24px; padding: 30px 25px 25px 25px; margin-bottom:20px; color:#0f172a; min-height: 95px; box-shadow: 0 10px 30px rgba(149, 157, 165, 0.15); }} 
div[data-testid="stExpander"] {{ background-color: #ffffff !important; border: none !important; border-radius: 20px !important; box-shadow: 0 8px 24px rgba(149, 157, 165, 0.08) !important; margin-bottom: 18px !important; }}
div.stButton > button {{ height: {DYNAMIC_BTN_H}rem !important; background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 18px !important; font-weight: 800 !important; font-size: 1.05rem !important; color: #334155 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important; transition: all 0.2s ease !important; }} 
div.stButton > button:active {{ transform: scale(0.97) !important; background-color: #f1f5f9 !important; }}
.section-header {{ font-size: 0.9rem; font-weight: 800; color: {DYNAMIC_HDR_COLOR}; letter-spacing: 0.5px; margin: 15px 0 12px 5px; }} 
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 사이드바
# ==========================================
with st.sidebar:
    st.markdown(f"### ⚙️ {username}님")
    if st.button("🔒 로그아웃", use_container_width=True):
        cookie_manager.delete("saved_username"); st.session_state.force_logout = True; st.session_state.logged_in = False; time.sleep(0.3); st.rerun()
    st.caption(f"📌 버전: {APP_VERSION}")
    st.divider()

    with st.expander("📱 텔레그램 알림 설정", expanded=False):
        tg_enabled = st.checkbox("백그라운드 알람 켜기", value=st.session_state.settings.get('tg_enabled', True))
        tg_token = st.text_input("Bot Token", value=st.session_state.settings.get('tg_token', ''))
        tg_chat_id = st.text_input("Chat ID", value=st.session_state.settings.get('tg_chat_id', ''))
        if st.button("텔레그램 설정 저장", use_container_width=True, type="primary"):
            st.session_state.settings.update({'tg_enabled': tg_enabled, 'tg_token': tg_token, 'tg_chat_id': tg_chat_id}); save_settings(st.session_state.settings); st.rerun()
    
    with st.expander("⏰ 시간 및 취침 설정", expanded=False):
        p_int = st.number_input("소변 간격(H)", 0.5, 24.0, float(st.session_state.settings.get('pee_interval', 5.0)), 0.5)
        m_int = st.number_input("식사 간격(H)", 1.0, 24.0, float(st.session_state.settings.get('meal_interval', 8.0)), 0.5)
        c_s, c_e = st.columns(2)
        with c_s: s_start = st.time_input("취침 시작", value=datetime.strptime(st.session_state.settings.get('sleep_start', '22:00'), "%H:%M").time())
        with c_e: s_end = st.time_input("취침 종료", value=datetime.strptime(st.session_state.settings.get('sleep_end', '05:00'), "%H:%M").time())
        if st.button("시간 설정 저장", use_container_width=True, type="primary"):
            st.session_state.settings.update({'pee_interval': p_int, 'meal_interval': m_int, 'sleep_start': s_start.strftime("%H:%M"), 'sleep_end': s_end.strftime("%H:%M")})
            save_settings(st.session_state.settings); st.rerun()
    
    with st.expander("🎨 화면 테마 및 배치 순서", expanded=False):
        new_order = {}
        for k, v in st.session_state.settings.get('order', {}).items():
            new_order[k] = st.number_input(k, min_value=1, max_value=20, value=int(v), step=1)
        if st.button("배치 저장", use_container_width=True, type="primary"):
            st.session_state.settings.update({'order': new_order}); save_settings(st.session_state.settings); st.rerun() 

# ==========================================
# 📊 UI 데이터 파싱 (v14.9.1 보존)
# ==========================================
df = st.session_state.pet_logs

def get_latest_event(kw, exclude_kws=['차감','리셋','끄기']):
    if df.empty: return None, ""
    for i in range(len(df)-1, -1, -1):
        act, t = str(df.iloc[i]['활동']), str(df.iloc[i]['시간'])
        if kw in act and not any(x in act for x in exclude_kws):
            return extract_dt(t, act), act
    return None, ""

p_dt, _ = get_latest_event("소변", ['차감','리셋','끄기','알림 발송'])
p_a_dt, _ = get_latest_event("소변 알림 발송")
d_dt, _ = get_latest_event("대변")
m_dt, _ = get_latest_event("사료", ['차감','리셋','간식'])
if not m_dt: m_dt, _ = get_latest_event("식사", ['차감','리셋','간식'])
m_a_dt, _ = get_latest_event("식사 알림 발송")

now_obj = now_kst()
anchor_dt = get_anchor_dt(now_obj, st.session_state.settings.get('sleep_end', '05:00'))

# --- 소변 상태 ---
p_disp, p_expect, p_iso, msg_st, msg_col = "--:--", "--:--", "", "대기 중", "#64748b"
if p_dt:
    p_disp = p_dt.strftime("%H:%M")
    if p_dt >= anchor_dt:
        p_iso = p_dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        p_expect = (p_dt + timedelta(hours=float(st.session_state.settings.get("pee_interval", 5.0)))).strftime("%H:%M")
        if p_a_dt and p_a_dt > p_dt: msg_st, msg_col = f"발송 완료", "#10b981"
        else: msg_st, msg_col = "대기 중", "#f59e0b"
    else: msg_st, msg_col = "기상 확인 전", "#94a3b8"

d_disp = d_dt.strftime("%H:%M") if d_dt else "--:--"
d_iso = d_dt.strftime("%Y-%m-%dT%H:%M:%S+09:00") if d_dt else ""

# --- 식사 상태 ---
m_disp, m_expect, m_iso, m_msg_st, m_msg_col = "--:--", "--:--", "", "대기 중", "#64748b"
if m_dt:
    m_disp = m_dt.strftime("%H:%M")
    if m_dt >= anchor_dt:
        m_iso = m_dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        m_expect = (m_dt + timedelta(hours=float(st.session_state.settings.get("meal_interval", 8.0)))).strftime("%H:%M")
        if m_a_dt and m_a_dt > m_dt: m_msg_st, m_msg_col = f"발송 완료", "#10b981"
        else: m_msg_st, m_msg_col = "대기 중", "#f59e0b"
    else: m_msg_st, m_msg_col = "기상 확인 전", "#94a3b8"

s_start = st.session_state.settings.get('sleep_start', '22:00')
s_end = st.session_state.settings.get('sleep_end', '05:00')

# ==========================================
# 🧱 UI 모듈 렌더링 (v14.9.1 보존)
# ==========================================
def render_timer():
    intv_h = float(st.session_state.settings.get("pee_interval", 5.0))
    m_intv_h = float(st.session_state.settings.get("meal_interval", 8.0))
    
    components.html(f"""
    <div style="display:flex; flex-direction:row; gap:15px; font-family:'Malgun Gothic', sans-serif; width:100%; margin-bottom:15px;">
        <div id="p_card" style="flex:3; background:#ffffff; border-radius:24px; padding:15px 10px; box-shadow:0 8px 24px rgba(0,0,0,0.06); display:flex; flex-direction:column;">
            <div id="p_title" style="font-size:0.95rem; font-weight:800; color:#0284c7; text-align:center; margin-bottom:10px;">💧 소변 타이머</div>
            <div style="display:flex; align-items:center; justify-content:space-evenly; flex:1;">
                <div style="position:relative; width:80px; height:80px;">
                    <svg viewBox="0 0 36 36" style="width:100%; height:100%;"><path d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#f0f9ff" stroke-width="2.5"/><path id="p_circ" d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#38bdf8" stroke-width="3" stroke-dasharray="0, 100" stroke-linecap="round"/></svg>
                    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width:100%; text-align:center;">
                        <div id="p_rem" style="font-size:1.1rem; font-weight:900; color:#0369a1;">--:--</div>
                    </div>
                </div>
                <div style="border-left:2px dashed #f1f5f9; padding-left:10px; display:flex; flex-direction:column; font-size:0.85rem;">
                    <div><span style="color:#64748b;">최근</span> <b style="float:right;">{p_disp}</b></div>
                    <div><span style="color:#0284c7;">예상</span> <b style="float:right;">{p_expect}</b></div>
                    <div style="margin-top:4px; font-size:0.75rem; font-weight:800; color:{msg_col}; background:#f8fafc; text-align:center; border-radius:4px;">{msg_st}</div>
                </div>
            </div>
        </div>
        <div id="d_card" style="flex:2; background:#ffffff; border-radius:24px; padding:15px 10px; text-align:center; box-shadow:0 8px 24px rgba(0,0,0,0.06);">
            <div style="font-size:0.95rem; font-weight:800; color:#c2410c; margin-bottom:5px;">💩 대변</div>
            <div style="position:relative; width:70px; height:70px; margin:0 auto;">
                <svg viewBox="0 0 36 36" style="width:100%; height:100%;"><path d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#fff7ed" stroke-width="2.5"/><path id="d_circ" d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#fb923c" stroke-width="3" stroke-dasharray="0, 100" stroke-linecap="round"/></svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%);"><div id="d_elap" style="font-size:1.0rem; font-weight:900; color:#9a3412;">--:--</div></div>
            </div>
            <div style="font-size:0.75rem; color:#64748b; font-weight:700; margin-top:5px;">최근: {d_disp}</div>
        </div>
    </div>
    
    <div style="display:flex; flex-direction:row; font-family:'Malgun Gothic', sans-serif; width: 100%;">
        <div id="m_card" style="flex:1; background:#ffffff; border-radius:24px; padding:15px 20px; box-shadow:0 8px 24px rgba(149,157,165,0.06); display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="position:relative; width:70px; height:70px;">
                    <svg viewBox="0 0 36 36" style="width:100%; height:100%;"><path d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#f4f4f5" stroke-width="2.5"/><path id="m_circ" d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#10b981" stroke-width="3" stroke-dasharray="0, 100" stroke-linecap="round"/></svg>
                    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width:100%; text-align:center;">
                        <div id="m_rem" style="font-size:1.0rem; font-weight:900; color:#047857;">--:--</div>
                    </div>
                </div>
                <div>
                    <div id="m_title" style="font-size:0.95rem; font-weight:800; color:#059669; margin-bottom:2px;">🍽️ 식사 타이머</div>
                    <div style="font-size:0.75rem; font-weight:800; color:{m_msg_col}; background:#f8fafc; padding:2px 6px; border-radius:4px; display:inline-block;">{m_msg_st}</div>
                </div>
            </div>
            <div style="border-left: 2px dashed #f1f5f9; padding-left:15px; display:flex; flex-direction:column; gap:4px; font-size:0.85rem; min-width:90px;">
                <div><span style="color:#64748b;">최근</span> <b style="float:right;">{m_disp}</b></div>
                <div><span style="color:#059669;">예상</span> <b style="float:right;">{m_expect}</b></div>
            </div>
        </div>
    </div>
    
    <script>
        const P_LIM = {intv_h} * 3600000; const M_LIM = {m_intv_h} * 3600000; const D_MAX_MS = 43200000; 
        const s_s = "{s_start}"; const s_e = "{s_end}";

        function isSleep(now) {{
            const n_m = now.getHours()*60+now.getMinutes(); const sm = parseInt(s_s.split(':')[0])*60+parseInt(s_s.split(':')[1]); const em = parseInt(s_e.split(':')[0])*60+parseInt(s_e.split(':')[1]);
            return sm<=em ? (n_m>=sm && n_m<=em) : (n_m>=sm || n_m<=em);
        }}

        function update() {{ 
            const now = new Date(); 
            const is_sleep = isSleep(now);
            
            // --- 소변 ---
            const p_rem = document.getElementById('p_rem'); const p_circ = document.getElementById('p_circ'); const p_card = document.getElementById('p_card'); const p_title = document.getElementById('p_title');
            if (is_sleep) {{
                p_card.style.background = "#f8fafc"; p_title.innerText = "🌙 취침 중"; p_rem.innerText = "Zzz"; p_circ.setAttribute('stroke-dasharray', '0, 100');
            }} else if ("{p_iso}" == "") {{
                p_rem.innerText = "WAIT"; p_circ.setAttribute('stroke-dasharray', '0, 100');
            }} else {{
                p_title.innerText = "💧 소변 타이머"; const diff = now - new Date("{p_iso}");
                if(diff >= 0) {{
                    const rem = P_LIM - diff; const r_abs = Math.abs(rem); const h = Math.floor(r_abs/3600000), m = Math.floor((r_abs%3600000)/60000);
                    p_rem.innerText = (rem<0?"-":"") + String(h).padStart(2,'0')+":"+String(m).padStart(2,'0');
                    p_rem.style.color = rem < 0 ? "#ef4444" : "#0369a1"; p_card.style.background = rem < 0 ? "#fff1f2" : "#ffffff";
                    p_circ.setAttribute('stroke-dasharray', Math.min((diff/P_LIM)*100, 100) + ', 100');
                }}
            }}

            // --- 식사 ---
            const m_rem = document.getElementById('m_rem'); const m_circ = document.getElementById('m_circ'); const m_card = document.getElementById('m_card'); const m_title = document.getElementById('m_title');
            if (is_sleep) {{
                m_card.style.background = "#f8fafc"; m_title.innerText = "🌙 취침 중"; m_rem.innerText = "Zzz"; m_circ.setAttribute('stroke-dasharray', '0, 100');
            }} else if ("{m_iso}" == "") {{
                m_rem.innerText = "WAIT"; m_circ.setAttribute('stroke-dasharray', '0, 100');
            }} else {{
                m_title.innerText = "🍽️ 식사 타이머"; const diff = now - new Date("{m_iso}");
                if(diff >= 0) {{
                    const rem = M_LIM - diff; const r_abs = Math.abs(rem); const h = Math.floor(r_abs/3600000), m = Math.floor((r_abs%3600000)/60000);
                    m_rem.innerText = (rem<0?"-":"") + String(h).padStart(2,'0')+":"+String(m).padStart(2,'0');
                    m_rem.style.color = rem < 0 ? "#ef4444" : "#047857"; m_card.style.background = rem < 0 ? "#fff1f2" : "#ffffff";
                    m_circ.setAttribute('stroke-dasharray', Math.min((diff/M_LIM)*100, 100) + ', 100');
                }}
            }}

            // --- 대변 ---
            const d_el = document.getElementById('d_elap'), d_circ = document.getElementById('d_circ'), d_iso = "{d_iso}";
            if(d_iso) {{
                const diff = now - new Date(d_iso); if(diff>=0) {{
                    const d_h = Math.floor(diff/3600000), d_m = Math.floor((diff%3600000)/60000);
                    d_el.innerText = String(d_h).padStart(2,'0') + ":" + String(d_m).padStart(2,'0');
                    d_circ.setAttribute('stroke-dasharray', Math.min((diff/D_MAX_MS)*100, 100) + ', 100');
                }}
            }}
        }}
        setInterval(update, 1000); update();
    </script>
    """, height=300)

def render_poo_pee():
    st.markdown("<div class='section-header'>🚨 실내 배변</div>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💧 실내 소변", use_container_width=True): add_record("💦 집에서 소변")
    with b2:
        if st.button("💩 실내 대변", use_container_width=True): add_record("💩 집에서 대변")

def render_meal():
    st.markdown("<div class='section-header'>🍽️ 식사 / 간식 / 물</div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        if st.button("🥣 사료 (종이컵1)", use_container_width=True): add_record("🥣 사료 (종이컵1)")
    with m2:
        if st.button("🍖 간식 (개껌)", use_container_width=True): add_record("🍖 간식 (개껌)")
    with m3:
        if st.button("💧 물 급여", use_container_width=True): add_record("💧 물 급여 완료")

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

def render_manual():
    with st.expander("⚙️ 타이머 수동 조절"):
        t1, t2, t3 = st.tabs(["💧 소변", "💩 대변", "🍽️ 식사"])
        with t1:
            p_w = st.time_input("시간 선택", now_kst().time(), key="p_w")
            if st.button("시간 저장", key="bp_w", use_container_width=True): add_record(f"💦 소변(수정) [{p_w.strftime('%H:%M:%S')}] (통계제외)")
        with t2:
            d_w = st.time_input("시간 선택", now_kst().time(), key="d_w")
            if st.button("시간 저장", key="bd_w", use_container_width=True): add_record(f"💩 대변(수정) [{d_w.strftime('%H:%M:%S')}] (통계제외)")
        with t3:
            m_w = st.time_input("시간 선택", now_kst().time(), key="m_w")
            if st.button("시간 저장", key="bm_w", use_container_width=True): add_record(f"🥣 사료(수정) [{m_w.strftime('%H:%M:%S')}] (통계제외)")

# 메인 렌더링
pet_n = st.session_state.profile.get('pet_name','강아지')
last_up = str(df.iloc[-1]['시간'])[:19] if not df.empty else "없음"
st.markdown(f"<div class='header-card'><div><div style='font-size:1.6rem; font-weight:900;'>🐾 {pet_n} 센터</div><div style='font-size:0.85rem;'>{now_kst().strftime('%m월 %d일 %H:%M')}</div></div><div style='text-align:right; font-size:0.75rem;'>☁️ {last_up}<br>{APP_VERSION}</div></div>", unsafe_allow_html=True)

ui_order = st.session_state.settings.get('order', {})
for mod_name, _ in sorted(ui_order.items(), key=lambda x: int(x[1])):
    if mod_name == "타이머": render_timer()
    elif mod_name == "배변기록": render_poo_pee()
    elif mod_name == "식사기록": render_meal()
    elif mod_name == "산책기록": render_walk()
    elif mod_name == "수동조절": render_manual()

with st.expander("📋 활동 로그", expanded=False):
    if not df.empty: st.dataframe(df.sort_values("시간", ascending=False).reset_index(drop=True), use_container_width=True)

st.divider()
if not df.empty:
    target_df = df[df['시간'].astype(str).str.startswith(t_date, na=False)].copy()
    if not target_df.empty:
        if st.button(f"❌ 직전 취소: [{str(target_df.iloc[-1]['시간'])[11:19]}] {str(target_df.iloc[-1]['활동'])}", use_container_width=True):
            try: requests.delete(f"{FIREBASE_URL}users/{username}/logs/{target_df.iloc[-1]['시간']}.json", timeout=5).raise_for_status(); st.rerun()
            except: pass

st.markdown(f"<div style='text-align:center; color:#94a3b8; font-size:0.75rem;'>🐾 Smart Pet Care Center<br>{APP_VERSION}</div>", unsafe_allow_html=True)

# END

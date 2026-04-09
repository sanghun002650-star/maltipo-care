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
APP_VERSION = "v14.1.9 (UI 정밀 정렬 & 잔상 원천 차단)"
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
# 🚪 로그인 로직
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
                    else: st.error("❌ 비밀번호 오류")
                except: st.error("⚠️ 네트워크 오류")
                
    with tab2:
        reg_id = st.text_input("아이디", key="r_id")
        reg_pw = st.text_input("비밀번호", type="password", key="r_pw")
        if st.button("계정 생성 💾", use_container_width=True):
            if reg_id and reg_pw:
                res = requests.get(f"{FIREBASE_URL}users/{reg_id}.json", timeout=5)
                if res.status_code == 200 and res.json() is not None: st.error("❌ 이미 존재함")
                else:
                    requests.put(f"{FIREBASE_URL}users/{reg_id}/password.json", json=reg_pw, timeout=5)
                    requests.put(f"{FIREBASE_URL}users/{reg_id}/settings.json", json={"pee_interval": 5.0, "tg_enabled": True, "tg_token": "8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0", "tg_chat_id": "8124116628", "order": {"타이머":1, "누적데이터":2, "배변기록":3, "활동로그":4, "가계부":5}}, timeout=5)
                    st.success("✅ 완료!")
    st.stop()

# ==========================================
# ☁️ 데이터 엔진 & 텔레그램 데몬
# ==========================================
username = st.session_state.username

def load_profile():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/profile.json", timeout=5)
        if res.status_code == 200 and res.json(): return res.json()
    except: pass
    return {"pet_name": "강아지", "birth": "", "weight": "", "gender": "수컷", "memo": ""}

def load_settings():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/settings.json", timeout=5)
        if res.status_code == 200 and res.json():
            loaded = res.json()
            if "pee_interval" not in loaded: loaded["pee_interval"] = 5.0
            if "order" not in loaded: loaded["order"] = {"타이머":1, "누적데이터":2, "배변기록":3, "산책기록":4, "건강미용":5, "수동조절":6, "기록차감":7, "활동로그":8, "주간통계":9, "가계부":10}
            return loaded
    except: pass
    return {"btn_h": 4.2, "hdr_color": "#64748b", "pee_interval": 5.0, "tg_enabled": True, "tg_token": "8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0", "tg_chat_id": "8124116628", "order": {"타이머":1, "누적데이터":2, "배변기록":3, "산책기록":4, "건강미용":5, "수동조절":6, "기록차감":7, "활동로그":8, "주간통계":9, "가계부":10}}

def save_settings(settings_data):
    try: requests.put(f"{FIREBASE_URL}users/{username}/settings.json", json=settings_data, timeout=5)
    except: st.error("⚠️ 저장 실패")

def save_profile(profile):
    try: requests.put(f"{FIREBASE_URL}users/{username}/profile.json", json=profile, timeout=5)
    except: st.error("⚠️ 저장 실패")

def load_data():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/logs.json", timeout=5)
        if res.status_code == 200 and res.json():
            records = [{"시간": k, "활동": v} for k, v in res.json().items()]
            return pd.DataFrame(records).sort_values("시간").reset_index(drop=True)
    except: pass
    return pd.DataFrame(columns=["시간", "활동"])

def add_record(act, c_time=None):
    t = c_time if c_time else now_kst().strftime("%Y-%m-%d %H:%M:%S_%f")
    try: requests.patch(f"{FIREBASE_URL}users/{username}/logs.json", json={t: act}, timeout=5)
    except: st.error("⚠️ 저장 실패"); return
    st.session_state.pet_logs = pd.concat([st.session_state.pet_logs, pd.DataFrame([{"시간": t, "활동": act}])], ignore_index=True)
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
    ts = now_kst().strftime("%Y-%m-%d %H:%M:%S_%f")
    try: requests.patch(f"{FIREBASE_URL}users/{username}/ledger.json", json={ts: {"date": date_str, "category": category, "amount": amount, "memo": memo}}, timeout=5)
    except: st.error("⚠️ 저장 실패"); return
    st.session_state.pet_ledger = pd.concat([st.session_state.pet_ledger, pd.DataFrame([{"키": ts, "날짜": date_str, "카테고리": category, "금액": amount, "메모": memo}])], ignore_index=True)
    st.rerun()

def delete_ledger_entry(key):
    try: requests.delete(f"{FIREBASE_URL}users/{username}/ledger/{key}.json", timeout=5); st.rerun()
    except: st.error("⚠️ 삭제 실패")

if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'settings' not in st.session_state: st.session_state.settings = load_settings()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()
if 'pet_ledger' not in st.session_state: st.session_state.pet_ledger = load_ledger()

# 🚀 텔레그램 백그라운드 스레드
def send_tg_msg(token, chat_id, text):
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=10)
    except: pass

@st.cache_resource
def start_bg_monitor(user_id):
    def job():
        last_alerted_ts = ""
        while True:
            try:
                time.sleep(30)
                s_res = requests.get(f"{FIREBASE_URL}users/{user_id}/settings.json", timeout=5)
                if s_res.status_code != 200 or not s_res.json(): continue
                sett = s_res.json()
                if not sett.get("tg_enabled"): continue
                
                l_res = requests.get(f"{FIREBASE_URL}users/{user_id}/logs.json", timeout=5)
                if l_res.status_code != 200 or not l_res.json(): continue
                logs = l_res.json()
                
                p_iso = ""
                for k in sorted(logs.keys(), reverse=True):
                    act = str(logs[k])
                    if "소변" in act and not any(x in act for x in ["차감","리셋","끄기","알림 발송"]):
                        t_part = k.split('_')[0] if '_' in k else k.split('.')[0]
                        p_iso = t_part.replace(" ","T") + "+09:00"
                        break
                
                if p_iso and p_iso != last_alerted_ts:
                    diff_h = (datetime.now(timezone(timedelta(hours=9))) - datetime.fromisoformat(p_iso)).total_seconds() / 3600.0
                    if diff_h >= float(sett.get("pee_interval", 5.0)):
                        msg = f"🚨 [Smart Pet] 소변 시간 {sett.get('pee_interval')}시간 경과!"
                        send_tg_msg(sett["tg_token"], sett["tg_chat_id"], msg)
                        alert_ts = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S_%f")
                        requests.patch(f"{FIREBASE_URL}users/{user_id}/logs.json", json={alert_ts: f"📱 알림 발송 ({sett.get('pee_interval')}시간 초과)"})
                        last_alerted_ts = p_iso
            except: pass
    t = threading.Thread(target=job, daemon=True); t.start(); return t

start_bg_monitor(username)

# ==========================================
# 🎨 UI / CSS (잔상 완전 제거 패치)
# ==========================================
DYNAMIC_BTN_H = st.session_state.settings.get("btn_h", 4.2)
DYNAMIC_HDR_COLOR = st.session_state.settings.get("hdr_color", "#475569")

st.markdown(f"""
<style>
.stApp {{ background-color: #f8fafc !important; }}
.block-container {{ padding: 1.5rem 1rem 6rem 1rem !important; max-width: 550px !important; }}
.header-card {{
    display:flex; justify-content:space-between; align-items:center; 
    background:linear-gradient(135deg, #f0f9ff, #e0f2fe); border-radius:24px; padding: 25px; 
    margin-bottom:20px; color:#0f172a; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
}} 
div[data-testid="stExpander"] {{
    background-color: #ffffff !important; border: none !important;
    border-radius: 20px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.04) !important; margin-bottom: 12px !important;
}}
div.stButton > button {{
    height: {DYNAMIC_BTN_H}rem !important; background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important; border-radius: 18px !important; font-weight: 800 !important;
}} 

/* [수정] 차트 잔상 및 툴팁 완벽 제거 */
.vega-bind, .vega-actions, #vg-tooltip-element, .vg-tooltip {{ 
    display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important; 
}}
canvas {{ pointer-events: none !important; }} /* 차트와 상호작용 원천 차단 */

/* 사이드바 저장버튼 수직 정렬 */
.stButton button[key*="btn_save_int"] {{ margin-top: 0px !important; }}
div[data-testid="column"]:has(button[key="btn_save_int"]) {{ display: flex; align-items: flex-end; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 사이드바
# ==========================================
with st.sidebar:
    st.markdown(f"### ⚙️ {username}님")
    if st.button("🔒 로그아웃", use_container_width=True):
        cookie_manager.delete("saved_username")
        st.session_state.force_logout = True; st.session_state.logged_in = False; st.rerun()
    st.caption(f"📌 {APP_VERSION}")
    st.divider()

    with st.expander("📱 텔레그램 설정", expanded=False):
        st.session_state.settings['tg_enabled'] = st.checkbox("알람 켜기", value=st.session_state.settings.get('tg_enabled', True))
        st.session_state.settings['tg_token'] = st.text_input("Token", value=st.session_state.settings.get('tg_token', ''))
        st.session_state.settings['tg_chat_id'] = st.text_input("Chat ID", value=st.session_state.settings.get('tg_chat_id', ''))
        if st.button("텔레그램 저장", use_container_width=True): save_settings(st.session_state.settings); st.rerun()
    
    with st.expander("⏰ 소변 알람 시간 설정", expanded=False):
        c1, c2 = st.columns([6, 4])
        with c1: new_i = st.number_input("간격(H)", 0.5, 24.0, float(st.session_state.settings.get('pee_interval', 5.0)), 0.5)
        with c2: 
            if st.button("💾 저장", key="btn_save_int", use_container_width=True):
                st.session_state.settings['pee_interval'] = new_i; save_settings(st.session_state.settings); st.rerun()
    
    with st.expander("🎨 배치 및 테마", expanded=False):
        new_bh = st.slider("버튼 높이", 3.0, 6.0, float(st.session_state.settings.get('btn_h', 4.2)), 0.1)
        new_hc = st.color_picker("헤더 색상", st.session_state.settings.get('hdr_color', '#475569'))
        new_order = {}
        order_items = list(st.session_state.settings.get('order', {}).items())
        c1, c2 = st.columns(2)
        for i, (k, v) in enumerate(order_items):
            with (c1 if i%2==0 else c2): new_order[k] = st.number_input(k, 1, 20, int(v))
        if st.button("테마 저장", use_container_width=True, type="primary"):
            st.session_state.settings.update({'btn_h': new_bh, 'hdr_color': new_hc, 'order': new_order}); save_settings(st.session_state.settings); st.rerun()

    with st.expander("📝 프로필 수정"):
        p = st.session_state.profile
        p.update({"pet_name": st.text_input("이름", p['pet_name']), "birth": st.text_input("생일", p['birth']), "weight": st.text_input("몸무게", p['weight'])})
        if st.button("프로필 저장", use_container_width=True): save_profile(p); st.rerun()

# ==========================================
# 📊 데이터 처리
# ==========================================
t_date = now_kst().strftime("%Y-%m-%d")
df = st.session_state.pet_logs
target_df = df[df['시간'].astype(str).str.startswith(t_date)].copy() if not df.empty else pd.DataFrame(columns=["시간","활동"])

def get_iso(kw, check_df):
    if check_df.empty: return ""
    for i in range(len(check_df)-1, -1, -1):
        act, t = str(check_df.iloc[i]['활동']), str(check_df.iloc[i]['시간'])
        if any(x in act for x in ['차감','리셋','끄기','알림']): continue
        if kw in act: return t.split('_')[0].replace(" ","T") + "+09:00"
    return ""

def get_count(kw, check_df):
    if check_df.empty: return 0
    p, m = 0, 0
    for act in check_df['활동'].astype(str):
        if kw in act:
            if '차감' in act: m += 1
            elif any(x in act for x in ['리셋','끄기','알림']): pass
            else: p += 1
    return max(0, p - m)

p_iso = get_iso("소변", target_df); d_iso = get_iso("대변", target_df)

# ==========================================
# 🧱 메인 모듈
# ==========================================
def render_timer():
    interval_h = float(st.session_state.settings.get("pee_interval", 5.0))
    components.html(f"""
    <div style="display:flex; justify-content:space-between; gap:12px; font-family:sans-serif;">
        <div id="p_card" style="flex:1; background:#ffffff; border-radius:24px; padding:15px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.05); transition:0.5s;">
            <div style="font-size:0.9rem; font-weight:800; color:#0284c7; margin-bottom:10px;">💧 소변 타이머</div>
            <div style="position:relative; width:120px; height:120px; margin:0 auto;">
                <svg viewBox="0 0 36 36" style="width:100%; height:100%;"><path d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#f0f9ff" stroke-width="2" /><path id="p_circ" d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="0, 100" stroke-linecap="round" /></svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width:100%;">
                    <div id="p_tm" style="font-size:1.4rem; font-weight:900; color:#0369a1;">--:--</div>
                    <div id="p_rem" style="font-size:0.75rem; font-weight:800; color:#ef4444;">남음 --:--</div>
                </div>
            </div>
        </div>
        <div id="d_card" style="flex:1; background:#ffffff; border-radius:24px; padding:15px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-size:0.9rem; font-weight:800; color:#c2410c; margin-bottom:10px;">💩 대변 타이머</div>
            <div style="position:relative; width:120px; height:120px; margin:0 auto;">
                <svg viewBox="0 0 36 36" style="width:100%; height:100%;"><path d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#fff7ed" stroke-width="2" /><path id="d_circ" d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" fill="none" stroke="#fb923c" stroke-width="2.5" stroke-dasharray="0, 100" stroke-linecap="round" /></svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width:100%;">
                    <div id="d_tm" style="font-size:1.4rem; font-weight:900; color:#9a3412;">--:--</div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const P_LIM = {interval_h} * 3600000;
        function update() {{
            const p_el=document.getElementById('p_tm'), p_rem=document.getElementById('p_rem'), p_circ=document.getElementById('p_circ'), p_card=document.getElementById('p_card'), p_iso="{p_iso}";
            if(p_iso) {{
                const diff = new Date() - new Date(p_iso);
                if(diff>=0) {{
                    p_el.innerText = Math.floor(diff/3600000).toString().padStart(2,'0')+":"+Math.floor((diff%3600000)/60000).toString().padStart(2,'0');
                    const rem = P_LIM - diff;
                    if(rem>0) {{ p_rem.innerText = "남음 "+Math.floor(rem/3600000).toString().padStart(2,'0')+":"+Math.floor((rem%3600000)/60000).toString().padStart(2,'0'); p_card.style.background="#ffffff"; }}
                    else {{ p_rem.innerText="🚨 초과!"; p_card.style.background="#fff1f2"; }}
                    p_circ.setAttribute('stroke-dasharray', Math.min((diff/P_LIM)*100, 100) + ', 100');
                }}
            }}
            const d_el=document.getElementById('d_tm'), d_circ=document.getElementById('d_circ'), d_iso="{d_iso}";
            if(d_iso) {{
                const diff = new Date() - new Date(d_iso);
                if(diff>=0) {{
                    d_el.innerText = Math.floor(diff/3600000).toString().padStart(2,'0')+":"+Math.floor((diff%3600000)/60000).toString().padStart(2,'0');
                    d_circ.setAttribute('stroke-dasharray', Math.min((diff/43200000)*100, 100) + ', 100');
                }}
            }}
        }}
        setInterval(update, 1000); update();
    </script>
    """, height=180)

def render_summary():
    p, d, w = get_count('소변', target_df), get_count('대변', target_df), get_count('산책', target_df)
    st.markdown(f"""
    <div style="background:#ffffff; border-radius:24px; padding:20px; box-shadow:0 4px 12px rgba(0,0,0,0.04); margin-bottom:15px;">
        <div class="horizontal-metrics">
            <div class="metric-box" style="background:#f0f9ff;"><div class="metric-label" style="color:#0284c7;">💧 소변</div><div class="metric-value" style="color:#0369a1;">{p}회</div></div>
            <div class="metric-box" style="background:#fff7ed;"><div class="metric-label" style="color:#c2410c;">💩 대변</div><div class="metric-value" style="color:#9a3412;">{d}회</div></div>
            <div class="metric-box" style="background:#ecfccb;"><div class="metric-label" style="color:#4d7c0f;">🐾 산책</div><div class="metric-value" style="color:#3f6212;">{w}회</div></div>
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

def render_log():
    with st.expander(f"📋 활동 로그 ({len(target_df)}건)", expanded=False):
        if not target_df.empty:
            log_display = target_df.copy()
            log_display['시간'] = log_display['시간'].astype(str).str[11:19]
            st.dataframe(log_display.sort_values('시간', ascending=False), use_container_width=True)

def render_stats():
    with st.expander("📊 주간 통계", expanded=False):
        if not df.empty:
            w_dates = [(now_kst() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            w_data = [{"날짜": d[5:], "소변": get_count('소변', df[df['시간'].astype(str).str.startswith(d)]), "대변": get_count('대변', df[df['시간'].astype(str).str.startswith(d)]), "산책": get_count('산책', df[df['시간'].astype(str).str.startswith(d)])} for d in w_dates]
            st.bar_chart(pd.DataFrame(w_data).set_index("날짜"), color=["#bae6fd","#fed7aa","#d9f99d"])

def render_ledger():
    with st.expander("💰 반려견 가계부", expanded=False):
        ldg = st.session_state.pet_ledger; cur_m = now_kst().strftime("%Y-%m")
        monthly = ldg[ldg["날짜"].astype(str).str.startswith(cur_m)].copy() if not ldg.empty else pd.DataFrame()
        total = int(monthly["금액"].sum()) if not monthly.empty else 0
        st.markdown(f"<div style='background:#1e293b; border-radius:15px; padding:15px; color:white; text-align:center; margin-bottom:15px;'><strong>{now_kst().month}월 합계: {total:,}원</strong></div>", unsafe_allow_html=True)
        lc1, lc2 = st.columns(2)
        with lc1: l_date, l_cat = st.date_input("날짜", value=now_kst().date()), st.selectbox("카테고리", ["사료", "간식", "배변패드", "의료비", "기타"])
        with lc2: l_amt, l_memo = st.number_input("금액", min_value=0, step=1000), st.text_input("메모")
        if st.button("💾 지출 저장", use_container_width=True, type="primary"):
            if l_amt > 0: add_ledger_entry(l_date.strftime("%Y-%m-%d"), l_cat, int(l_amt), l_memo)
        if not monthly.empty:
            st.dataframe(monthly[["날짜","카테고리","금액","메모"]].sort_values("날짜", ascending=False), use_container_width=True)

# ==========================================
# 🏠 메인 렌더링
# ==========================================
pet_n = st.session_state.profile.get('pet_name','강아지'); last_up = str(df.iloc[-1]['시간'])[:19] if not df.empty else "없음"
st.markdown(f"<div class='header-card'><div><div style='font-size:1.6rem; font-weight:900; margin-bottom:5px; color:#0f172a;'>🐾 {pet_n} 센터</div><div style='font-size:0.85rem; font-weight:700; color:#475569;'>{now_kst().strftime('%m월 %d일 (%a) %H:%M')}</div></div><div style='text-align:right; font-size:0.75rem; color:#64748b; font-weight:600;'><div style='margin-bottom:5px;'>☁️ {last_up}</div><div>{APP_VERSION[:7]}</div></div></div>", unsafe_allow_html=True)

ui_order = st.session_state.settings.get('order', {})
for mod_name, _ in sorted(ui_order.items(), key=lambda x: int(x[1])):
    if mod_name == "타이머": render_timer()
    elif mod_name == "누적데이터": render_summary()
    elif mod_name == "배변기록": render_poo_pee()
    elif mod_name == "산책기록": render_walk()
    elif mod_name == "활동로그": render_log()
    elif mod_name == "주간통계": render_stats()
    elif mod_name == "가계부": render_ledger()

st.divider()
if not target_df.empty:
    last_act, last_t = str(target_df.iloc[-1]['활동']), str(target_df.iloc[-1]['시간'])[11:19]
    if st.button(f"❌ 직전 취소: [{last_t}] {last_act}", use_container_width=True):
        try: requests.delete(f"{FIREBASE_URL}users/{username}/logs/{target_df.iloc[-1]['시간']}.json", timeout=5); st.rerun()
        except: st.error("취소 실패")
st.markdown(f"<div style='text-align:center; color:#94a3b8; font-size:0.75rem; padding:20px 0 30px; font-weight:600;'>🐾 Smart Pet Care Center<br>현재 버전: <strong>{APP_VERSION}</strong></div>", unsafe_allow_html=True)

# END

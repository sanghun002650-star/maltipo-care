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
APP_VERSION = "v14.2.4 (수동 시간 동기화 & 초 단위 제거)"
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
        login_id = st.text_input("아이디", key="l_id")
        login_pw = st.text_input("비밀번호", type="password", key="l_pw")
        if st.button("접속하기 🚀", use_container_width=True, type="primary"):
            try:
                res = requests.get(f"{FIREBASE_URL}users/{login_id}/password.json", timeout=5)
                if res.status_code == 200 and res.json() == login_pw:
                    cookie_manager.set("saved_username", login_id, expires_at=datetime.now() + timedelta(days=180))
                    st.session_state.force_logout = False
                    st.session_state.logged_in = True
                    st.session_state.username = login_id
                    st.rerun()
                else: st.error("❌ 비밀번호 오류")
            except: st.error("⚠️ 네트워크 오류")
    st.stop()

# ==========================================
# ☁️ 데이터 엔진 & 텔레그램 데몬
# ==========================================
username = st.session_state.username

def load_settings():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/settings.json", timeout=5)
        if res.status_code == 200 and res.json():
            loaded = res.json()
            if "pee_interval" not in loaded: loaded["pee_interval"] = 5.0
            return loaded
    except: pass
    return {"btn_h": 4.2, "hdr_color": "#64748b", "pee_interval": 5.0, "tg_enabled": True, "tg_token": "8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0", "tg_chat_id": "8124116628"}

def save_settings(settings_data):
    requests.put(f"{FIREBASE_URL}users/{username}/settings.json", json=settings_data, timeout=5)

def load_data():
    try:
        res = requests.get(f"{FIREBASE_URL}users/{username}/logs.json", timeout=5)
        if res.status_code == 200 and res.json():
            records = [{"시간": k, "활동": v} for k, v in res.json().items()]
            return pd.DataFrame(records).sort_values("시간").reset_index(drop=True)
    except: pass
    return pd.DataFrame(columns=["시간", "활동"])

def add_record(act):
    t = now_kst().strftime("%Y-%m-%d %H:%M:%S_%f")
    requests.patch(f"{FIREBASE_URL}users/{username}/logs.json", json={t: act}, timeout=5)
    st.rerun()

# 🚀 텔레그램 백그라운드 스레드 (수동 시간 동기화 패치)
def send_tg_msg(token, chat_id, text):
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=10)

@st.cache_resource
def start_bg_monitor(user_id):
    def job():
        last_alerted_ts = ""
        while True:
            try:
                time.sleep(30)
                sett = load_settings()
                if not sett.get("tg_enabled"): continue
                logs_res = requests.get(f"{FIREBASE_URL}users/{user_id}/logs.json", timeout=5)
                if logs_res.status_code != 200 or not logs_res.json(): continue
                logs = logs_res.json()
                
                p_ts = ""
                for k in sorted(logs.keys(), reverse=True):
                    act = str(logs[k])
                    if "소변" in act and not any(x in act for x in ["차감", "리셋", "끄기", "알림 발송"]):
                        if '(수정)' in act and '[' in act and ']' in act:
                            try:
                                ext_time = act.split('[')[1].split(']')[0]
                                date_part = k.split(' ')[0]
                                p_ts = f"{date_part} {ext_time}"
                            except:
                                p_ts = k.split('_')[0]
                        else:
                            p_ts = k.split('_')[0]
                        break
                
                if p_ts and p_ts != last_alerted_ts:
                    diff = (datetime.now(timezone(timedelta(hours=9))) - datetime.strptime(p_ts, "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600.0
                    if diff >= float(sett.get("pee_interval", 5.0)):
                        send_tg_msg(sett["tg_token"], sett["tg_chat_id"], "🚨 [관제센터] 소변 인터벌을 초과했습니다!")
                        alert_t = now_kst().strftime("%Y-%m-%d %H:%M:%S_%f")
                        requests.patch(f"{FIREBASE_URL}users/{user_id}/logs.json", json={alert_t: f"📱 알림 발송 ({sett['pee_interval']}시간 경과)"})
                        last_alerted_ts = p_ts
            except: pass
    t = threading.Thread(target=job, daemon=True); t.start(); return t

start_bg_monitor(username)

# ==========================================
# 🎨 UI / CSS
# ==========================================
st.markdown(f"""
<style>
.stApp {{ background-color: #f8fafc !important; }}
.block-container {{ padding: 1.5rem 1rem 6rem 1rem !important; max-width: 600px !important; }}
.header-card {{
    display:flex; justify-content:space-between; align-items:center; 
    background:linear-gradient(135deg, #f0f9ff, #e0f2fe); border-radius:24px; padding: 25px; 
    margin-bottom:20px; color:#0f172a; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
}} 
/* 잔상 방지 패치 */
#vg-tooltip-element, .vg-tooltip, canvas {{ pointer-events: none !important; display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 📊 관제 데이터 계산 (수동 시간 동기화 패치)
# ==========================================
if 'settings' not in st.session_state: st.session_state.settings = load_settings()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()
df = st.session_state.pet_logs

def get_event_time(kw):
    if df.empty: return None, ""
    for i in range(len(df)-1, -1, -1):
        act = str(df.iloc[i]['활동'])
        t = str(df.iloc[i]['시간'])
        if kw in act:
            if any(x in act for x in ['차감', '리셋', '끄기']): continue
            # 수동 조절 데이터 완벽 파싱
            if '(수정)' in act and '[' in act and ']' in act:
                try:
                    ext_time = act.split('[')[1].split(']')[0]
                    date_part = t.split(' ')[0]
                    return f"{date_part} {ext_time}", act
                except: pass
            return t.split('_')[0], act
    return None, ""

p_time_raw, _ = get_event_time("소변")
a_time_raw, _ = get_event_time("알림 발송")
d_time_raw, _ = get_event_time("대변")

# 소변 예상/상태 로직
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

# ==========================================
# 🧱 타이머 렌더링 (초 단위 생략 & 가독성 향상)
# ==========================================
def render_timer():
    intv_h = float(st.session_state.settings.get("pee_interval", 5.0))
    ALARM_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"
    
    components.html(f"""
    <div style="display:flex; flex-direction:row; gap:15px; font-family:'Malgun Gothic', sans-serif; width: 100%;">
        
        <div id="p_card" style="flex:3; background:#ffffff; border-radius:20px; padding:20px 15px; box-shadow:0 4px 15px rgba(0,0,0,0.04); border: 2px solid #e0f2fe; display: flex; flex-direction: column; justify-content: space-between; min-height:160px; transition: all 0.5s ease;">
            <div style="font-size:1.0rem; font-weight:900; color:#0284c7; margin-bottom:15px; text-align:center;">💧 소변 관제</div>
            
            <div style="display:flex; align-items:center; justify-content:space-around; flex:1;">
                <div style="text-align:center; flex:1.2;">
                    <div style="font-size:0.85rem; font-weight:800; color:#64748b; margin-bottom:5px;">남은 시간</div>
                    <div id="p_rem" style="font-size:2.5rem; font-weight:900; color:#0369a1; letter-spacing:2px; line-height:1.0;">--:--</div>
                </div>
                
                <div style="border-left: 2px dashed #f1f5f9; padding-left: 15px; flex:1; display:flex; flex-direction:column; gap:8px;">
                    <div style="font-size:0.9rem; color:#334155;">최근 <span style="font-weight:900; float:right;">{p_disp}</span></div>
                    <div style="font-size:0.9rem; color:#0284c7;">예상 <span style="font-weight:900; float:right;">{p_expect}</span></div>
                    <div style="margin-top: 5px; font-size: 0.8rem; font-weight: 800; color: {msg_color}; background: #f8fafc; padding: 6px 0; border-radius: 6px; text-align:center; width:100%;">[{msg_status}]</div>
                </div>
            </div>
        </div>

        <div id="d_card" style="flex:2; background:#ffffff; border-radius:20px; padding:20px 15px; box-shadow:0 4px 15px rgba(0,0,0,0.04); border: 2px solid #ffedd5; text-align:center; display: flex; flex-direction: column; justify-content: center; min-height:160px;">
            <div style="font-size:1.0rem; font-weight:900; color:#c2410c; margin-bottom:15px;">💩 대변 타이머</div>
            <div style="font-size:0.85rem; font-weight:800; color:#64748b; margin-bottom:5px;">경과 시간</div>
            <div id="d_elap" style="font-size:2.5rem; font-weight:900; color:#9a3412; letter-spacing:2px; line-height:1.0;">--:--</div>
            <div style="font-size:0.85rem; color:#64748b; margin-top:15px; border-top: 2px dashed #f1f5f9; padding-top: 10px; font-weight:700;">최근 발생: <span style="color:#334155;">{d_disp}</span></div>
        </div>
        
    </div>
    <audio id="alarm_sound" src="{ALARM_URL}" preload="auto"></audio>
    
    <script>
        const P_LIMIT = {intv_h} * 3600000;
        let isAlarmed = false;

        function upd() {{
            const now = new Date();
            const p_iso = "{p_iso}";
            const p_rem_el = document.getElementById('p_rem');
            const p_card = document.getElementById('p_card');
            const audio = document.getElementById('alarm_sound');

            if(p_iso) {{
                const diff = now - new Date(p_iso);
                if(diff >= 0) {{
                    const rem = P_LIMIT - diff;
                    const r_abs = Math.abs(rem);
                    // 초(r_s) 생략하고 시, 분만 표시
                    const r_h = Math.floor(r_abs/3600000), r_m = Math.floor((r_abs%3600000)/60000);
                    const sign = rem < 0 ? "-" : "";
                    
                    p_rem_el.innerText = sign + String(r_h).padStart(2,'0') + ":" + String(r_m).padStart(2,'0');
                    
                    if (rem < 0) {{ 
                        p_rem_el.style.color = "#ef4444"; 
                        p_card.style.background = "#fff1f2";
                        if(!isAlarmed) {{ audio.play().catch(e => console.log(e)); isAlarmed = true; }}
                    }} else {{ 
                        p_rem_el.style.color = "#0369a1"; 
                        p_card.style.background = "#ffffff";
                        isAlarmed = false;
                    }}
                }}
            }}
            
            const d_iso = "{d_iso}";
            if(d_iso) {{
                const diff = now - new Date(d_iso);
                if(diff >= 0) {{
                    const d_h = Math.floor(diff/3600000), d_m = Math.floor((diff%3600000)/60000);
                    document.getElementById('d_elap').innerText = String(d_h).padStart(2,'0') + ":" + String(d_m).padStart(2,'0');
                }}
            }}
        }}
        // 1초 주기로 실행하되 시/분만 갱신되므로 시각적 피로도 하락
        setInterval(upd, 1000); upd();
    </script>
    """, height=180)

# ==========================================
# 🏠 사이드바 & 메인 UI
# ==========================================
with st.sidebar:
    st.markdown(f"### ⚙️ {username}님")
    if st.button("🔒 로그아웃", use_container_width=True):
        cookie_manager.delete("saved_username"); st.session_state.logged_in = False; st.rerun()
    
    with st.expander("⏰ 알람 및 배치 설정"):
        c1, c2 = st.columns([6, 4])
        with c1: ni = st.number_input("인터벌(H)", 0.5, 24.0, float(st.session_state.settings.get('pee_interval', 5.0)), 0.5)
        with c2: 
            if st.button("💾 저장", key="sv_int"):
                st.session_state.settings['pee_interval'] = ni
                save_settings(st.session_state.settings); st.rerun()
        
        st.markdown("**메뉴 순서**")
        new_order = {}
        for k, v in st.session_state.settings.get('order', {}).items():
            new_order[k] = st.number_input(k, 1, 20, int(v))
        if st.button("테마/배치 저장"):
            st.session_state.settings['order'] = new_order; save_settings(st.session_state.settings); st.rerun()

# 메인 렌더링
st.markdown(f"<div class='header-card'><div><div style='font-size:1.6rem; font-weight:900; color:#0f172a;'>🐾 {st.session_state.profile.get('pet_name','강아지')} 센터</div><div style='font-size:0.85rem; font-weight:700; color:#475569;'>{now_kst().strftime('%m월 %d일 (%a) %H:%M')}</div></div><div style='text-align:right; font-size:0.75rem; color:#64748b; font-weight:600;'>{APP_VERSION}</div></div>", unsafe_allow_html=True)

ui_order = st.session_state.settings.get('order', {"타이머":1, "누적데이터":2, "배변기록":3, "산책기록":4, "활동로그":5})

def get_count(kw, check_df):
    if check_df.empty: return 0
    p, m = 0, 0
    for act in check_df['활동'].astype(str):
        if kw in act:
            if '차감' in act: m += 1
            elif any(x in act for x in ['리셋','끄기','알림']): pass
            else: p += 1
    return max(0, p - m)

for mod_name, _ in sorted(ui_order.items(), key=lambda x: int(x[1])):
    if mod_name == "타이머": render_timer()
    elif mod_name == "누적데이터": 
        p_cnt = get_count("소변", df[df['시간'].str.startswith(t_date)])
        d_cnt = get_count("대변", df[df['시간'].str.startswith(t_date)])
        w_cnt = get_count("산책", df[df['시간'].str.startswith(t_date)])
        st.markdown(f"""
        <div style="background:#ffffff; border-radius:24px; padding:20px; box-shadow:0 4px 12px rgba(0,0,0,0.04); margin-bottom:15px;">
            <div style="font-size:0.9rem; font-weight:800; color:#475569; margin-bottom:12px;">✨ 오늘의 달성 현황</div>
            <div style="display: flex; flex-direction: row; justify-content: space-between; gap: 10px; width: 100%;">
                <div style="flex: 1; border-radius: 18px; padding: 15px 5px; text-align: center; border: 1px solid transparent; background: #f0f9ff; border-color: #e0f2fe;">
                    <div style="font-size: 0.8rem; font-weight: 800; margin-bottom: 6px; color: #0284c7;">💧 소변</div>
                    <div style="font-size: 1.8rem; font-weight: 900; line-height: 1.1; color: #0369a1;">{p_cnt}회</div>
                </div>
                <div style="flex: 1; border-radius: 18px; padding: 15px 5px; text-align: center; border: 1px solid transparent; background: #fff7ed; border-color: #ffedd5;">
                    <div style="font-size: 0.8rem; font-weight: 800; margin-bottom: 6px; color: #c2410c;">💩 대변</div>
                    <div style="font-size: 1.8rem; font-weight: 900; line-height: 1.1; color: #9a3412;">{d_cnt}회</div>
                </div>
                <div style="flex: 1; border-radius: 18px; padding: 15px 5px; text-align: center; border: 1px solid transparent; background: #ecfccb; border-color: #d9f99d;">
                    <div style="font-size: 0.8rem; font-weight: 800; margin-bottom: 6px; color: #4d7c0f;">🐾 산책</div>
                    <div style="font-size: 1.8rem; font-weight: 900; line-height: 1.1; color: #3f6212;">{w_cnt}회</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif mod_name == "배변기록":
        b1, b2 = st.columns(2)
        with b1: 
            if st.button("💧 실내 소변", use_container_width=True): add_record("💦 집에서 소변")
        with b2:
            if st.button("💩 실내 대변", use_container_width=True): add_record("💩 집에서 대변")
    elif mod_name == "활동로그":
        with st.expander("📋 활동 로그", expanded=False):
            if not df.empty:
                st.dataframe(df.sort_values("시간", ascending=False), use_container_width=True)
    elif mod_name == "수동조절":
        with st.expander("⚙️ 타이머 수동 조절"):
            t1, t2 = st.tabs(["💧 소변", "💩 대변"])
            with t1:
                p_w = st.time_input("시간 선택", now_kst().time(), key="p_w")
                if st.button("시간 저장", key="b_pw", use_container_width=True): add_record(f"💦 소변(수정) [{p_w.strftime('%H:%M:%S')}] (통계제외)")
            with t2:
                d_w = st.time_input("시간 선택", now_kst().time(), key="d_w")
                if st.button("시간 저장", key="b_dw", use_container_width=True): add_record(f"💩 대변(수정) [{d_w.strftime('%H:%M:%S')}] (통계제외)")
    elif mod_name == "기록차감":
        with st.expander("➖ 기록 차감"):
            a1, a2, a3 = st.columns(3)
            if a1.button("💧 -1", use_container_width=True): add_record("💦 소변 차감 (-1)")
            if a2.button("💩 -1", use_container_width=True): add_record("💩 대변 차감 (-1)")
            if a3.button("🐾 -1", use_container_width=True): add_record("🦮 산책 차감 (-1)")

st.divider()
if not df.empty:
    last = df.iloc[-1]
    if st.button(f"❌ 직전 취소: {last['활동']}", use_container_width=True):
        requests.delete(f"{FIREBASE_URL}users/{username}/logs/{last['시간']}.json"); st.rerun()

st.markdown(f"<div style='text-align:center; color:#94a3b8; font-size:0.7rem; padding-bottom:30px;'>🐾 Smart Pet Care Center | Update: {UPDATE_DATE}</div>", unsafe_allow_html=True)

# END

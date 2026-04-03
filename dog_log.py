import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import requests
import extra_streamlit_components as stx
import time
from urllib.parse import quote  # ✅ Fix 1: URL 인코딩 추가

# ==========================================
# 0. 기본 설정
# ==========================================
APP_VERSION = "v14.0.0 (프리미엄 카드 UI & 원형 타이머)"
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
                        default_settings = {
                            "btn_h": 4.2, "hdr_color": "#64748b",
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
        "btn_h": 4.2, "hdr_color": "#64748b",
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
        # ✅ Fix 2: 가계부 키 URL 인코딩 (공백·콜론 등 처리)
        key_encoded = quote(str(key), safe='')
        requests.delete(f"{FIREBASE_URL}users/{username}/ledger/{key_encoded}.json", timeout=5).raise_for_status()
        st.session_state.pet_ledger = st.session_state.pet_ledger[st.session_state.pet_ledger["키"] != key].reset_index(drop=True)
        st.rerun()
    except:
        st.error("⚠️ 삭제 실패")

if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'settings' not in st.session_state: st.session_state.settings = load_settings()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()
if 'pet_ledger' not in st.session_state: st.session_state.pet_ledger = load_ledger()

# ==========================================
# 🎨 프리미엄 UI / 동적 CSS 인젝션
# ==========================================
DYNAMIC_BTN_H = st.session_state.settings.get("btn_h", 4.0)
DYNAMIC_HDR_COLOR = st.session_state.settings.get("hdr_color", "#475569")

st.markdown(f"""
<style>
/* 1. 아주 연한 미색 배경으로 눈의 피로도 감소 */
.stApp {{ background-color: #f8fafc !important; }}
.block-container {{ padding: 1.5rem 1rem 6rem 1rem !important; max-width: 550px !important; }}
::-webkit-scrollbar {{ width: 0px; }}

/* 2. 네츄럴 톤의 세련된 헤더 카드 */
.header-card {{
    display:flex; justify-content:space-between; align-items:center;
    background:linear-gradient(135deg, #334155, #1e293b);
    border-radius:24px;
    padding: 30px 25px 25px 25px;
    margin-bottom:20px; color:white;
    min-height: 95px; line-height: 1.4;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.15);
}}

/* 3. 흰색 카드형 모듈 스타일 (Glass/Neumorphism) */
div[data-testid="stExpander"] {{
    background-color: #ffffff !important;
    border: none !important;
    border-radius: 20px !important;
    box-shadow: 0 8px 24px rgba(149, 157, 165, 0.08) !important;
    margin-bottom: 18px !important;
    overflow: hidden !important;
}}
div[data-testid="stExpander"] details {{ border: none !important; }}

/* 4. 아이콘 중심의 고급스러운 버튼 디자인 */
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

/* 대시보드 메트릭스 */
.horizontal-metrics {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 5px; }}
.metric-box {{
    flex: 1; border-radius: 18px; padding: 15px 5px;
    text-align: center; border: 1px solid transparent;
}}
.metric-label {{ font-size: 0.8rem; font-weight: 800; margin-bottom: 6px; }}
.metric-value {{ font-size: 1.8rem; font-weight: 900; line-height: 1.1; }}

.section-header {{
    font-size: 0.9rem; font-weight: 800; color: {DYNAMIC_HDR_COLOR};
    letter-spacing: 0.5px; margin: 15px 0 12px 5px;
}}

.health-row {{
    display: flex; justify-content: space-between; align-items: center;
    background: #f8fafc; padding: 12px 18px; border-radius: 14px; margin-bottom: 10px;
    border: 1px solid #f1f5f9;
}}
.last-date {{ font-size: 0.75rem; color: #64748b; font-weight: 700; text-align: right; }}
.d-day-badge {{
    background: #e2e8f0; color: #334155; padding: 4px 8px; border-radius: 8px;
    font-size: 0.75rem; margin-left: 8px; font-weight: 800;
}}

.stTabs [data-baseweb="tab-list"] {{ gap: 20px !important; justify-content: center !important; }}
.stTabs [data-baseweb="tab"] {{ height: 3.2rem !important; font-weight: 800 !important; padding: 0 15px !important; }}
hr {{ margin: 15px 0 !important; border-color: #f1f5f9 !important; }}
.streamlit-expanderHeader {{ font-weight: 800 !important; font-size: 1rem !important; color: #1e293b !important; padding: 15px 20px !important; }}

@media (max-width: 768px) {{
    div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important;
        gap: 12px !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 사이드바
# ==========================================
with st.sidebar:
    st.markdown(f"### ⚙️ {username}님")
    _ldg = st.session_state.pet_ledger
    _cur_month = now_kst().strftime("%Y-%m")
    _monthly_total = int(_ldg[_ldg["날짜"].astype(str).str.startswith(_cur_month)]["금액"].sum()) if not _ldg.empty else 0
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#334155,#1e293b); border-radius:18px; padding:16px 16px; color:white; margin-bottom:15px; text-align:center;'>
        <div style='font-size:0.75rem; font-weight:800; opacity:0.9; letter-spacing:0.5px;'>💰 {now_kst().strftime("%m월")} 총지출</div>
        <div style='font-size:2.2rem; font-weight:900; line-height:1.2; margin-top:5px;'>{_monthly_total:,}원</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔒 로그아웃", use_container_width=True):
        cookie_manager.delete("saved_username")
        st.session_state.force_logout = True
        st.session_state.logged_in = False
        time.sleep(0.3); st.rerun()

    st.caption(f"📌 버전: {APP_VERSION}")
    st.divider()

    with st.expander("🎨 UI 설정", expanded=False):
        new_btn_h = st.slider("버튼 높이", 3.0, 6.0, float(st.session_state.settings.get('btn_h', 4.0)), 0.1)
        new_hdr_c = st.color_picker("섹션 헤더 색상", st.session_state.settings.get('hdr_color', '#475569'))

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
    <div style="display:flex; justify-content:space-between; gap:15px; font-family:sans-serif;">
        <div style="flex:1; background:#ffffff; border-radius:24px; padding:20px 10px; text-align:center; box-shadow:0 8px 24px rgba(149,157,165,0.08); position:relative;">
            <div style="font-size:0.9rem; font-weight:800; color:#0284c7; letter-spacing:0.5px; margin-bottom:10px;">💧 소변</div>
            <div style="position:relative; width:110px; height:110px; margin:0 auto;">
                <svg viewBox="0 0 36 36" style="width:100%; height:100%;">
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#f0f9ff" stroke-width="3" />
                    <path id="p_circ" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#38bdf8" stroke-width="3" stroke-dasharray="0, 100" stroke-linecap="round" style="transition: stroke-dasharray 1s ease-out;" />
                </svg>
                <div id="p_tm" style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:1.6rem; font-weight:900; color:#0369a1; letter-spacing:1px;">--:--</div>
            </div>
            <div style="margin-top:12px; font-size:0.75rem; font-weight:800; color:#94a3b8;">최근 <span style="color:#0284c7;">{p_time_str}</span></div>
        </div>

        <div style="flex:1; background:#ffffff; border-radius:24px; padding:20px 10px; text-align:center; box-shadow:0 8px 24px rgba(149,157,165,0.08); position:relative;">
            <div style="font-size:0.9rem; font-weight:800; color:#c2410c; letter-spacing:0.5px; margin-bottom:10px;">💩 대변</div>
            <div style="position:

검토 완료했습니다. 발견된 버그들:

Firebase DELETE URL 인코딩 버그 — 타임스탬프에 공백/콜론이 있어 삭제 요청이 실패함 (urllib.parse.quote 필요)
직전 취소 후 세션 상태 미업데이트 — Firebase에서는 삭제되지만 st.session_state.pet_logs가 갱신 안 됨 (화면에 여전히 남아 있음)
가계부 삭제도 같은 URL 인코딩 버그 존재
헤더 요일이 영문 표시 — %a가 Mon/Tue 등 영문으로 나옴 → 한국어 변환 필요
아래가 수정된 전체 코드입니다:

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import requests
import extra_streamlit_components as stx
import time
from urllib.parse import quote

# ==========================================
# 0. 기본 설정
# ==========================================
APP_VERSION = "v14.1.0 (버그 수정: 삭제/요일/세션)"
UPDATE_DATE = "2026-04-03"

KST = timezone(timedelta(hours=9))
def now_kst(): return datetime.now(KST)
FIREBASE_URL = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/"

KOR_WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

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
                        default_settings = {
                            "btn_h": 4.2, "hdr_color": "#64748b",
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
        "btn_h": 4.2, "hdr_color": "#64748b",
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
        # [수정] 타임스탬프 키에 공백/콜론이 있어 URL 인코딩 필수
        key_encoded = quote(str(key), safe='')
        requests.delete(f"{FIREBASE_URL}users/{username}/ledger/{key_encoded}.json", timeout=5).raise_for_status()
        st.session_state.pet_ledger = st.session_state.pet_ledger[st.session_state.pet_ledger["키"] != key].reset_index(drop=True)
        st.rerun()
    except:
        st.error("⚠️ 삭제 실패")

if 'profile' not in st.session_state: st.session_state.profile = load_profile()
if 'settings' not in st.session_state: st.session_state.settings = load_settings()
if 'pet_logs' not in st.session_state: st.session_state.pet_logs = load_data()
if 'pet_ledger' not in st.session_state: st.session_state.pet_ledger = load_ledger()

# ==========================================
# 🎨 프리미엄 UI / 동적 CSS 인젝션
# ==========================================
DYNAMIC_BTN_H = st.session_state.settings.get("btn_h", 4.0)
DYNAMIC_HDR_COLOR = st.session_state.settings.get("hdr_color", "#475569")

st.markdown(f"""
<style>
/* 1. 아주 연한 미색 배경으로 눈의 피로도 감소 */
.stApp {{ background-color: #f8fafc !important; }}
.block-container {{ padding: 1.5rem 1rem 6rem 1rem !important; max-width: 550px !important; }}
::-webkit-scrollbar {{ width: 0px; }}

/* 2. 네츄럴 톤의 세련된 헤더 카드 */
.header-card {{
    display:flex; justify-content:space-between; align-items:center;
    background:linear-gradient(135deg, #334155, #1e293b);
    border-radius:24px;
    padding: 30px 25px 25px 25px;
    margin-bottom:20px; color:white;
    min-height: 95px; line-height: 1.4;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.15);
}}

/* 3. 흰색 카드형 모듈 스타일 (Glass/Neumorphism) */
div[data-testid="stExpander"] {{
    background-color: #ffffff !important;
    border: none !important;
    border-radius: 20px !important;
    box-shadow: 0 8px 24px rgba(149, 157, 165, 0.08) !important;
    margin-bottom: 18px !important;
    overflow: hidden !important;
}}
div[data-testid="stExpander"] details {{ border: none !important; }}

/* 4. 아이콘 중심의 고급스러운 버튼 디자인 */
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

/* 대시보드 메트릭스 */
.horizontal-metrics {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 5px; }}
.metric-box {{
    flex: 1; border-radius: 18px; padding: 15px 5px;
    text-align: center; border: 1px solid transparent;
}}
.metric-label {{ font-size: 0.8rem; font-weight: 800; margin-bottom: 6px; }}
.metric-value {{ font-size: 1.8rem; font-weight: 900; line-height: 1.1; }}

.section-header {{
    font-size: 0.9rem; font-weight: 800; color: {DYNAMIC_HDR_COLOR};
    letter-spacing: 0.5px; margin: 15px 0 12px 5px;
}}

.health-row {{
    display: flex; justify-content: space-between; align-items: center;
    background: #f8fafc; padding: 12px 18px; border-radius: 14px; margin-bottom: 10px;
    border: 1px solid #f1f5f9;
}}
.last-date {{ font-size: 0.75rem; color: #64748b; font-weight: 700; text-align: right; }}
.d-day-badge {{
    background: #e2e8f0; color: #334155; padding: 4px 8px; border-radius: 8px;
    font-size: 0.75rem; margin-left: 8px; font-weight: 800;
}}

.stTabs [data-baseweb="tab-list"] {{ gap: 20px !important; justify-content: center !important; }}
.stTabs [data-baseweb="tab"] {{ height: 3.2rem !important; font-weight: 800 !important; padding: 0 15px !important; }}
hr {{ margin: 15px 0 !important; border-color: #f1f5f9 !important; }}
.streamlit-expanderHeader {{ font-weight: 800 !important; font-size: 1rem !important; color: #1e293b !important; padding: 15px 20px !important; }}

@media (max-width: 768px) {{
    div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important;
        gap: 12px !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 사이드바
# ==========================================
with st.sidebar:
    st.markdown(f"### ⚙️ {username}님")
    _ldg = st.session_state.pet_ledger
    _cur_month = now_kst().strftime("%Y-%m")
    _monthly_total = int(_ldg[_ldg["날짜"].astype(str).str.startswith(_cur_month)]["금액"].sum()) if not _ldg.empty else 0
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#334155,#1e293b); border-radius:18px; padding:16px 16px; color:white; margin-bottom:15px; text-align:center;'>
        <div style='font-size:0.75rem; font-weight:800; opacity:0.9; letter-spacing:0.5px;'>💰 {now_kst().strftime("%m월")} 총지출</div>
        <div style='font-size:2.2rem; font-weight:900; line-height:1.2; margin-top:5px;'>{_monthly_total:,}원</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔒 로그아웃", use_container_width=True):
        cookie_manager.delete("saved_username")
        st.session_state.force_logout = True
        st.session_state.logged_in = False
        time.sleep(0.3); st.rerun()

    st.caption(f"📌 버전: {APP_VERSION}")
    st.divider()

    with st.expander("🎨 UI 설정", expanded=False):
        new_btn_h = st.slider("버튼 높이", 3.0, 6.0, float(st.session_state.settings.get('btn_h', 4.0)), 0.1)
        new_hdr_c = st.color_picker("섹션 헤더 색상", st.session_state.settings.get('hdr_color', '#475569'))

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
    <div style="display:flex; justify-content:space-between; gap:15px; font-family:sans-serif;">
        <div style="flex:1; background:#ffffff; border-radius:24px; padding:20px 10px; text-align:center; box-shadow:0 8px 24px rgba(149,157,165,0.08); position:relative;">
            <div style="font-size:0.9rem; font-weight:800; color:#0284c7; letter-spacing:0.5px; margin-bottom:10px;">💧 소변</div>
            <div style="position:relative; width:110px; height:110px; margin:0 auto;">
                <svg viewBox="0 0 36 36" style="width:100%; height:100%;">
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#f0f9ff" stroke-width="3" />
                    <path id="p_circ" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#38bdf8" stroke-width="3" stroke-dasharray="0, 100" stroke-linecap="round" style="transition: stroke-dasharray 1s ease-out;" />
                </svg>
                <div id="p_tm" style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:1.6rem; font-weight:900; color:#0369a1; letter-spacing:1px;">--:--</div>
            </div>
            <div style="margin-top:12px; font-size:0.75rem; font-weight:800; color:#94a3b8;">최근 <span style="color:#0284c7;">{p_time_str}</span></div>
        </div>

        <div style="flex:1; background:#ffffff; border-radius:24px; padding:20px 10px; text-align:center; box-shadow:0 8px 24px rgba(149,157,165,0.08); position:relative;">
            <div style="font-size:0.9rem; font-weight:800; color:#c2410c; letter-spacing:0.5px; margin-bottom:10px;">💩 대변</div>
            <div style="position:relative; width:110px; height:110px; margin:0 auto;">
                <svg viewBox="0 0 36 36" style="width:100%; height:100%;">
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#fff7ed" stroke-width="3" />
                    <path id="d_circ" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#fb923c" stroke-width="3" stroke-dasharray="0, 100" stroke-linecap="round" style="transition: stroke-dasharray 1s ease-out;" />
                </svg>
                <div id="d_tm" style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:1.6rem; font-weight:900; color:#9a3412; letter-spacing:1px;">--:--</div>
            </div>
            <div style="margin-top:12px; font-size:0.75rem; font-weight:800; color:#94a3b8;">최근 <span style="color:#c2410c;">{d_time_str}</span></div>
        </div>
    </div>
    <script>
        const MAX_MS = 43200000;
        function upP(){{
            const el=document.getElementById('p_tm'), circ=document.getElementById('p_circ'), iso="{p_iso}";
            if(!iso){{el.innerText="--:--"; return;}}
            const diff=new Date()-new Date(iso); if(diff<0)return;
            const m=Math.floor(diff/60000);
            el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0');
            const pct = Math.min((diff/MAX_MS)*100, 100); circ.setAttribute('stroke-dasharray', pct + ', 100');
        }}
        function upD(){{
            const el=document.getElementById('d_tm'), circ=document.getElementById('d_circ'), iso="{d_iso}";
            if(!iso){{el.innerText="--:--"; return;}}
            const diff=new Date()-new Date(iso); if(diff<0)return;
            const m=Math.floor(diff/60000);
            el.innerText=String(Math.floor(m/60)).padStart(2,'0')+":"+String(m%60).padStart(2,'0');
            const pct = Math.min((diff/MAX_MS)*100, 100); circ.setAttribute('stroke-dasharray', pct + ', 100');
        }}
        setInterval(()=>{{upP();upD();}},1000); upP(); upD();
    </script>
    """, height=220)

def render_summary():
    p, d, w = get_real_count('소변', target_df), get_real_count('대변', target_df), get_real_count('산책', target_df)
    st.markdown(f"""
    <div style="background:#ffffff; border-radius:24px; padding:25px 20px; box-shadow:0 8px 24px rgba(149,157,165,0.08); margin-bottom:20px;">
        <div style="font-size:0.9rem; font-weight:800; color:#475569; letter-spacing:0.5px; margin-bottom:18px;">✨ 오늘의 달성 현황</div>
        <div class="horizontal-metrics">
            <div class="metric-box" style="background:#f0f9ff; border-color:#e0f2fe;"><div class="metric-label" style="color:#0284c7;">💧 소변</div><div class="metric-value" style="color:#0369a1;">{p}회</div></div>
            <div class="metric-box" style="background:#fff7ed; border-color:#ffedd5;"><div class="metric-label" style="color:#c2410c;">💩 대변</div><div class="metric-value" style="color:#9a3412;">{d}회</div></div>
            <div class="metric-box" style="background:#ecfccb; border-color:#d9f99d;"><div class="metric-label" style="color:#4d7c0f;">🐾 산책</div><div class="metric-value" style="color:#3f6212;">{w}회</div></div>
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
                save_settings(st.session_state.settings)
                st.rerun()

            t_val = st.text_input("메모 (예: 심장사상충)", key="t_mh", placeholder="음성/키보드 입력")
            if st.button("🏥 기록 저장", use_container_width=True):
                add_record(f"🏥 병원/약: {t_val}" if t_val else "🏥 병원/약", f"{d_val} {ts}")
        with c2:
            date_mh, memo_mh = get_record_for_date("🏥 병원/약", d_val.strftime("%Y-%m-%d"))
            st.markdown(f"""
            <div style='padding: 18px 15px; border-radius: 16px; min-height: 110px; display: flex; flex-direction: column; justify-content: center; background-color: #fefce8; border-left: 6px solid #facc15; box-shadow: 0 4px 10px rgba(0,0,0,0.02);'>
                <div style='font-size: 0.85rem; font-weight: 900; margin-bottom: 8px; color: #a16207;'>📌 선택일 진료/약</div>
                <div style='font-size: 1.1rem; font-weight: 900; color: #52525b; margin-bottom: 4px;'>📅 {date_mh}</div>
                <div style='font-size: 1.1rem; font-weight: 900; color: #422006; word-break: break-all; line-height: 1.4;'>📝 {memo_mh}</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

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
            <div style='padding: 18px 15px; border-radius: 16px; min-height: 110px; display: flex; flex-direction: column; justify-content: center; background-color: #fdf2f8; border-left: 6px solid #f472b6; box-shadow: 0 4px 10px rgba(0,0,0,0.02);'>
                <div style='font-size: 0.85rem; font-weight: 900; margin-bottom: 8px; color: #be185d;'>📌 선택일 미용 기록</div>
                <div style='font-size: 1.1rem; font-weight: 900; color: #52525b; margin-bottom: 4px;'>📅 {date_gr}</div>
                <div style='font-size: 1.1rem; font-weight: 900; color: #831843; word-break: break-all; line-height: 1.4;'>📝 {memo_gr}</div>
            </div>
            """, unsafe_allow_html=True)

def render_manual():
    with st.expander("⚙️ 타이머 수동 조절"):
        st.info("오늘 날짜를 기준으로 시간을 수정합니다.")
        t1, t2 = st.tabs(["💧 소변", "💩 대변"])
        with t1:
            tw1, tk1 = st.tabs(["⏱️ 휠", "⌨️ 키보드"])
            with tw1:
                p_wheel = st.time_input("시간 선택", now_kst().time(), key="p_wheel")
                if st.button("시간 저장", key="bp_w", use_container_width=True):
                    add_record(f"💦 소변(수정) [{p_wheel.strftime('%H:%M:%S')}] (통계제외)")
            with tk1:
                p_txt = st.text_input("시간 입력 (HH:MM)", value=now_kst().strftime("%H:%M"), key="p_txt")
                if st.button("시간 저장", key="bp_k", use_container_width=True):
                    try:
                        vt = datetime.strptime(p_txt, '%H:%M').strftime('%H:%M:00')
                        add_record(f"💦 소변(수정) [{vt}] (통계제외)")
                    except: st.error("HH:MM 형식!")
            if st.button("🔄 리셋", use_container_width=True, key="bp_r"): add_record("💦 소변 리셋 (통계제외)")
        with t2:
            tw2, tk2 = st.tabs(["⏱️ 휠", "⌨️ 키보드"])
            with tw2:
                d_wheel = st.time_input("시간 선택", now_kst().time(), key="d_wheel")
                if st.button("시간 저장", key="bd_w", use_container_width=True):
                    add_record(f"💩 대변(수정) [{d_wheel.strftime('%H:%M:%S')}] (통계제외)")
            with tk2:
                d_txt = st.text_input("시간 입력 (HH:MM)", value=now_kst().strftime("%H:%M"), key="d_txt")
                if st.button("시간 저장", key="bd_k", use_container_width=True):
                    try:
                        vt = datetime.strptime(d_txt, '%H:%M').strftime('%H:%M:00')
                        add_record(f"💩 대변(수정) [{vt}] (통계제외)")
                    except: st.error("HH:MM 형식!")
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

def render_ledger():
    st.markdown("""
    <style>
    div[data-testid="stExpander"]:has(.ledger-unique-marker) > details > summary {
        padding: 16px 15px !important;
        background: linear-gradient(135deg, #f8fafc, #e2e8f0) !important;
        border-radius: 18px !important;
        margin-bottom: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
    }
    div[data-testid="stExpander"]:has(.ledger-unique-marker) > details > summary p {
        font-size: 1.15rem !important;
        font-weight: 900 !important;
        color: #0f172a !important;
    }
    div[data-testid="stExpander"]:has(.ledger-unique-marker) > details > summary svg {
        width: 1.4rem !important;
        height: 1.4rem !important;
        color: #475569 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.expander("💰 반려견 가계부 (터치하여 펼치기)", expanded=False):
        st.markdown('<div class="ledger-unique-marker"></div>', unsafe_allow_html=True)

        CATS = ["사료", "간식", "배변패드", "의료비", "기타"]
        CAT_ICONS = {"사료": "🍚", "간식": "🦴", "배변패드": "📦", "의료비": "🏥", "기타": "📝"}

        ldg = st.session_state.pet_ledger
        cur_month = now_kst().strftime("%Y-%m")
        monthly_ldg = ldg[ldg["날짜"].astype(str).str.startswith(cur_month)].copy() if not ldg.empty else pd.DataFrame(columns=["키","날짜","카테고리","금액","메모"])
        total = int(monthly_ldg["금액"].sum()) if not monthly_ldg.empty else 0

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#334155,#1e293b); border-radius:18px; padding:16px 20px; color:white; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;'>
            <div style='font-size:0.85rem; font-weight:800; opacity:0.9;'>💰 {now_kst().strftime("%m월")} 총지출</div>
            <div style='font-size:1.8rem; font-weight:900;'>{total:,}원</div>
        </div>
        """, unsafe_allow_html=True)

        if not monthly_ldg.empty:
            cat_totals = monthly_ldg.groupby("카테고리")["금액"].sum().to_dict()
            active_cats = [(c, cat_totals[c]) for c in CATS if c in cat_totals and cat_totals[c] > 0]
            if active_cats:
                boxes = "".join([
                    f"<div class='metric-box' style='background:#f8fafc;'><div class='metric-label'>{CAT_ICONS.get(c,'')}&nbsp;{c}</div><div style='font-size:1.1rem; font-weight:900; color:#0f172a;'>{int(amt):,}원</div></div>"
                    for c, amt in active_cats
                ])
                st.markdown(f"<div class='horizontal-metrics'>{boxes}</div>", unsafe_allow_html=True)

        with st.expander("➕ 지출 입력", expanded=False):
            lc1, lc2 = st.columns(2)
            with lc1:
                l_date = st.date_input("날짜", value=now_kst().date(), key="l_date")
                l_cat  = st.selectbox("카테고리", CATS, key="l_cat")
            with lc2:
                l_amt  = st.number_input("금액 (원)", min_value=0, step=100, key="l_amt")
                l_memo = st.text_input("메모", key="l_memo", placeholder="예: 로얄캐닌 2kg")
            if st.button("💾 지출 저장", use_container_width=True, type="primary", key="btn_ledger_save"):
                if l_amt > 0:
                    add_ledger_entry(l_date.strftime("%Y-%m-%d"), l_cat, int(l_amt), l_memo)
                else:
                    st.warning("금액을 입력하세요.")

        if not monthly_ldg.empty:
            disp = monthly_ldg[["날짜","카테고리","금액","메모"]].sort_values("날짜", ascending=False).reset_index(drop=True)
            disp.index += 1
            st.dataframe(disp, use_container_width=True, column_config={
                "날짜": st.column_config.TextColumn("📅 날짜", width="small"),
                "카테고리": st.column_config.TextColumn("🏷️", width="small"),
                "금액": st.column_config.NumberColumn("💰 금액", format="%d원"),
                "메모": st.column_config.TextColumn("📝 메모"),
            })
            last_row = monthly_ldg.sort_values("날짜", ascending=False).iloc[0]
            if st.button(f"❌ 직전 취소: {last_row['카테고리']} {int(last_row['금액']):,}원", use_container_width=True, key="btn_ledger_del"):
                delete_ledger_entry(str(last_row["키"]))
        else:
            st.info("이번 달 지출 내역이 없습니다.")

def render_stats():
    with st.expander("📊 주간 통계"):
        if df.empty: st.info("데이터 없음")
        else:
            w_dates = [(now_kst() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            w_data = [{"날짜": d[5:], "소변": get_real_count('소변', df[df['시간'].astype(str).str.startswith(d)]), "대변": get_real_count('대변', df[df['시간'].astype(str).str.startswith(d)]), "산책": get_real_count('산책', df[df['시간'].astype(str).str.startswith(d)])} for d in w_dates]
            st.bar_chart(pd.DataFrame(w_data).set_index("날짜"), color=["#bae6fd","#fed7aa","#d9f99d"])

# ==========================================
# 🏠 메인 렌더링
# ==========================================
pet_n = st.session_state.profile.get('pet_name','강아지')
last_up = str(df.iloc[-1]['시간'])[:19] if not df.empty else "없음"

# [수정] %a 대신 한국어 요일 딕셔너리 사용
_now = now_kst()
_kor_day = KOR_WEEKDAYS[_now.weekday()]
_date_display = _now.strftime(f"%m월 %d일 ({_kor_day}) %H:%M")

st.markdown(f"""
<div class="header-card">
    <div>
        <div style="font-size:1.6rem; font-weight:900; margin-bottom:5px;">🐾 {pet_n} 센터</div>
        <div style="font-size:0.85rem; font-weight:700; color:#cbd5e1;">{_date_display}</div>
    </div>
    <div style="text-align:right; font-size:0.75rem; color:#94a3b8; font-weight:600;">
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
        # [수정] URL 인코딩 + 세션 상태 동기화
        key_to_del = str(target_df.iloc[-1]['시간'])
        try:
            key_encoded = quote(key_to_del, safe='')
            requests.delete(f"{FIREBASE_URL}users/{username}/logs/{key_encoded}.json", timeout=5).raise_for_status()
            st.session_state.pet_logs = st.session_state.pet_logs[
                st.session_state.pet_logs["시간"] != key_to_del
            ].reset_index(drop=True)
            st.rerun()
        except: st.error("취소 실패")

st.markdown(f"""
<div style="text-align:center; color:#94a3b8; font-size:0.75rem; padding:20px 0 30px; font-weight:600;">
    🐾 Smart Pet Care Center<br>
    현재 버전: <strong>{APP_VERSION}</strong> | 업데이트: {UPDATE_DATE}
</div>
""", unsafe_allow_html=True)

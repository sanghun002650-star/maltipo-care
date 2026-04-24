"""
pee_alert_monitor.py  —  Smart Pet Care 클라우드 알림 데몬
===========================================================
Railway / Render / 라즈베리파이 등 24시간 서버에서 실행합니다.

Firebase DB를 주기적으로 조회하여 마지막 소변 기록이
사용자가 설정한 목표 간격(pee_interval)을 초과하면
텔레그램으로 알림 메시지를 발송합니다.

실행:
    pip install requests
    python pee_alert_monitor.py
"""

import time
import requests
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────
# 설정 (dog_log.py 와 동일한 값)
# ─────────────────────────────────────────────
FIREBASE_URL     = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/"
CHECK_EVERY_SEC  = 60       # Firebase 확인 주기 (초)
KST              = timezone(timedelta(hours=9))


def now_kst():
    return datetime.now(KST)


def send_telegram(token: str, chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        res.raise_for_status()
        print(f"[{now_kst():%H:%M:%S}] ✅ 텔레그램 전송 완료")
    except Exception as e:
        print(f"[{now_kst():%H:%M:%S}] ❌ 텔레그램 전송 실패: {e}")


def firebase_get(path: str):
    try:
        res = requests.get(f"{FIREBASE_URL}{path}.json", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"[{now_kst():%H:%M:%S}] ⚠️ Firebase 읽기 실패 ({path}): {e}")
    return None


def get_all_users() -> list:
    data = firebase_get("users")
    return list(data.keys()) if isinstance(data, dict) else []


def is_sleeping(now_dt: datetime, start_str: str, end_str: str) -> bool:
    """취침 시간대(DND)이면 True"""
    try:
        n_m = now_dt.hour * 60 + now_dt.minute
        sh, sm = map(int, start_str.split(':'))
        eh, em = map(int, end_str.split(':'))
        s_m, e_m = sh * 60 + sm, eh * 60 + em
        if s_m <= e_m:
            return s_m <= n_m <= e_m
        return n_m >= s_m or n_m <= e_m
    except Exception:
        return False


def get_last_pee(logs: dict):
    """마지막 소변 이벤트의 (raw_key, datetime) 반환"""
    for key in sorted(logs.keys(), reverse=True):
        act = str(logs[key])
        if "소변" not in act:
            continue
        if any(x in act for x in ["차감", "리셋", "끄기", "알림 발송"]):
            continue

        # 수정 기록이면 괄호 안 시각 추출
        if "(수정)" in act and "[" in act and "]" in act:
            try:
                ext_time = act.split("[")[1].split("]")[0]
                date_part = key.split(" ")[0]
                ts_str = f"{date_part} {ext_time}"
            except Exception:
                ts_str = key.split("_")[0]
        else:
            ts_str = key.split("_")[0]

        try:
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)
            return key, dt
        except ValueError:
            continue

    return None, None


# ─────────────────────────────────────────────
# 중복 발송 방지: 마지막으로 알림 보낸 이벤트 키 저장
# ─────────────────────────────────────────────
_last_alerted: dict = {}   # {username: raw_key}


def check_user(username: str):
    settings = firebase_get(f"users/{username}/settings")
    if not isinstance(settings, dict):
        return

    # 텔레그램 설정 확인
    if not settings.get("tg_enabled"):
        return
    tg_token   = settings.get("tg_token", "")
    tg_chat_id = settings.get("tg_chat_id", "")
    if not tg_token or not tg_chat_id:
        return

    now = now_kst()

    # 취침 시간대 → 알림 건너뜀
    if is_sleeping(now, settings.get("sleep_start", "22:00"), settings.get("sleep_end", "05:00")):
        return

    logs = firebase_get(f"users/{username}/logs")
    if not isinstance(logs, dict):
        return

    raw_key, last_pee_dt = get_last_pee(logs)
    if last_pee_dt is None:
        return

    interval_h  = float(settings.get("pee_interval", 5.0))
    interval_td = timedelta(hours=interval_h)
    elapsed     = now - last_pee_dt

    print(f"[{now:%H:%M:%S}] 👤 {username} | 마지막소변: {last_pee_dt:%H:%M} | "
          f"경과: {int(elapsed.total_seconds()//3600)}h{int((elapsed.total_seconds()%3600)//60)}m | "
          f"목표: {interval_h}h")

    if elapsed < interval_td:
        return                          # 아직 시간 안 됨

    if _last_alerted.get(username) == raw_key:
        return                          # 이미 이 이벤트로 알림 보냄

    # ── 알림 발송 ──
    over_sec = (elapsed - interval_td).total_seconds()
    over_h   = int(over_sec // 3600)
    over_m   = int((over_sec % 3600) // 60)
    time_str = f"{over_h}시간 {over_m}분" if over_h > 0 else f"{over_m}분"

    try:
        profile  = firebase_get(f"users/{username}/profile") or {}
        pet_name = profile.get("pet_name", "강아지")
    except Exception:
        pet_name = "강아지"

    msg = (
        f"🚨 <b>[Smart Pet Care] {pet_name} 소변 알람!</b>\n\n"
        f"⏰ 마지막 소변: <b>{last_pee_dt:%H:%M}</b>\n"
        f"📏 설정 간격: <b>{interval_h:.1f}시간</b>\n"
        f"🔴 초과 시간: <b>{time_str}</b>\n\n"
        f"💧 지금 바로 확인해 주세요!"
    )
    send_telegram(tg_token, tg_chat_id, msg)
    _last_alerted[username] = raw_key

    # 알림 기록을 Firebase 로그에 남김
    try:
        alert_ts  = now.strftime("%Y-%m-%d %H:%M:%S_%f")
        alert_act = f"📱 알림 발송 (소변 후 {time_str} 초과)"
        requests.patch(f"{FIREBASE_URL}users/{username}/logs.json",
                       json={alert_ts: alert_act}, timeout=5)
    except Exception:
        pass


def main():
    print("=" * 55)
    print("🐾 Smart Pet Care — 소변 알림 모니터 시작")
    print(f"   확인 주기 : {CHECK_EVERY_SEC}초")
    print(f"   시작 시각 : {now_kst():%Y-%m-%d %H:%M:%S} KST")
    print("=" * 55)

    while True:
        try:
            users = get_all_users()
            for u in users:
                check_user(u)
        except Exception as e:
            print(f"[{now_kst():%H:%M:%S}] ❌ 오류: {e}")
        time.sleep(CHECK_EVERY_SEC)


if __name__ == "__main__":
    main()

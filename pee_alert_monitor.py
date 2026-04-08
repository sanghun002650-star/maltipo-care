"""
pee_alert_monitor.py
====================
24시간 클라우드 서버에서 실행되는 소변 알림 스크립트.

Firebase DB를 주기적으로 확인하여, 마지막 소변 기록이
설정된 목표 간격(pee_interval_h)을 초과하면 텔레그램 메시지를 발송합니다.

실행 방법:
    pip install requests
    python pee_alert_monitor.py

배포 환경: Railway / Render / Google Cloud Run / 라즈베리파이 등
"""

import time
import requests
from datetime import datetime, timezone, timedelta

# ============================================================
# 설정 (Firebase URL 은 dog_log.py 와 동일하게 맞추세요)
# ============================================================
FIREBASE_URL  = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/"
TELEGRAM_TOKEN = "8560607237:AAH1HTdbxFsWGS8UFoNPAKsfmxr9wd2VNS0"
TELEGRAM_CHAT_ID = "8124116628"

CHECK_INTERVAL_SEC = 60   # Firebase 확인 주기 (초)
KST = timezone(timedelta(hours=9))

# ============================================================
# 헬퍼 함수
# ============================================================
def now_kst():
    return datetime.now(KST)

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
        res.raise_for_status()
        print(f"[{now_kst():%H:%M:%S}] ✅ 텔레그램 전송 완료")
    except Exception as e:
        print(f"[{now_kst():%H:%M:%S}] ❌ 텔레그램 전송 실패: {e}")

def get_firebase(path: str):
    try:
        res = requests.get(f"{FIREBASE_URL}{path}.json", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"[{now_kst():%H:%M:%S}] ⚠️ Firebase 읽기 실패: {e}")
    return None

def get_users() -> list:
    data = get_firebase("users")
    return list(data.keys()) if isinstance(data, dict) else []

def get_last_pee_time(username: str):
    """마지막 소변 기록의 datetime을 반환 (없으면 None)"""
    logs = get_firebase(f"users/{username}/logs")
    if not isinstance(logs, dict):
        return None
    pee_times = []
    for ts_key, activity in logs.items():
        if not isinstance(activity, str):
            continue
        if "소변" in activity and "차감" not in activity and "리셋" not in activity and "끄기" not in activity:
            # 타임스탬프 파싱 (형식: "2026-04-08 13:45:22_123456" 또는 "2026-04-08 13:45:22")
            ts_clean = ts_key.split("_")[0].strip()
            try:
                dt = datetime.strptime(ts_clean, "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)
                pee_times.append(dt)
            except ValueError:
                pass
    return max(pee_times) if pee_times else None

def get_interval_hours(username: str) -> float:
    settings = get_firebase(f"users/{username}/settings")
    if isinstance(settings, dict):
        return float(settings.get("pee_interval_h", 5.0))
    return 5.0

# ============================================================
# 알림 상태 추적 (메모리 기반 - 재시작 시 초기화됨)
# 같은 초과 구간에서 중복 발송 방지용
# ============================================================
# notified_at[username] = 마지막으로 알림을 보낸 소변 기록 시각
notified_at: dict = {}

# ============================================================
# 메인 루프
# ============================================================
def check_all_users():
    users = get_users()
    if not users:
        print(f"[{now_kst():%H:%M:%S}] 사용자 없음")
        return

    for username in users:
        last_pee = get_last_pee_time(username)
        if last_pee is None:
            continue

        interval_h = get_interval_hours(username)
        interval_td = timedelta(hours=interval_h)
        elapsed = now_kst() - last_pee
        remaining = interval_td - elapsed

        print(f"[{now_kst():%H:%M:%S}] 👤 {username} | 마지막소변: {last_pee:%H:%M} | "
              f"경과: {elapsed.seconds//3600}h{(elapsed.seconds%3600)//60}m | "
              f"목표: {interval_h}h | 남은: {'초과' if remaining.total_seconds()<0 else str(timedelta(seconds=int(remaining.total_seconds())))}")

        if remaining.total_seconds() <= 0:
            # 이미 이 소변 기록에 대해 알림 보냈으면 스킵
            if notified_at.get(username) == last_pee:
                continue

            over_min = int(abs(remaining.total_seconds()) / 60)
            over_h   = over_min // 60
            over_m   = over_min % 60
            pee_str  = last_pee.strftime("%H:%M")
            interval_str = f"{interval_h:.1f}시간"

            msg = (
                f"🐾 <b>{username}님 반려견 소변 알림</b>\n\n"
                f"⏰ 마지막 소변: <b>{pee_str}</b>\n"
                f"📏 설정 간격: <b>{interval_str}</b>\n"
                f"🚨 초과 시간: <b>{over_h}시간 {over_m}분</b>\n\n"
                f"💧 지금 바로 소변을 볼 수 있도록 확인해 주세요!"
            )
            send_telegram(msg)
            notified_at[username] = last_pee

def main():
    print("=" * 50)
    print("🐾 소변 알림 모니터 시작")
    print(f"   확인 주기: {CHECK_INTERVAL_SEC}초")
    print(f"   시작 시각: {now_kst():%Y-%m-%d %H:%M:%S}")
    print("=" * 50)

    while True:
        try:
            check_all_users()
        except Exception as e:
            print(f"[{now_kst():%H:%M:%S}] ❌ 오류: {e}")
        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()

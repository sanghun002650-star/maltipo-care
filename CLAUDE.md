# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A Korean-language smart pet care system for a dog named 말티포 (Maltipo). It has three independent components that share a single Firebase Realtime Database and Telegram bot.

## Running the Components

**Streamlit web dashboard (main app):**
```bash
pip install -r requirements.txt
streamlit run dog_log.py --server.enableCORS false --server.enableXsrfProtection false
```
Runs on port 8501. The devcontainer starts this automatically on attach.

**Standalone pee-alert server script (deploy separately on Railway / Render / Raspberry Pi):**
```bash
pip install requests
python pee_alert_monitor.py
```

**Desktop CV camera monitor (Windows only, requires GPU/CPU with TensorFlow):**
```bash
pip install opencv-python tensorflow Pillow requests
python cam_monitor.py
```
`cam_monitor.py` is NOT in `requirements.txt` — it needs separate installation. It also requires `pee_model.h5` (a trained Keras model) to exist in the working directory before launch, or it exits immediately.

## Architecture

### Shared Infrastructure
All three components talk to the same Firebase Realtime Database:
```
FIREBASE_URL = "https://petcare-test-c28cd-default-rtdb.asia-southeast1.firebasedatabase.app/"
```
And the same Telegram bot (token + chat ID hardcoded in each file).

### Firebase Data Schema
```
users/
  {username}/
    password: string          # plaintext — no hashing
    profile: {pet_name, birth, weight, gender, memo}
    settings: {btn_h, hdr_color, pee_interval, meal_interval,
                sleep_start, sleep_end, tg_enabled, tg_token,
                tg_chat_id, order}
    logs: {timestamp_key: activity_string}
    ledger: {timestamp_key: {date, category, amount, memo}}
```

### Timestamp Key Format
Log entries use `"%Y-%m-%d %H:%M:%S_%f"` (datetime + microseconds) as Firebase keys to guarantee uniqueness. Parsing always strips the `_microseconds` suffix with `.split('_')[0]`.

### Activity String Conventions
Activity log entries are plain Korean strings like `"💦 집에서 소변"`, `"🥣 사료 (종이컵1)"`. Filtering logic matches substrings:
- `"소변"` → pee events; exclude `"차감"`, `"리셋"`, `"끄기"`, `"알림 발송"`
- `"대변"` → poop events
- `"사료"` or `"식사"` → meal events; exclude `"차감"`, `"리셋"`, `"알림 발송"`, `"간식"`
- `"(수정)"` in the string means the real event time is embedded as `[HH:MM:SS]` inside the activity string, not the key timestamp — handled by `extract_dt()` in `dog_log.py`

### "Anchor Time" / Day Boundary
The day boundary is the wake-up time (`sleep_end`, default `"05:00"`), not midnight. `get_anchor_dt()` computes the most recent occurrence of that time before now. Events before the anchor are treated as "previous day" for timer display purposes.

### Background Alert Logic (dog_log.py)
`start_bg_monitor()` is decorated with `@st.cache_resource` so Streamlit only starts it once per server process. It runs a daemon thread that polls Firebase every 30 seconds and fires Telegram messages when pee/meal intervals are exceeded. `pee_alert_monitor.py` is a standalone equivalent of this logic for server deployments where the Streamlit process isn't always running.

### cam_monitor.py Architecture
- **Motion detection:** OpenCV `BackgroundSubtractorMOG2` computes foreground volume
- **AI classification:** TensorFlow CNN (`pee_model.h5`) classifies 224×224 ROI crops
- **Combined score:** `score = model_score + ACT_WEIGHT` if motion volume exceeds `SUSTAIN_VOLUME`
- **Event trigger:** both `score > threshold` AND `vol > motion_sens` must be true; dog must stay in zone for `stay_limit` seconds before an alert fires
- **ROI zone:** hexagonal polygon saved to `auto_data/roi_points.npy`; first launch shows zone editor (right-click to confirm)
- **Korean text rendering:** uses `PIL.ImageDraw` with `malgunbd.ttf` (Windows font) because OpenCV's `putText` doesn't support Korean glyphs

## Known Issues

`cam_monitor.py` has non-Python text appended at line 339 that will cause a `SyntaxError` at import time:
```
print("END") 예전에 짲던 코드입니다.. ...
```
This line must be removed or commented out before the file can run.

## Timezone

All datetime logic uses KST (UTC+9) exclusively. `now_kst()` is a helper defined in each file. Never use naive datetimes or assume UTC.

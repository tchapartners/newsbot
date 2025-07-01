

#KEYWORDS = ['남양유업', '상상인', '행동주의', '소액주주', '경영권 분쟁']
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import time
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = '7981123882:AAHFwkT9PpmOcvVcHojLsUL-WUgYUJE6KWU'
CHAT_IDS = [7473402256]
TARGET_URLS = [
    'https://www.mk.co.kr/',
    'https://www.hankyung.com/',
    'https://www.naver.com/'
]
KEYWORDS = ['남양유업', '상상인', '행동주의', '주주', 
            '소액주주', '주주가치']
CHECK_INTERVAL_MINUTES = 5

seen_alerts = set()
# Bot 생성 시에는 request 파라미터 없이 토큰만 넘깁니다.
bot = Bot(token=TELEGRAM_TOKEN)

def check_for_keywords():
    for url in TARGET_URLS:
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
        except Exception as e:
            logging.error(f"페이지 로드 실패 ({url}): {e}")
            continue

        text = BeautifulSoup(res.text, 'html.parser').get_text()
        for kw in KEYWORDS:
            idx = text.find(kw)
            if idx != -1:
                start = max(0, idx-30)
                end = min(len(text), idx+len(kw)+30)
                snippet = text[start:end].replace('\n',' ').strip()
                alert_id = f"{url}|{kw}|{idx}"
                if alert_id not in seen_alerts:
                    seen_alerts.add(alert_id)
                    msg = f"🔔 키워드 '{kw}' 발견!\nURL: {url}\n…{snippet}…"
                    for chat_id in CHAT_IDS:
                        try:
                            bot.send_message(chat_id=chat_id, text=msg)
                        except Exception as e:
                            logging.error(f"메시지 전송 실패 ({chat_id}): {e}")
                    logging.info(f"알림 발송 ({url}): {kw}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # 시작하자마자 한 번 실행
    check_for_keywords()
    sched = BackgroundScheduler()
    # 즉시 실행을 원하면 next_run_time을 지정합니다.
    from datetime import datetime
    sched.add_job(
        check_for_keywords,
        'interval',
        minutes=CHECK_INTERVAL_MINUTES,
        next_run_time=datetime.now()
    )
    sched.start()
    logging.info("spsi25Bot 모니터링 시작…")

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()
        logging.info("종료합니다.")
import os
import json
import re
import asyncio
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newspaper import Article
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
# Load .env
load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]

# 파일 경로
TOPIC_FILE = "topics.json"
COMPANY_FILE = "companies.json"
NEW_COMPANIES_FILE = "new_companies.json"
SUBSCRIBERS_FILE = "subscribers.json"
SENT_FILE = "sent_articles.json"

# JSON 헬퍼 함수
def load_json(path): return json.load(open(path)) if os.path.exists(path) else []
def save_json(path, data): json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)

def load_topics(): return load_json(TOPIC_FILE)
def save_topics(data): save_json(TOPIC_FILE, data)
def load_companies(): return load_json(COMPANY_FILE)
def save_companies(data): save_json(COMPANY_FILE, data)
def load_new_companies(): return load_json(NEW_COMPANIES_FILE)
def save_new_companies(data): save_json(NEW_COMPANIES_FILE, data)
def load_subscribers(): return load_json(SUBSCRIBERS_FILE)
def save_subscribers(data): save_json(SUBSCRIBERS_FILE, data)
def load_sent(): return load_json(SENT_FILE)
def save_sent(data): save_json(SENT_FILE, data)



# Google Custom Search
def google_search_all(query, api_key, cse_id, days=2):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key, "cx": cse_id, "q": query,
        "num": 10, "lr": "lang_ko", "gl": "kr", "dateRestrict": f"d{days}"
    }
    try:
        res = requests.get(url, params=params)
        print(f"[{query}] 상태: {res.status_code}")
        return res.json().get("items", []) if res.status_code == 200 else []
    except Exception as e:
        print(f"[!] Search error: {e}")
        return []

# 기사 본문 추출
def extract_clean_text(url: str) -> str:
    try:
        article = Article(url, language='ko')
        article.download()
        article.parse()
        return article.text.strip()
    except:
        try:
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            return soup.get_text(separator=' ', strip=True)[:3000]
        except Exception as e:
            print(f"[!] Fallback error: {e}")
            return ""

# 유사 기사 필터링
def is_similar_article(new_text: str, old_summaries: list, threshold=0.8) -> bool:
    new_tokens = set(re.findall(r"\w+", new_text))
    for old in old_summaries:
        old_tokens = set(re.findall(r"\w+", old))
        if not old_tokens:
            continue
        similarity = len(new_tokens & old_tokens) / len(new_tokens | old_tokens)
        if similarity >= threshold:
            return True
    return False

# ... (앞부분은 동일 생략)

# 행동주의 관련 키워드 목록
ACTIVISM_KEYWORDS = [
    "행동주의", "소액주주", "경영권 분쟁", "인수합병", "최대주주", 
    "지배구조", "자사주", "배당", "이사회", "주주총회"
]

# 뉴스 푸시
async def push_news():
    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)

    sent_articles = load_sent()
    sent_summaries = [a["summary"] for a in sent_articles]
    topics = load_topics()
    companies = load_companies()
    
    # 1. Topic 기반 검색
    for topic in topics:
        results = google_search_all(topic, GOOGLE_API_KEY, GOOGLE_CSE_ID)
        print(f"[+] 토픽 '{topic}' 검색 결과: {len(results)}개")

        for item in results:
            link = item.get("link", "")
            if any(link == a["url"] for a in sent_articles):
                continue

            content = extract_clean_text(link)
            if not content:
                continue

            summary = content[:500]
            if is_similar_article(summary, sent_summaries):
                continue

            matched_companies = [c for c in companies if c in content]
            msg = f"{matched_companies[0]}\n{item.get('title')}\n{link}" if matched_companies else f"{item.get('title')}\n{link}"

            # 발송
            subscribers = load_subscribers()
            for chat_id in subscribers:
                await bot.send_message(chat_id=chat_id, text=msg)

            print(f"[전송 완료] {link}")
            sent_articles.append({"url": link, "summary": summary})
            sent_summaries.append(summary)
            save_sent(sent_articles)
         
    # 2. 기업 기반 검색 + 본문에 activism 키워드 필터링
    for company in companies:
        results = google_search_all(company, GOOGLE_API_KEY, GOOGLE_CSE_ID)
        print(f"[+] 기업 '{company}' 검색 결과: {len(results)}개")

        for item in results:
            link = item.get("link", "")
            if any(link == a["url"] for a in sent_articles):
                continue

            content = extract_clean_text(link)
            if not content:
                continue

            # 본문 내 activism 키워드 포함 여부 확인
            if not any(keyword in content for keyword in ACTIVISM_KEYWORDS):
                continue

            summary = content[:500]
            if is_similar_article(summary, sent_summaries):
                continue

            msg = f"{company}\n{item.get('title')}\n{link}"
            subscribers = load_subscribers()
            for chat_id in subscribers:
                await bot.send_message(chat_id=chat_id, text=msg)

            print(f"[전송 완료] {link}")
            sent_articles.append({"url": link, "summary": summary})
            sent_summaries.append(summary)
            save_sent(sent_articles)
            
# 단독 실행 시 뉴스 크롤링 수행
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run-bot":
        from telegram.ext import ApplicationBuilder
        # 앞서 정의한 ApplicationBuilder 코드 실행됨 ← 이게 없음 (아무것도 안함)
    else:
        asyncio.run(push_news())
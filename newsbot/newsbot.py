import os
import json
import re
import asyncio
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newspaper import Article
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]

# File paths
TOPIC_FILE = "topics.json"
COMPANY_FILE = "companies.json"
SUBSCRIBERS_FILE = "subscribers.json"
SENT_FILE = "sent_articles.json"

# JSON helpers
def load_json(path): return json.load(open(path)) if os.path.exists(path) else []
def save_json(path, data): json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)

def load_topics(): return load_json(TOPIC_FILE)
def load_companies(): return load_json(COMPANY_FILE)
def load_subscribers(): return load_json(SUBSCRIBERS_FILE)
def save_subscribers(data): save_json(SUBSCRIBERS_FILE, data)
def load_sent(): return load_json(SENT_FILE)
def save_sent(data): save_json(SENT_FILE, data)

# Google Custom Search
def google_search_all(query, api_key, cse_id, days=5):
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

# Clean article
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

# Similarity check
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

# 행동주의 키워드
ACTIVISM_KEYWORDS = [
    "행동주의", "소액주주", "경영권", "인수합병", "최대주주", 
    "지배구조", "자사주", "배당", "이사회", "주주총회", "지분", 
     "주총", "소송", "감사", "이사", "선임", "경영", "배당", "의결권"
]

# 뉴스 푸시
async def push_news():
    bot = Bot(token=BOT_TOKEN)
    sent_articles = load_sent()
    sent_summaries = [a["summary"] for a in sent_articles]
    topics = load_topics()
    companies = load_companies()
    subscribers = load_subscribers()

    # Topic 검색
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
            for chat_id in subscribers:
                await bot.send_message(chat_id=chat_id, text=msg)
            print(f"[전송 완료] {link}")
            sent_articles.append({"url": link, "summary": summary})
            sent_summaries.append(summary)
            save_sent(sent_articles)

    # 기업 검색
    for company in companies:
        results = google_search_all(company, GOOGLE_API_KEY, GOOGLE_CSE_ID)
        print(f"[+] 기업 '{company}' 검색 결과: {len(results)}개")
        for item in results:
            link = item.get("link", "")
            if any(link == a["url"] for a in sent_articles):
                continue
            content = extract_clean_text(link)
            if not content or not any(k in content for k in ACTIVISM_KEYWORDS):
                continue
            summary = content[:500]
            if is_similar_article(summary, sent_summaries):
                continue
            msg = f"{company}\n{item.get('title')}\n{link}"
            for chat_id in subscribers:
                await bot.send_message(chat_id=chat_id, text=msg)
            print(f"[전송 완료] {link}")
            sent_articles.append({"url": link, "summary": summary})
            sent_summaries.append(summary)
            save_sent(sent_articles)

# /start 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        await context.bot.send_message(chat_id=chat_id, text="\ud83d\udc4b \ub274\uc2a4 \uad6c\ub3c5 \uc644\ub8cc!")
    else:
        await context.bot.send_message(chat_id=chat_id, text="\u2705 \uc774\ubbf8 \uad6c\ub3c5 \uc911\uc785\ub2c8\ub2e4.")

# 실행부
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "start-bot":
        # 수동으로 /start 테스트용
        async def fake_start():
            app = ApplicationBuilder().token(BOT_TOKEN).build()
            app.add_handler(CommandHandler("start", start))
            await app.initialize()
            await app.start()
            await asyncio.sleep(15)
            await app.stop()
        asyncio.run(fake_start())
    else:
        asyncio.run(push_news())

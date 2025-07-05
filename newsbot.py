import os
import json
import requests
import asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup
from newspaper import Article
# load secrets

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]
SUBSCRIBERS_FILE = "subscribers.json"
SENT_FILE = "sent_articles.json"

# search keywords 
companies = ['한국콜마', '한진칼', '현대해상', '동양고속', "삼영전자", "남양유업", "맵스리얼티", "상상인",
             "파크시스템스", "금호석유화학", "와이엠", "씨에스윈드", "사조오양", "마음AI", "리파인", "가비아"]

topics = ["행동주의", "소액주주", "경영권 분쟁", '밸류업', '지배구조', '주주총회','액티비스트', '최대주주', 
          '기업가치 제고','주주가치 제고', "기업분할", "물적분할", "인적분할","자사주", "배당", "배당확대",
          "배당정책", "지분확대", "지분매입", "경영참여", "사외이사","이사회", "경영투명성","기업지배구조", 
          "의결권", "경영효율화", "사업재편", "지속가능경영","이익환원", "리스크관리", "경영쇄신", 
          "감사위원 분리선출", "집중투표제", "누적투표제", "전자투표", "이사후보추천위원회","주주제안", "스튜어드십 코드", 
          "지분율 변화", "최대주주 변경", "오너리스크", "오너일가", "특수관계인", "상속세", "우호지분", 
          "의결권 대리행사", "이익잉여금", "배당성향", "현금배당", "현금흐름 활용", "주주환원", "백기사", 
          "적대적 인수합병", "경영권 방어", "차등의결권", "공개매수", "지분매수청구"]


def load_subscribers() -> list[int]:
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)

def save_subscribers(chat_ids: list[int]) -> None:
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(chat_ids, f)

async def auto_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        await context.bot.send_message(chat_id=chat_id, text="👋 Welcome! You've been subscribed to news updates.")

def google_search_all(query: str, api_key: str, cse_id: str, days: int = 2) -> list[dict]:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": 10,
        "lr": "lang_ko",
        "gl": "kr"
    }
    if days:
        params["dateRestrict"] = f"d{days}"
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        print(f"[!] Error in google_search_all: {e}")
        return []

def contains_topic(url: str, topics: list[str]) -> bool:
    try:
        res = requests.get(url, timeout=5)
        text = res.text
        found = any(topic in text for topic in topics)
        #print(f"[+] Topic match: {found} for URL: {url}")
        return found
    except Exception as e:
        #print(f"[!] Error fetching {url}: {e}")
        return False
  
# store sent articles   
def load_sent_articles():
    if not os.path.exists(SENT_FILE):
        return []
    with open(SENT_FILE, "r") as f:
        return json.load(f)

def save_sent_articles(data):
    with open(SENT_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_clean_text(url: str) -> str:
    try:
        article = Article(url, language='ko')
        article.download()
        article.parse()
        return article.text.strip()
    except Exception as e:
        print(f"[!] newspaper3k failed for {url}: {e}")
        try:
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(separator=' ', strip=True)
            return text[:3000]  # 너무 길면 자름
        except Exception as e2:
            print(f"[!] BeautifulSoup fallback failed for {url}: {e2}")
            return ""
        
# check for duplicate   
def is_similar_article(new_text: str, existing_summaries: list[str], threshold: float = 0.6) -> bool:
    def tokenize(text):
        return set(re.findall(r'\w+', text))

    new_tokens = tokenize(new_text)
    for old in existing_summaries:
        old_tokens = tokenize(old)
        if not old_tokens:
            continue
        similarity = len(new_tokens & old_tokens) / len(new_tokens | old_tokens)
        if similarity >= threshold:
            return True
    return False

async def push_news():
    bot = Bot(token=BOT_TOKEN)
    subscribers = load_subscribers()
    sent_articles = load_sent_articles()
    sent_summaries = [a["summary"] for a in sent_articles]

    for chat_id in subscribers:
        for company in companies:
            try:
                results = google_search_all(company, GOOGLE_API_KEY, GOOGLE_CSE_ID)
                print(f"[+] {company}: {len(results)} results")
                for item in results:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")

                    if any(link == a["url"] for a in sent_articles):
                        print(f"⛔️ Already sent: {link}")
                        continue

                    content = extract_clean_text(link)
                    if not content:
                        continue

                    summary = content[:1000]
                    if is_similar_article(summary, sent_summaries):
                        print(f"🔁 Similar to previous, skipping: {link}")
                        continue

                    topic_hits = [t for t in topics if t in content]
                    company_in_content = company in content

                    if (company_in_content and topic_hits) or len(topic_hits) >= 2:
                        msg = f"🔍 {company} + {len(topic_hits)}개 토픽\n{title}\n{link}"
                        await bot.send_message(chat_id=chat_id, text=msg)
                        print(f"✅ Sent to {chat_id}: {link}")

                        sent_articles.append({
                            "url": link,
                            "summary": summary,
                        })
                        sent_summaries.append(summary)
                        save_sent_articles(sent_articles)
                    else:
                        print(f"🔇 조건 미충족: {link}")

            except Exception as e:
                print(f"[!] Error processing {company} for {chat_id}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run-bot":
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_subscribe))
        print("🤖 Bot is polling...")
        app.run_polling()
    else:
        asyncio.run(push_news())


'''
# load secrets
load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]
SUBSCRIBERS_FILE = "subscribers.json"

# search keywords 
companies = ['한국콜마', '한진칼', '현대해상', '동양고속', "삼영전자", "남양유업", "맵스리얼티", "상상인",
             "파크시스템스", "금호석유화학", "와이엠", "씨에스윈드", "사조오양", "마음AI", "리파인", "가비아"]

topics = ["행동주의", "소액주주", "경영권 분쟁", '밸류업', '지배구조', '주주총회','액티비스트', '최대주주', 
          '기업가치 제고','주주가치 제고', "기업분할", "물적분할", "인적분할","자사주", "배당", "배당확대",
          "배당정책", "지분확대", "지분매입", "경영참여", "사외이사","이사회", "경영투명성","기업지배구조", 
          "의결권", "경영효율화", "사업재편", "지속가능경영","이익환원", "리스크관리", "경영쇄신" ]


def load_subscribers() -> list[int]:
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)

def save_subscribers(chat_ids: list[int]) -> None:
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(chat_ids, f)

async def auto_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        await context.bot.send_message(chat_id=chat_id, text="👋 Welcome! You've been subscribed to news updates.")

def google_search_all(query: str, api_key: str, cse_id: str, days: int = 2) -> list[dict]:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": 10,
        "lr": "lang_ko",
        "gl": "kr"
    }
    if days:
        params["dateRestrict"] = f"d{days}"
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        print(f"[!] Error in google_search_all: {e}")
        return []

def contains_topic(url: str, topics: list[str]) -> bool:
    try:
        res = requests.get(url, timeout=5)
        text = res.text
        found = any(topic in text for topic in topics)
        #print(f"[+] Topic match: {found} for URL: {url}")
        return found
    except Exception as e:
        #print(f"[!] Error fetching {url}: {e}")
        return False

# [company] + [topic] OR [keyword]*2 
async def push_news():
    bot = Bot(token=BOT_TOKEN)
    subscribers = load_subscribers()
    print(f"[+] Subscribers: {subscribers}")

    for chat_id in subscribers:
        for company in companies:
            try:
                results = google_search_all(company, GOOGLE_API_KEY, GOOGLE_CSE_ID)
                print(f"[+] Results for {company}: {len(results)}")

                for item in results:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")
                    preview_text = f"{title} {snippet}"

                    try:
                        res = requests.get(link, timeout=5)
                        content = res.text

                        topic_hits = [t for t in topics if t in content]
                        company_in_content = company in content

                        if (company_in_content and topic_hits) or len(topic_hits) >= 2:
                            msg = f"🔍 {company} + {len(topic_hits)}개 토픽\n{title}\n{link}"
                            print(f"✅ Sending to {chat_id}: {msg}")
                            await bot.send_message(chat_id=chat_id, text=msg)
                        else:
                            print(f"🔇 Skipped (조건 미충족): {link}")
                    except Exception as e:
                        print(f"[!] 본문 파싱 오류: {e}")
            except Exception as e:
                print(f"[!] Error processing {company} for chat_id {chat_id}: {e}")


                        
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run-bot":
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_subscribe))
        print("🤖 Bot is polling...")
        app.run_polling()
    else:
        asyncio.run(push_news())
        
'''
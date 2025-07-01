import os
import requests
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]

def get_latest_chat_id(token: str) -> int:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    res = requests.get(url).json()

    if "result" in res and res["result"]:
        return res["result"][-1]["message"]["chat"]["id"]
    else:
        raise ValueError("No chat messages found. Send /start to your bot to register a chat ID.")

def google_search(query: str, api_key: str, cse_id: str) -> str:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": 1
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data:
        result = data["items"][0]
        return f"{result['title']}\n{result['link']}"
    else:
        return "No results found."

def push_news():
    bot = Bot(token=BOT_TOKEN)
    chat_id = get_latest_chat_id(BOT_TOKEN)
    queries = ["행동주의", "소액주주", "경영권 분쟁"]

    for query in queries:
        result = google_search(query, GOOGLE_API_KEY, GOOGLE_CSE_ID)
        bot.send_message(chat_id=chat_id, text=f"🔍 {query}\n{result}")

if __name__ == "__main__":
    push_news()

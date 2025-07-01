import os
import json
import requests
import asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]
SUBSCRIBERS_FILE = "subscribers.json"

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

def google_search(query: str, api_key: str, cse_id: str) -> str:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cse_id, "q": query, "num": 1}
    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data:
        result = data["items"][0]
        return f"{result['title']}\n{result['link']}"
    return "No results found."
'''
async def push_news():
    
    bot = Bot(token=BOT_TOKEN)
    subscribers = load_subscribers()
    queries = ["행동주의", "소액주주", "경영권 분쟁", '트럼프', '미국', '주가']

    for chat_id in subscribers:
        for query in queries:
            try:
                result = google_search(query, GOOGLE_API_KEY, GOOGLE_CSE_ID)
                print(f"Sending to {chat_id}: {query}")
                await bot.send_message(chat_id=chat_id, text=f"🔍 {query}\n{result}")
            except Exception as e:
                print(f"Failed to send to {chat_id}: {e}")
'''
# dummy send / main 
async def push_news():
    
    print("Checking subscribers.json:") 
    with open("subscribers.json") as f: 
        print(f.read())
    
    bot = Bot(token=BOT_TOKEN)
    subscribers = load_subscribers()
    print(f"✅ push_news started")
    print(f"Loaded subscribers: {subscribers}")

    for chat_id in subscribers:
        try:
            print(f"Sending to {chat_id}: Hello world")
            await bot.send_message(chat_id=chat_id, text="🌍 Hello, this is a test message from your bot!")
        except Exception as e:
            print(f"❌ Failed to send to {chat_id}: {e}")

if __name__ == "__main__":
    import sys
    print("🟡 Running newsbot.py...")
    if len(sys.argv) > 1 and sys.argv[1] == "run-bot":
        print("🟢 Running in polling mode")
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_subscribe))
        app.run_polling()
    else:
        print("🔵 Running push_news() via asyncio")
        asyncio.run(push_news())
        
'''
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run-bot":
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_subscribe))
        print("Bot is polling...")
        app.run_polling()
    else:
        asyncio.run(push_news())
'''
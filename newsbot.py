import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Load secrets from environment
BOT_TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]

# Function to perform Google search
def google_search(query: str, api_key: str, cse_id: str) -> str:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": 1  # top result
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data:
        result = data["items"][0]
        return f"{result['title']}\n{result['link']}"
    else:
        return "No results found."

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me a keyword and I’ll search Google for you.")

# Main search handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text("Searching...")
    result = google_search(query, GOOGLE_API_KEY, GOOGLE_CSE_ID)
    await update.message.reply_text(result)

# Main app runner
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()

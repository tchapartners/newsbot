#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  1 10:15:20 2025

@author: yujin
"""

# bot.py
import json
import os
import time
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

BOT_TOKEN = os.getenv("7981123882:AAHFwkT9PpmOcvVcHojLsUL-WUgYUJE6KWU")
SUBSCRIBERS_FILE = "subscribers.json"
KEYWORDS = ["AI", "technology", "science"]

# Load subscribers list
def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)

# Save subscribers list
def save_subscribers(subs):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subs, f)

# Add user to subscribers
def add_subscriber(user_id):
    subs = load_subscribers()
    if user_id not in subs:
        subs.append(user_id)
        save_subscribers(subs)

# Handle /start command
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    add_subscriber(user_id)
    update.message.reply_text("You're now subscribed to news alerts!")

# Dummy web searcher (placeholder)
def search_news():
    # Replace this with real API or scraping logic
    return [
        "https://example.com/news1",
        "https://example.com/news2"
    ]

# Send news to all subscribers
def send_news():
    bot = Bot(BOT_TOKEN)
    news_links = search_news()
    subs = load_subscribers()
    for uid in subs:
        for link in news_links:
            bot.send_message(chat_id=uid, text=link)

if __name__ == '__main__':
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()
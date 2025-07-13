#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 환경 변수 로드 (.env에서 BOT_TOKEN 불러오기)
load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]

# 파일 경로
TOPIC_FILE = "topics.json"
COMPANY_FILE = "companies.json"
SUBSCRIBERS_FILE = "subscribers.json"

# JSON 헬퍼 함수 (예외 처리 포함)
def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] 저장 실패: {path}, 에러: {e}")

# 파일 로딩 함수
def load_topics(): return load_json(TOPIC_FILE)
def save_topics(data): save_json(TOPIC_FILE, data)
def load_companies(): return load_json(COMPANY_FILE)
def save_companies(data): save_json(COMPANY_FILE, data)
def load_subscribers(): return load_json(SUBSCRIBERS_FILE)
def save_subscribers(data): save_json(SUBSCRIBERS_FILE, data)

# /start: 구독 처리
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        await context.bot.send_message(chat_id=chat_id, text="👋 뉴스 구독 완료!")
    else:
        await context.bot.send_message(chat_id=chat_id, text="✅ 이미 구독 중입니다.")

# /add_topic
async def add_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /add_topic [토픽명]")
        return
    topic = " ".join(context.args).strip().replace(" ", "")
    topics = load_topics()
    if topic in topics:
        await update.message.reply_text(f"✅ 이미 있는 토픽: {topic}")
    else:
        topics.append(topic)
        save_topics(topics)
        await update.message.reply_text(f"🎉 토픽 추가됨: {topic}")

# /remove_topic
async def remove_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /remove_topic [토픽명]")
        return
    topic = " ".join(context.args).strip().replace(" ", "")
    topics = load_topics()
    if topic in topics:
        topics.remove(topic)
        save_topics(topics)
        await update.message.reply_text(f"🗑️ 토픽 삭제됨: {topic}")
    else:
        await update.message.reply_text(f"❌ 존재하지 않음: {topic}")

# /list_topics
async def list_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topics = load_topics()
    msg = "📌 등록된 토픽:\n" + "\n".join(f"- {t}" for t in topics) if topics else "❗ 등록된 토픽 없음"
    await update.message.reply_text(msg)

# /add_company
async def add_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /add_company [회사명]")
        return
    name = " ".join(context.args).strip().replace(" ", "")
    companies = load_companies()
    if name in companies:
        await update.message.reply_text(f"✅ 이미 있는 회사명: {name}")
    else:
        companies.append(name)
        save_companies(companies)
        await update.message.reply_text(f"🏢 회사명 추가됨: {name}")

# /remove_company
async def remove_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /remove_company [회사명]")
        return
    name = " ".join(context.args).strip().replace(" ", "")
    companies = load_companies()
    if name in companies:
        companies.remove(name)
        save_companies(companies)
        await update.message.reply_text(f"🗑️ 회사명 삭제됨: {name}")
    else:
        await update.message.reply_text(f"❌ 존재하지 않음: {name}")

# /list_companies
async def list_companies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    companies = load_companies()
    msg = "🏢 등록된 기업:\n" + "\n".join(f"- {c}" for c in companies) if companies else "❗ 등록된 기업 없음"
    await update.message.reply_text(msg)

# 일반 메시지로도 구독 처리
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# 실행부
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 명령어 핸들러 등록
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_topic", add_topic))
    app.add_handler(CommandHandler("remove_topic", remove_topic))
    app.add_handler(CommandHandler("list_topics", list_topics))
    app.add_handler(CommandHandler("add_company", add_company))
    app.add_handler(CommandHandler("remove_company", remove_company))
    app.add_handler(CommandHandler("list_companies", list_companies))

    # 일반 메시지도 구독 처리
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    print("🤖 관리용 봇 실행 중...")
    app.run_polling()
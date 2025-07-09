import os
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)

# Environment Variable থেকে Bot Token নেওয়া
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://tg-chaker.onrender.com"  # তোমার Render URL

app = Flask(__name__)

# স্টেট সংজ্ঞা
BOARD, YEAR, ROLL, REG = range(4)

# বোর্ড তালিকা
boards = {
    "ঢাকা": "dhaka", "চট্টগ্রাম": "chittagong", "রাজশাহী": "rajshahi",
    "কুমিল্লা": "comilla", "বরিশাল": "barisal", "সিলেট": "sylhet",
    "দিনাজপুর": "dinajpur", "যশোর": "jessore", "মাদ্রাসা": "madrasah",
    "টেকনিক্যাল": "technical"
}

@app.route('/')
def home():
    return "✅ রেজাল্ট বট চলছে!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return 'ok'

# শুরু কমান্ড
async def শুরু(update: Update, context: ContextTypes.DEFAULT_TYPE):
    বোর্ড_তালিকা = list(boards.items())
    বোর্ড_বাটন = []

    for i in range(0, len(বোর্ড_তালিকা), 2):
        সারি = []
        for নাম, কী in বোর্ড_তালিকা[i:i+2]:
            সারি.append(InlineKeyboardButton(নাম, callback_data=কী))
        বোর্ড_বাটন.append(সারি)

    await update.message.reply_text(
        "📚 পরীক্ষার বোর্ড নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(বোর্ড_বাটন)
    )
    return BOARD

# বোর্ড নির্বাচন
async def বোর্ড_নির্বাচন(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['board'] = query.data
    await query.message.reply_text("📅 পরীক্ষার সাল লিখুন (যেমনঃ ২০২৫):")
    return YEAR

# সাল ইনপুট
async def সাল_নিবে(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['year'] = update.message.text.strip()
    await update.message.reply_text("🔢 রোল নম্বর লিখুন:")
    return ROLL

# রোল ইনপুট
async def রোল_নিবে(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['roll'] = update.message.text.strip()
    await update.message.reply_text("🆔 রেজিস্ট্রেশন নম্বর লিখুন:")
    return REG

# রেজি ইনপুট এবং রেজাল্ট আনা
async def রেজি_নিবে(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] = update.message.text.strip()
    await update.message.reply_text("⏳ রেজাল্ট আনা হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")

    data = context.user_data
    ফলাফল = রেজাল্ট_আনো(data['board'], data['year'], data['roll'], data['reg'])

    await update.message.reply_text(ফলাফল)
    return ConversationHandler.END

# রেজাল্ট স্ক্র্যাপ ফাংশন
def রেজাল্ট_আনো(বোর্ড, সাল, রোল, রেজি):
    try:
        তথ্য = {
            "exam": "ssc",
            "year": সাল,
            "board": বোর্ড,
            "roll": রোল,
            "reg": রেজি,
            "button2": "Submit"
        }
        রেস = requests.post("https://educationboardresults.gov.bd/index.php", data=তথ্য)
        if "GPA" in রেস.text:
            return "✅ রেজাল্ট পাওয়া গেছে!\n(এই অংশে চাইলে HTML থেকে GPA, নাম, সাবজেক্ট আলাদা করে বের করা যাবে।)"
        else:
            return "❌ রেজাল্ট খুঁজে পাওয়া যায়নি। তথ্য সঠিকভাবে দিন।"
    except Exception as e:
        return f"⚠️ সমস্যা হয়েছে: {e}"

# বাতিল
async def বাতিল(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ বাতিল করা হয়েছে।")
    return ConversationHandler.END

# অ্যাপ তৈরি ও হ্যান্ডলার যোগ
application = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", শুরু)],
    states={
        BOARD: [CallbackQueryHandler(বোর্ড_নির্বাচন)],
        YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, সাল_নিবে)],
        ROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, রোল_নিবে)],
        REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, রেজি_নিবে)],
    },
    fallbacks=[CommandHandler("cancel", বাতিল)],
)

application.add_handler(conv_handler)

# Webhook চালু
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",  # সব IP থেকে কানেকশন গ্রহণ করার জন্য
        port=8000,         # ৮০০০ পোর্টে ওয়েব সার্ভার চালানো
        webhook_url=WEBHOOK_URL  # তোমার Render webhook URL
    )

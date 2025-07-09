import os
import logging
import requests
from functools import lru_cache
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)

# লগিং কনফিগারেশন
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# এনভায়রনমেন্ট ভ্যারিয়েবল
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Render.com থেকে অটোমেটিকভাবে সেট হবে

app = Flask(__name__)

# কনভারসেশন স্টেটস
BOARD, YEAR, ROLL, REG = range(4)

# বোর্ড তালিকা
boards = {
    "ঢাকা": "dhaka", "চট্টগ্রাম": "chittagong", "রাজশাহী": "rajshahi",
    "কুমিল্লা": "comilla", "বরিশাল": "barisal", "সিলেট": "sylhet",
    "দিনাজপুর": "dinajpur", "যশোর": "jessore", "মাদ্রাসা": "madrasah",
    "টেকনিক্যাল": "technical"
}

# রেজাল্ট ফেচিং ফাংশন (ক্যাশিং সহ)
@lru_cache(maxsize=100)
def fetch_result(board, year, roll, reg):
    try:
        logger.info(f"Fetching result for: {board}, {year}, {roll}, {reg}")
        
        payload = {
            "exam": "ssc",
            "year": year,
            "board": board,
            "roll": roll,
            "reg": reg,
            "button2": "Submit"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.post(
            "https://educationboardresults.gov.bd/index.php",
            data=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            result_table = soup.find('table', {'class': 'black'})
            
            if result_table:
                result_data = {}
                rows = result_table.find_all('tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) == 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1].get_text(strip=True)
                        result_data[key] = value
                
                if 'GPA' in result_data:
                    formatted_result = (
                        "📌 **রেজাল্ট ডিটেইলস**\n"
                        f"➖➖➖➖➖➖➖➖➖\n"
                        f"👤 নাম: {result_data.get('Name', 'N/A')}\n"
                        f"🔢 রোল: {roll}\n"
                        f"🏫 বোর্ড: {board.capitalize()}\n"
                        f"📅 সাল: {year}\n"
                        f"⭐ GPA: {result_data['GPA']}\n"
                        f"📊 গ্রেড: {result_data.get('Grade', 'N/A')}\n"
                        f"➖➖➖➖➖➖➖➖➖\n"
                        f"📝 /start দিয়ে আবার চেক করুন"
                    )
                    return formatted_result
                
            return "❌ রেজাল্ট পাওয়া যায়নি। দয়া করে:\n1. তথ্য পুনরায় চেক করুন\n2. পরীক্ষার ফলাফল প্রকাশিত হয়েছে কিনা নিশ্চিত হন\n3. পরে আবার চেষ্টা করুন"
        
        return "⚠️ সার্ভারে সমস্যা হচ্ছে। কিছুক্ষণ পর আবার চেষ্টা করুন।"
    
    except requests.Timeout:
        return "⏳ সার্ভার রেসপন্স দিতে বেশি সময় নিচ্ছে। পরে আবার চেষ্টা করুন।"
    except Exception as e:
        logger.error(f"Error fetching result: {str(e)}")
        return f"⚠️ ত্রুটি হয়েছে: {str(e)}"

# কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    
    keyboard = []
    board_items = list(boards.items())
    
    # 2 কলামে বোর্ড বাটন সাজানো
    for i in range(0, len(board_items), 2):
        row = []
        for name, key in board_items[i:i+2]:
            row.append(InlineKeyboardButton(name, callback_data=key))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ বাতিল", callback_data="cancel")])
    
    await update.message.reply_text(
        "📚 **এসএসসি/এইচএসসি রেজাল্ট চেকার**\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "প্রথমে আপনার বোর্ড নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BOARD

async def select_board(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        return await cancel(update, context)
    
    context.user_data['board'] = query.data
    await query.edit_message_text(
        text="📅 **পরীক্ষার সাল লিখুন**\n"
             "উদাহরণ: 2023\n"
             "(শুধুমাত্র সংখ্যায় লিখুন, ২০০০-২০২৫ এর মধ্যে)",
        reply_markup=None
    )
    return YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    year = update.message.text.strip()
    
    if not year.isdigit() or len(year) != 4 or int(year) < 2000 or int(year) > 2025:
        await update.message.reply_text(
            "⚠️ **অবৈধ সাল!**\n"
            "দয়া করে ২০০০ থেকে ২০২৫ এর মধ্যে একটি সাল লিখুন।\n"
            "উদাহরণ: 2023"
        )
        return YEAR
    
    context.user_data['year'] = year
    await update.message.reply_text(
        "🔢 **রোল নম্বর লিখুন**\n"
        "উদাহরণ: 123456\n"
        "(শুধুমাত্র ৬ ডিজিটের সংখ্যা)"
    )
    return ROLL

async def get_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll = update.message.text.strip()
    
    if not roll.isdigit() or len(roll) != 6:
        await update.message.reply_text(
            "⚠️ **অবৈধ রোল নম্বর!**\n"
            "দয়া করে ৬ ডিজিটের রোল নম্বর লিখুন।\n"
            "উদাহরণ: 123456"
        )
        return ROLL
    
    context.user_data['roll'] = roll
    await update.message.reply_text(
        "🆔 **রেজিস্ট্রেশন নম্বর লিখুন**\n"
        "উদাহরণ: 1234567890\n"
        "(শুধুমাত্র সংখ্যা)"
    )
    return REG

async def get_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reg = update.message.text.strip()
    
    if not reg.isdigit():
        await update.message.reply_text(
            "⚠️ **অবৈধ রেজিস্ট্রেশন নম্বর!**\n"
            "দয়া করে শুধুমাত্র সংখ্যায় লিখুন।\n"
            "উদাহরণ: 1234567890"
        )
        return REG
    
    context.user_data['reg'] = reg
    
    data = context.user_data
    await update.message.reply_text(
        "⏳ রেজাল্ট চেক করা হচ্ছে...\n"
        "একটু অপেক্ষা করুন...",
        parse_mode='Markdown'
    )
    
    result = fetch_result(data['board'], data['year'], data['roll'], data['reg'])
    await update.message.reply_text(result, parse_mode='Markdown')
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if hasattr(update, 'callback_query') else None
    
    if query:
        await query.answer()
        await query.edit_message_text("❌ বাতিল করা হয়েছে। /start দিয়ে আবার শুরু করুন।")
    else:
        await update.message.reply_text("❌ বাতিল করা হয়েছে। /start দিয়ে আবার শুরু করুন。")
    
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 **হেল্প মেনু**\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "🔹 /start - রেজাল্ট চেক শুরু করুন\n"
        "🔹 /help - এই মেসেজ দেখাবে\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "⚠️ সমস্যা হলে:\n"
        "1. তথ্য পুনরায় চেক করুন\n"
        "2. ইন্টারনেট কানেকশন নিশ্চিত করুন\n"
        "3. ফলাফল প্রকাশিত হয়েছে কিনা নিশ্চিত হন"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Flask রাউট
@app.route('/')
def home():
    return "✅ রেজাল্ট বট সচল রয়েছে!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return 'ok'

# অ্যাপ্লিকেশন সেটআপ
def setup_application():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BOARD: [CallbackQueryHandler(select_board)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_year)],
            ROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_roll)],
            REG: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reg)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('help', help_command)],
        per_message=False  # PTB warning সমাধানের জন্য
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    return application

# মেইন ফাংশন
if __name__ == '__main__':
    application = setup_application()
    
    if WEBHOOK_URL:
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8000)),  # Render.com থেকে PORT নেবে
            webhook_url=WEBHOOK_URL,
            secret_token=os.getenv("WEBHOOK_SECRET", "")
        )
    else:
        application.run_polling()

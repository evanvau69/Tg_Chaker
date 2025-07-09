import logging
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, Dispatcher
from telegram.ext import BasePersistence, PicklePersistence
from telegram.ext import ConversationHandler

# টেলিগ্রাম বটের Token
TOKEN = '8014475811:AAHnXLAke9XRfNq_LCdhqdcxazMk6nZM8kE'

# Flask app তৈরি
app = Flask(__name__)

# বোর্ডের নামের বাটন
BOARD_LIST = [
    "SSC/Dakhil/Equivalent", "JSC/JDC", "SSC/Dakhil", "SSC(Vocational)", "HSC/Alim", 
    "HSC(Vocational)", "HSC(BM)", "Diploma in Commerce", "Diploma in Business Studies"
]

# কনভার্সেশন স্টেট
WAITING_YEAR, WAITING_ROLL, WAITING_REG, WAITING_CAPTCHA, WAITING_CAPTCHA_RESPONSE = range(5)

# রেজাল্ট ফেচ করার ফাংশন
def fetch_result(year, board, roll, reg):
    url = "https://example.com/api/result"  # আপনার সঠিক URL ব্যবহার করুন
    params = {
        'year': year,
        'board': board,
        'roll': roll,
        'reg_no': reg
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # যদি API কল ঠিক না থাকে, তাহলে error দেখাবে
        result_data = response.json()
        return result_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching result: {e}")
        return None

# রেজাল্ট দেখানোর ফাংশন
def show_result(update, context):
    # ইউজারের ইনপুট থেকে ডেটা সংগ্রহ করা
    year = context.user_data.get('year')
    board = context.user_data.get('board')
    roll = context.user_data.get('roll')
    reg = context.user_data.get('reg')
    
    # রেজাল্ট ফেচ করা
    result_data = fetch_result(year, board, roll, reg)
    
    if result_data:
        # রেজাল্ট যদি সঠিকভাবে পাওয়া যায়
        result_message = f"রেজাল্ট: \n\n"
        result_message += f"বোর্ড: {board}\n"
        result_message += f"বছর: {year}\n"
        result_message += f"রোল: {roll}\n"
        result_message += f"রেজিস্ট্রেশন নম্বর: {reg}\n"
        result_message += f"গ্রেড: {result_data['grade']}\n"
        result_message += f"পাস/ফেল: {result_data['status']}\n"
    else:
        # যদি API থেকে রেজাল্ট পাওয়া না যায়
        result_message = "দুঃখিত, রেজাল্ট পাওয়া যায়নি। দয়া করে আবার চেষ্টা করুন।"
    
    update.message.reply_text(result_message)

# স্টার্ট কমান্ড হ্যান্ডলার
def start(update, context):
    user_name = update.message.from_user.first_name
    welcome_message = f"{user_name} স্বাগতম 🌸 রেজাল্ট দেখার জন্য নিচের তথ্য গুলান দিন"
    
    keyboard = [[InlineKeyboardButton(option, callback_data=option)] for option in BOARD_LIST]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    return WAITING_YEAR

# বোর্ড সিলেক্ট করার পর
def button(update, context):
    query = update.callback_query
    board = query.data
    context.user_data['board'] = board
    query.answer()

    # বোর্ড সিলেক্ট হওয়ার পর, বছর চাওয়া হবে
    query.edit_message_text(text=f"{board} সিলেক্ট হয়েছে। এখন রেজাল্টের জন্য বছর দিন।")
    
    return WAITING_YEAR

# বছর নেওয়ার জন্য
def get_year(update, context):
    year = update.message.text
    context.user_data['year'] = year
    update.message.reply_text("বোর্ড সিলেক্ট হয়েছে। এবার রোল নম্বর দিন।")
    
    return WAITING_ROLL

# রোল নম্বর নেওয়ার জন্য
def get_roll(update, context):
    roll = update.message.text
    context.user_data['roll'] = roll
    update.message.reply_text("রেজিস্ট্রেশন নম্বর দিন।")

    return WAITING_REG

# রেজিস্ট্রেশন নম্বর নেওয়ার জন্য
def get_reg(update, context):
    reg = update.message.text
    context.user_data['reg'] = reg
    update.message.reply_text("যদি CAPTCHA দেখায়, বট এর মাধ্যমে পাঠানো হবে।")

    return WAITING_CAPTCHA

# CAPTCHA দেখানোর জন্য
def captcha(update, context):
    update.message.reply_text("Captcha কোড সঠিকভাবে দিন")
    
    return WAITING_CAPTCHA_RESPONSE

# CAPTCHA এর উত্তর পাওয়া
def captcha_response(update, context):
    captcha_answer = update.message.text
    # CAPTCHA সঠিক হলে রেজাল্ট দেখানো হবে
    show_result(update, context)

    return ConversationHandler.END

# টেলিগ্রাম বটের Webhook ফাংশন
@app.route('/webhook', methods=['POST'])
def webhook():
    # টেলিগ্রাম আপডেট নিন
    json_str = request.get_data().decode('UTF-8')
    update = Update.de_json(json_str, updater.bot)
    dispatcher.process_update(update)
    return 'OK'

# বটের মূল ফাংশন
def main():
    global updater, dispatcher

    # Dispatcher & Updater তৈরি করুন
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # কনভার্সেশন হ্যান্ডলার
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_YEAR: [MessageHandler(Filters.text & ~Filters.command, get_year)],
            WAITING_ROLL: [MessageHandler(Filters.text & ~Filters.command, get_roll)],
            WAITING_REG: [MessageHandler(Filters.text & ~Filters.command, get_reg)],
            WAITING_CAPTCHA: [MessageHandler(Filters.text & ~Filters.command, captcha)],
            WAITING_CAPTCHA_RESPONSE: [MessageHandler(Filters.text & ~Filters.command, captcha_response)],
        },
        fallbacks=[],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Webhook সেটআপ
    updater.bot.set_webhook(url="https://your-render-app-name.onrender.com/webhook")

    # Start Flask app
    app.run(host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main()

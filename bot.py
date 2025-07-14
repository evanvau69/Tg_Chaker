import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
import logging

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# এনভায়রনমেন্ট ভেরিয়েবল
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-1001234567890")  # আপনার অ্যাডমিন গ্রুপ আইডি

# দেশ এবং পতাকা ইমোজি
COUNTRIES = {
    "US": "🇺🇸 US",
    "UK": "🇬🇧 UK",
    "Canada": "🇨🇦 Canada",
    "Israel": "🇮🇱 Israel",
    "Peru": "🇵🇪 Peru",
    "Panama": "🇵🇦 Panama",
    "Slovenia": "🇸🇮 Slovenia",
    "Chad": "🇹🇩 Chad",
    "Afghanistan": "🇦🇫 Afghanistan"
}

# ডুরেশন এবং মূল্য
DURATIONS = {
    "2_hour": {"text": "2 Hour $0.25 🟡", "price": "0.25"},
    "12_hour": {"text": "12 Hour $0.40 🔵", "price": "0.40"},
    "1_day": {"text": "1 Days $0.80 🟢", "price": "0.80"}
}

# পেমেন্ট মেথড
PAYMENT_METHODS = {
    "bkash": "Bkash",
    "nagad": "Nagad",
    "binance": "Binance"
}

def start(update: Update, context: CallbackContext) -> None:
    """/start কমান্ড হ্যান্ডলার"""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Buy Proxy 🎉", callback_data="buy_proxy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"Hay {user.first_name} How Are You",
        reply_markup=reply_markup
    )

def button(update: Update, context: CallbackContext) -> None:
    """বাটন ক্লিক হ্যান্ডলার"""
    query = update.callback_query
    query.answer()

    if query.data == "buy_proxy":
        # Buy Proxy বাটনে ক্লিক করলে
        show_country_buttons(query)
    elif query.data in COUNTRIES:
        # দেশ সিলেক্ট করলে
        context.user_data["selected_country"] = query.data
        show_duration_buttons(query)
    elif query.data == "others":
        # Others বাটনে ক্লিক করলে
        query.edit_message_text("If You want Others country Proxy Please Inbox Admin")
    elif query.data in DURATIONS:
        # ডুরেশন সিলেক্ট করলে
        context.user_data["selected_duration"] = query.data
        show_payment_info(query, context)
    elif query.data == "confirm":
        # Confirm বাটনে ক্লিক করলে
        handle_confirmation(query, context)
    elif query.data == "cancel":
        # Cancel বাটনে ক্লিক করলে
        query.edit_message_text("Order has been cancelled.")

def show_country_buttons(query):
    """দেশ সিলেক্ট করার বাটন দেখাবে"""
    keyboard = []
    # 2টি কলামে বাটন সাজানো
    countries_list = list(COUNTRIES.items())
    for i in range(0, len(countries_list), 2):
        row = []
        if i < len(countries_list):
            country_code, country_name = countries_list[i]
            row.append(InlineKeyboardButton(country_name, callback_data=country_code))
        if i+1 < len(countries_list):
            country_code, country_name = countries_list[i+1]
            row.append(InlineKeyboardButton(country_name, callback_data=country_code))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("Others 🌍", callback_data="others")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Which Country Proxy You Want..?",
        reply_markup=reply_markup
    )

def show_duration_buttons(query):
    """ডুরেশন সিলেক্ট করার বাটন দেখাবে"""
    keyboard = []
    for duration_key, duration_info in DURATIONS.items():
        keyboard.append(
            [InlineKeyboardButton(duration_info["text"], callback_data=duration_key)]
        )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="How long do you want to take it for?",
        reply_markup=reply_markup
    )

def show_payment_info(query, context):
    """পেমেন্ট ইনফরমেশন দেখাবে"""
    selected_country = context.user_data.get("selected_country", "Unknown")
    selected_duration = context.user_data.get("selected_duration", "2_hour")
    duration_info = DURATIONS.get(selected_duration, {"text": "", "price": "0.00"})
    
    message_text = (
        "Pay And Give Screenshot Here ✅ After Payment Press Confirm Button ✅\n\n"
        f"Bkash: \n"
        f"Nagad: \n"
        f"Binance: 1119515774\n"
        f"Amount: ${duration_info['price']}\n"
        f"Country: {COUNTRIES.get(selected_country, selected_country)}\n"
        "For More Payment Please Contact To Admin ✅"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Confirm ✅", callback_data="confirm"),
            InlineKeyboardButton("Cancel ❌", callback_data="cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup
    )

def handle_confirmation(query, context):
    """অর্ডার কনফার্মেশন হ্যান্ডলার"""
    user = query.from_user
    selected_country = context.user_data.get("selected_country", "Unknown")
    selected_duration = context.user_data.get("selected_duration", "2_hour")
    duration_info = DURATIONS.get(selected_duration, {"text": "", "price": "0.00"})
    
    # অ্যাডমিন গ্রুপে নোটিফিকেশন পাঠানো
    admin_message = (
        "New Order Arrived!\n\n"
        f"User Name: {user.full_name}\n"
        f"Username: @{user.username}\n"
        f"Country: {COUNTRIES.get(selected_country, selected_country)}\n"
        f"Duration: {duration_info['text']}"
    )
    
    context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=admin_message
    )
    
    # ইউজারকে কনফার্মেশন মেসেজ
    query.edit_message_text("Your order has been confirmed! Admin will contact you soon.")

def main():
    """মেইন ফাংশন"""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # কমান্ড হ্যান্ডলার
    dispatcher.add_handler(CommandHandler("start", start))

    # ক্যালব্যাক কুয়েরি হ্যান্ডলার
    dispatcher.add_handler(CallbackQueryHandler(button))

    # মেসেজ হ্যান্ডলার
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, start))

    # বট শুরু করুন
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

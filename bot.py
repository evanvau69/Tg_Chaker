import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext,
)

# লগিং কনফিগারেশন
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# এনভায়রনমেন্ট ভেরিয়েবল
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-1001234567890")  # আপনার অ্যাডমিন গ্রুপ আইডি দিয়ে প্রতিস্থাপন করুন

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
    "bkash": "Bkash: Not Added",
    "nagad": "Nagad: Not Added",
    "binance": "Binance: 1119515774"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ব্যবহারকারী /start কমান্ড দিলে এই ফাংশন কল হবে"""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Buy Proxy 🎉", callback_data="buy_proxy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hay {user.first_name} How Are You",
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ইনলাইন বাটনে ক্লিক করলে এই ফাংশন কল হবে"""
    query = update.callback_query
    await query.answer()

    if query.data == "buy_proxy":
        await show_country_buttons(query)
    elif query.data in COUNTRIES:
        context.user_data["selected_country"] = query.data
        await show_duration_buttons(query)
    elif query.data == "others":
        await query.edit_message_text("If You want Others country Proxy Please Inbox Admin @Zero_proxy_1 ")
    elif query.data in DURATIONS:
        context.user_data["selected_duration"] = query.data
        await show_payment_info(query, context)
    elif query.data == "confirm":
        await handle_confirmation(query, context)
    elif query.data == "cancel":
        await query.edit_message_text("Order has been cancelled.")

async def show_country_buttons(query):
    """দেশ নির্বাচনের বাটন দেখাবে"""
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
    await query.edit_message_text(
        text="Which Country Proxy You Want..?",
        reply_markup=reply_markup
    )

async def show_duration_buttons(query):
    """সময়কাল নির্বাচনের বাটন দেখাবে"""
    keyboard = []
    for duration_key, duration_info in DURATIONS.items():
        keyboard.append(
            [InlineKeyboardButton(duration_info["text"], callback_data=duration_key)]
        )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="How long do you want to take it for?",
        reply_markup=reply_markup
    )

async def show_payment_info(query, context):
    """পেমেন্ট তথ্য দেখাবে"""
    selected_country = context.user_data.get("selected_country", "Unknown")
    selected_duration = context.user_data.get("selected_duration", "2_hour")
    duration_info = DURATIONS.get(selected_duration, {"text": "", "price": "0.00"})
    
    payment_text = "\n".join([f"{method}: {details}" for method, details in PAYMENT_METHODS.items()])
    
    message_text = (
        "Pay And Give Screenshot Here ✅ After Payment Press Confirm Button ✅\n\n"
        f"{payment_text}\n"
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
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup
    )

async def handle_confirmation(query, context):
    """অর্ডার কনফার্মেশন হ্যান্ডেল করবে"""
    user = query.from_user
    selected_country = context.user_data.get("selected_country", "Unknown")
    selected_duration = context.user_data.get("selected_duration", "2_hour")
    duration_info = DURATIONS.get(selected_duration, {"text": "", "price": "0.00"})
    
    # অ্যাডমিন গ্রুপে নোটিফিকেশন পাঠানো
    admin_message = (
        "🚀 New Order Arrived!\n\n"
        f"👤 User: {user.full_name} (@{user.username if user.username else 'N/A'})\n"
        f"🌍 Country: {COUNTRIES.get(selected_country, selected_country)}\n"
        f"⏳ Duration: {duration_info['text']}\n"
        f"💰 Amount: ${duration_info['price']}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=admin_message
        )
        await query.edit_message_text("✅ Your order has been confirmed! Admin will contact you soon.")
    except Exception as e:
        logger.error(f"Error sending message to admin group: {e}")
        await query.edit_message_text("✅ Your order has been received! Please wait for admin confirmation.")

def main() -> None:
    """এপ্লিকেশন শুরু করবে"""
    application = Application.builder().token(TOKEN).build()

    # কমান্ড হ্যান্ডলার
    application.add_handler(CommandHandler("start", start))

    # ক্যালব্যাক কুয়েরি হ্যান্ডলার
    application.add_handler(CallbackQueryHandler(button_click))

    # মেসেজ হ্যান্ডলার
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    # Render-এর জন্য পোর্ট কনফিগারেশন
    port = int(os.environ.get("PORT", 5000))
    
    # Webhook এর পরিবর্তে Polling ব্যবহার করছি
    application.run_polling()

if __name__ == '__main__':
    main()

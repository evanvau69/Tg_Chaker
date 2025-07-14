import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from dotenv import load_dotenv

# .env ফাইল থেকে পরিবেশ ভেরিয়েবল লোড করা
load_dotenv()

# API Token এবং Group Chat ID পরিবেশ থেকে নেওয়া
API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# /start কমান্ডের জন্য ফাংশন
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    welcome_message = f"Hay {user_id}, How Are You?"
    
    # 'Buy Proxy' বাটন
    keyboard = [[InlineKeyboardButton("Buy Proxy 🎉", callback_data='buy_proxy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Buy Proxy বাটনে ক্লিক করলে কি হবে
async def buy_proxy(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # 'Which Country Proxy You Want..?'
    keyboard = [
        [InlineKeyboardButton("US 🇺🇸", callback_data='us')],
        [InlineKeyboardButton("UK 🇬🇧", callback_data='uk')],
        [InlineKeyboardButton("Canada 🇨🇦", callback_data='canada')],
        [InlineKeyboardButton("Israel 🇮🇱", callback_data='israel')],
        [InlineKeyboardButton("Peru 🇵🇪", callback_data='peru')],
        [InlineKeyboardButton("Panama 🇵🇦", callback_data='panama')],
        [InlineKeyboardButton("Slovenia 🇸🇮", callback_data='slovenia')],
        [InlineKeyboardButton("Chad 🇹🇩", callback_data='chad')],
        [InlineKeyboardButton("Afghanistan 🇦🇫", callback_data='afghanistan')],
        [InlineKeyboardButton("Others 🌍", callback_data='others')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text="Which Country Proxy You Want..?", reply_markup=reply_markup)

# Country Selection বাটন ক্লিক করলে
async def country_choice(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # ব্যবহারকারী যে দেশ সিলেক্ট করেছে, তা context তে রাখা
    context.user_data['selected_country'] = query.data

    if query.data == 'others':
        await query.edit_message_text(text="If You want Others country Proxy Please Inbox Admin")
    else:
        # 'How long do you want to take it for?'
        keyboard = [
            [InlineKeyboardButton("2 Hour $0.25 🟡", callback_data='2_hour')],
            [InlineKeyboardButton("12 Hour $0.40 🔵", callback_data='12_hour')],
            [InlineKeyboardButton("1 Day $0.80 🟢", callback_data='1_day')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text="How long do you want to take it for?", reply_markup=reply_markup)

# Time duration বাটন ক্লিক করলে
async def time_duration(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    country = context.user_data.get('selected_country', 'Unknown Country')  # ব্যবহারকারীর সিলেক্ট করা দেশ
    duration = query.data  # সিলেক্ট করা সময় (যেমন 2_hour, 12_hour, 1_day)
    
    # মূল্য নির্ধারণ করা
    if duration == '2_hour':
        amount = '$0.25'
    elif duration == '12_hour':
        amount = '$0.40'
    elif duration == '1_day':
        amount = '$0.80'
    else:
        amount = 'Unknown Amount'

    # Payment message
    payment_message = f"""
    Pay And Give Screenshot Here ✅ After Payment Press Confirm Button ✅

    Bkash :
    Nagad :
    Binance : 1119515774
    Amount : {amount}
    Country : {country}
    For More Payment Please Contact To Admin ✅
    """

    # Confirm এবং Cancel বাটন
    keyboard = [
        [InlineKeyboardButton("Confirm ✅", callback_data='confirm')],
        [InlineKeyboardButton("Cancel ❌", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=payment_message, reply_markup=reply_markup)

# Confirm বাটনে ক্লিক করলে
async def confirm_order(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # ইউজারের নাম, দেশ এবং সময় (Duration) রিটার্ন করার জন্য
    user = query.from_user
    selected_country = context.user_data.get('selected_country', 'Unknown Country')
    selected_duration = context.user_data.get('selected_duration', 'Unknown Duration')

    # Order Confirmation Message
    confirmation_message = f"""
    New Order:

    User Name: {user.first_name}
    Country: {selected_country}
    Duration: {selected_duration}
    """

    # Send Confirmation Message to Group (GROUP_CHAT_ID ব্যবহার করা হচ্ছে)
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=confirmation_message)

    # Send Confirmation Message to User
    await query.edit_message_text(text=confirmation_message)

# Cancel বাটনে ক্লিক করলে
async def cancel_order(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(text="Order Cancelled.")

# Main function to run the bot
async def main() -> None:
    # Application তৈরি
    application = Application.builder().token(API_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(buy_proxy, pattern='buy_proxy'))
    application.add_handler(CallbackQueryHandler(country_choice, pattern='^(us|uk|canada|israel|peru|panama|slovenia|chad|afghanistan|others)$'))
    application.add_handler(CallbackQueryHandler(time_duration, pattern='^(2_hour|12_hour|1_day)$'))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern='confirm'))
    application.add_handler(CallbackQueryHandler(cancel_order, pattern='cancel'))

    # Start the bot
    await application.run_polling()

if __name__ == '__main__':
    import sys
    # Checking if the event loop is already running (to prevent errors)
    if sys.version_info >= (3, 7):
        import asyncio
        asyncio.get_event_loop().run_until_complete(main())
    else:
        # If the loop is already running, use asyncio.ensure_future
        asyncio.ensure_future(main())

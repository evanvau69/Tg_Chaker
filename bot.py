from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# /start কমান্ডের জন্য ফাংশন
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    welcome_message = f"Hay {user_id}, How Are You?"
    
    # 'Buy Proxy' বাটন
    keyboard = [[InlineKeyboardButton("Buy Proxy 🎉", callback_data='buy_proxy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Buy Proxy বাটনে ক্লিক করলে কি হবে
def buy_proxy(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

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
    
    query.edit_message_text(text="Which Country Proxy You Want..?", reply_markup=reply_markup)

# Country Selection বাটন ক্লিক করলে
def country_choice(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    # ব্যবহারকারী যে দেশ সিলেক্ট করেছে, তা context তে রাখা
    context.user_data['selected_country'] = query.data

    if query.data == 'others':
        query.edit_message_text(text="If You want Others country Proxy Please Inbox Admin")
    else:
        # 'How long do you want to take it for?'
        keyboard = [
            [InlineKeyboardButton("2 Hour $0.25 🟡", callback_data='2_hour')],
            [InlineKeyboardButton("12 Hour $0.40 🔵", callback_data='12_hour')],
            [InlineKeyboardButton("1 Day $0.80 🟢", callback_data='1_day')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text="How long do you want to take it for?", reply_markup=reply_markup)

# Time duration বাটন ক্লিক করলে
def time_duration(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

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

    Bkash : Not Added
    Nagad : Not Added
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
    
    query.edit_message_text(text=payment_message, reply_markup=reply_markup)

# Confirm বাটনে ক্লিক করলে
def confirm_order(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

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

    # Send Confirmation Message to Group (replace 'YOUR_GROUP_CHAT_ID' with actual group chat ID)
    context.bot.send_message(chat_id='-1002795045866', text=confirmation_message)

    # Send Confirmation Message to User
    query.edit_message_text(text=confirmation_message)

# Cancel বাটনে ক্লিক করলে
def cancel_order(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    query.edit_message_text(text="Order Cancelled.")

# Main function to run the bot
def main() -> None:
    # Bot token from BotFather
    updater = Updater("8039756158:AAH1HKrDS2nZ-oybrcM9oR3BS8XKqSeDdKQ")

    # Handlers
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CallbackQueryHandler(buy_proxy, pattern='buy_proxy'))
    updater.dispatcher.add_handler(CallbackQueryHandler(country_choice, pattern='^(us|uk|canada|israel|peru|panama|slovenia|chad|afghanistan|others)$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(time_duration, pattern='^(2_hour|12_hour|1_day)$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(confirm_order, pattern='confirm'))
    updater.dispatcher.add_handler(CallbackQueryHandler(cancel_order, pattern='cancel'))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

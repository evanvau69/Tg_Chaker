import os
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# বট কনফিগারেশন
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID', '-1002832508143'))
ADMINS = set(map(int, os.getenv('ADMINS', '6165060012').split()))
SECRET_TOKEN = os.getenv('SECRET_TOKEN', ''.join(random.choices(string.ascii_letters + string.digits, k=32)))

# ডাটাবেস সিমুলেশন
user_data = {}
spam_list = set()

def generate_order_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

def is_admin(user_id):
    return user_id in ADMINS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("Twilio Buy 🎉", callback_data='twilio_buy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('TP Buy Zone - স্বাগতম!', reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'twilio_buy':
        keyboard = [
            [InlineKeyboardButton("৫ টি ✅", callback_data='tokens_5')],
            [InlineKeyboardButton("১০ টি ✅", callback_data='tokens_10')],
            [InlineKeyboardButton("১৫ টি ✅", callback_data='tokens_15')],
            [InlineKeyboardButton("২০ টি ✅", callback_data='tokens_20')],
            [InlineKeyboardButton("Back 🔙", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text='প্রতিটি টোকেনের মূল্য ১০ টাকা ❄️ আপনি কতোটি টোকেন নিতে চাচ্ছেন..?',
            reply_markup=reply_markup
        )

    elif query.data.startswith('tokens_'):
        tokens = int(query.data.split('_')[1])
        price = tokens * 10
        binance_rate = tokens * 0.9
        order_id = generate_order_id()
        user = query.from_user

        user_data[user.id] = {
            'tokens': tokens,
            'price': price,
            'binance_rate': binance_rate,
            'order_id': order_id
        }

        keyboard = [
            [InlineKeyboardButton("Confirm ✅", callback_data='confirm_order')],
            [InlineKeyboardButton("Cancel ❌", callback_data='cancel_order')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = f"""
✅ Price : {price} টাকা
✅ Binance Rate : ${binance_rate}
✅ Your Order Id : {order_id}
✅ Your Name : {user.first_name or 'N/A'}
✅ Your Chat Id : {user.id}
✅ Your Username : @{user.username or 'N/A'}

✅ Bkash : 0123456789
✅ Nagad : 0123456789
✅ Binance : binance_id

পেমেন্ট করে স্কিনশর্ট সেন্ড করবেন তার পর Confirm এ ক্লিক করবেন এবং ১০ মিনিটের মধ্যে আপনার পণ্য দেওয়া হবে ✅

পেমেন্ট না করে Confirm বাটনে ক্লিক করলে আপনাকে চিরদিনের জন্য Spam করানো হবে ✅
        """
        await query.edit_message_text(text=message_text, reply_markup=reply_markup)

    elif query.data == 'back_to_main':
        keyboard = [[InlineKeyboardButton("Twilio Buy 🎉", callback_data='twilio_buy')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text='TP Buy Zone - স্বাগতম!', reply_markup=reply_markup)

    elif query.data == 'confirm_order':
        user = query.from_user
        if user.id in spam_list:
            await query.edit_message_text(text='আপনাকে স্প্যাম লিস্টে রাখা হয়েছে!')
            return

        order_data = user_data.get(user.id, {})
        
        group_message = f"""
📌 নতুন অর্ডার 📌
✅ Tokens: {order_data.get('tokens', 0)}
✅ Price: {order_data.get('price', 0)} টাকা
✅ Binance Rate: ${order_data.get('binance_rate', 0)}
✅ Order ID: {order_data.get('order_id', 'N/A')}
✅ User: @{user.username or 'N/A'} ({user.first_name or 'N/A'})
✅ Chat ID: {user.id}
        """
        await context.bot.send_message(chat_id=GROUP_ID, text=group_message)
        await query.edit_message_text(text='আপনার অর্ডার কনফার্ম করা হয়েছে! ১০ মিনিটের মধ্যে আপনার পণ্য দেওয়া হবে।')
        del user_data[user.id]

    elif query.data == 'cancel_order':
        user = query.from_user
        if user.id in user_data:
            del user_data[user.id]
        await query.edit_message_text(text='আপনার অর্ডার ক্যানসেল করা হয়েছে।')

# অ্যাডমিন কমান্ডস
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Permission denied!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = ' '.join(context.args)
    await update.message.reply_text(f"Broadcast sent to X users")

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Permission denied!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /add_admin <user_id>")
        return

    try:
        new_admin = int(context.args[0])
        ADMINS.add(new_admin)
        await update.message.reply_text(f"User {new_admin} added as admin")
    except ValueError:
        await update.message.reply_text("Invalid user ID")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Permission denied!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /remove_admin <user_id>")
        return

    try:
        admin_id = int(context.args[0])
        if admin_id in ADMINS:
            ADMINS.remove(admin_id)
            await update.message.reply_text(f"User {admin_id} removed from admin")
        else:
            await update.message.reply_text("User is not an admin")
    except ValueError:
        await update.message.reply_text("Invalid user ID")

async def spam_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Permission denied!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /spam <user_id>")
        return

    try:
        user_id = int(context.args[0])
        spam_list.add(user_id)
        await update.message.reply_text(f"User {user_id} added to spam list")
    except ValueError:
        await update.message.reply_text("Invalid user ID")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # হ্যান্ডলার রেজিস্টার
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler('broadcast', broadcast))
    application.add_handler(CommandHandler('add_admin', add_admin))
    application.add_handler(CommandHandler('remove_admin', remove_admin))
    application.add_handler(CommandHandler('spam', spam_user))

    if os.getenv('RENDER'):
        PORT = int(os.getenv('PORT', 10000))
        WEBHOOK_URL = os.getenv('WEBHOOK_URL')
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            secret_token=SECRET_TOKEN,
            drop_pending_updates=True
        )
    else:
        application.run_polling()

if __name__ == '__main__':
    main()

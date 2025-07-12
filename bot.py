import os
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ApplicationBuilder,
    ContextTypes
)
from telegram.constants import ParseMode

# বট কনফিগারেশন
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Render.com এ environment variable থেকে নিবে
GROUP_ID = int(os.getenv('GROUP_ID', '-1002832508143'))  # আপনার গ্রুপ আইডি
ADMINS = set(map(int, os.getenv('ADMINS', '6165060012').split()))  # অ্যাডমিন আইডি লিস্ট

# ডাটাবেসের জন্য (Render.com-এ PostgreSQL বা Redis ব্যবহার করতে পারেন)
user_data = {}
spam_list = set()

# হেল্পার ফাংশন
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
    # এখানে ডাটাবেস থেকে সব ইউজার আইডি নিয়ে ব্রডকাস্ট করতে হবে
    # উদাহরণ:
    # for user_id in all_users:
    #     try:
    #         await context.bot.send_message(chat_id=user_id, text=message)
    #     except:
    #         continue
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

async def webhook(request):
    """Render.com-এ Webhook হ্যান্ডলার"""
    update = Update.de_json(await request.get_json(), bot)
    await dispatcher.process_update(update)
    return {"status": "ok"}

def main() -> None:
    """Render.com-এ Web Service হিসেবে রান করবে"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # কমান্ড হ্যান্ডলার
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # অ্যাডমিন কমান্ডস
    application.add_handler(CommandHandler('broadcast', broadcast))
    application.add_handler(CommandHandler('add_admin', add_admin))
    application.add_handler(CommandHandler('remove_admin', remove_admin))
    application.add_handler(CommandHandler('spam', spam_user))

    # Render.com-এ Web Service হিসেবে রান করবে
    if os.getenv('RENDER'):
        PORT = int(os.getenv('PORT', 10000))
        WEBHOOK_URL = os.getenv('WEBHOOK_URL') + '/webhook'
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL
        )
    else:
        # লোকাল টেস্টিং
        application.run_polling()

if __name__ == '__main__':
    main()

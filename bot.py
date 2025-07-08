import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from telegram.ext.filters import Filters
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

bot_token = '8014475811:AAHnXLAke9XRfNq_LCdhqdcxazMk6nZM8kE'  # Your Bot's Token

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Start Command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("হ্যালো! আমাকে আপনার টেলিগ্রাম একাউন্টের নাম্বার দিন।")

# Login Command
def login(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    phone_number = user_input.strip()  # User's phone number
    
    # Create Telegram client
    client = TelegramClient('session_name', phone_number)  # API_ID and API_HASH will be automatically fetched after login
    
    try:
        # Try logging in with OTP
        client.connect()
        if not client.is_user_authorized():
            client.send_code_request(phone_number)
            update.message.reply_text(f"OTP পাঠানো হয়েছে আপনার নাম্বারে {phone_number}. OTP দিন:")
            
            # Wait for OTP from user
            context.user_data['phone_number'] = phone_number  # Store phone number for later
            return
        
        update.message.reply_text(f"{phone_number} এর সাথে লগ ইন করা হয়েছে।")
        client.disconnect()
    except SessionPasswordNeededError:
        update.message.reply_text("পাসওয়ার্ড দিন:")
        context.user_data['phone_number'] = phone_number  # Store phone number for password entry
        return

# Verify OTP
def verify_otp(update: Update, context: CallbackContext) -> None:
    otp = update.message.text.strip()
    phone_number = context.user_data.get('phone_number', None)

    if not phone_number:
        update.message.reply_text("অনুগ্রহ করে প্রথমে আপনার নাম্বার দিন।")
        return

    client = TelegramClient('session_name', phone_number)
    client.connect()
    
    try:
        client.sign_in(phone_number, otp)
        update.message.reply_text(f"আপনার {phone_number} নাম্বারে লগ ইন সফল!")
    except SessionPasswordNeededError:
        password = update.message.text.strip()
        client.sign_in(password=password)
        update.message.reply_text(f"{phone_number} নাম্বারে লগ ইন সফল!")
    
    client.disconnect()

# Check Phone Numbers
def check_numbers(update: Update, context: CallbackContext) -> None:
    phone_numbers = update.message.text.strip().split()
    
    valid_numbers = []
    invalid_numbers = []
    
    for number in phone_numbers:
        client = TelegramClient('session_name', number)
        client.connect()

        try:
            if client.is_user_authorized():
                valid_numbers.append(number)
            else:
                invalid_numbers.append(number)
        except Exception as e:
            invalid_numbers.append(number)
        
        client.disconnect()
    
    update.message.reply_text(f"টেলিগ্রাম একাউন্ট খোলা আছে: {', '.join(valid_numbers)}")
    update.message.reply_text(f"টেলিগ্রাম একাউন্ট খোলা নেই: {', '.join(invalid_numbers)}")

# Main Function
def main():
    updater = Updater(bot_token)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("login", login))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, verify_otp))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_numbers))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

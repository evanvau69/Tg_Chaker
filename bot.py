import os
import asyncio
from pyrogram import Client, errors
from pyrogram.session import Session
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# এনভায়রনমেন্ট ভেরিয়েবল লোড করছি
load_dotenv()

app = Flask(__name__)

# ইউজার সেশন স্টোরেজ
user_sessions = {}

class TelegramCheckerBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")  # বট টোকেন
        self.api_id = None
        self.api_hash = None
        self.client = None

    async def initialize_client(self, user_id):
        # প্রতিটি ইউজারের জন্য নতুন ক্লায়েন্ট তৈরি করছি
        session_name = f"user_{user_id}"
        self.client = Client(session_name, in_memory=True)
        return self.client

    async def request_credentials(self, user_id):
        # ইউজারের বর্তমান স্টেপ স্টোর করছি
        user_sessions[user_id] = {"step": "request_number"}
        return {
            "message": "আপনার টেলিগ্রাম ফোন নাম্বার দিন (কান্ট্রি কোড সহ):",
            "next_step": "wait_for_number"
        }

    async def process_phone_number(self, user_id, phone_number):
        user_sessions[user_id] = {
            "step": "request_otp",
            "phone_number": phone_number
        }
        
        try:
            await self.client.connect()
            sent_code = await self.client.send_code(phone_number)
            
            user_sessions[user_id].update({
                "phone_code_hash": sent_code.phone_code_hash,
                "sent_code": sent_code
            })
            
            return {
                "message": "আপনার মোবাইলে প্রেরিত ৫ ডিজিটের OTP কোডটি দিন:",
                "next_step": "wait_for_otp"
            }
        except Exception as e:
            return {
                "error": f"কোড পাঠাতে সমস্যা: {str(e)}",
                "next_step": "error"
            }

    async def process_otp(self, user_id, otp):
        session_data = user_sessions[user_id]
        session_data["step"] = "check_2fa"
        
        try:
            await self.client.sign_in(
                session_data["phone_number"],
                session_data["phone_code_hash"],
                otp
            )
            
            # সফলভাবে লগইন হয়েছে
            session_data["step"] = "logged_in"
            session_data["is_authenticated"] = True
            
            # ক্লায়েন্ট থেকে API ID এবং HASH নিচ্ছি
            self.api_id = self.client.api_id
            self.api_hash = self.client.api_hash
            
            return {
                "message": "✅ সফলভাবে লগইন করা হয়েছে!\n\nএখন চেক করার জন্য ফোন নাম্বারগুলোর লিস্ট দিন (প্রতি লাইনে একটি নাম্বার):\n\nউদাহরণ:\n1416727252526\n1627265272726\n52726255262662",
                "next_step": "wait_for_number_list"
            }
        except errors.SessionPasswordNeeded:
            session_data["step"] = "request_2fa"
            return {
                "message": "এই অ্যাকাউন্টে 2FA চালু আছে। আপনার পাসওয়ার্ড দিন:",
                "next_step": "wait_for_2fa"
            }
        except Exception as e:
            return {
                "error": f"লগইনে সমস্যা: {str(e)}",
                "next_step": "error"
            }

    async def process_2fa(self, user_id, password):
        session_data = user_sessions[user_id]
        
        try:
            await self.client.check_password(password)
            
            # সফলভাবে লগইন হয়েছে
            session_data["step"] = "logged_in"
            session_data["is_authenticated"] = True
            
            # ক্লায়েন্ট থেকে API ID এবং HASH নিচ্ছি
            self.api_id = self.client.api_id
            self.api_hash = self.client.api_hash
            
            return {
                "message": "✅ সফলভাবে লগইন করা হয়েছে!\n\nএখন চেক করার জন্য ফোন নাম্বারগুলোর লিস্ট দিন (প্রতি লাইনে একটি নাম্বার):\n\nউদাহরণ:\n1416727252526\n1627265272726\n52726255262662",
                "next_step": "wait_for_number_list"
            }
        except Exception as e:
            return {
                "error": f"পাসওয়ার্ড ভেরিফিকেশনে সমস্যা: {str(e)}",
                "next_step": "error"
            }

    async def check_numbers(self, user_id, numbers_list):
        if not user_sessions[user_id].get("is_authenticated"):
            return {
                "error": "আপনি লগইন করেননি। প্রথমে লগইন করুন।",
                "next_step": "error"
            }
        
        # নাম্বার লিস্ট প্রসেসিং
        numbers = [n.strip() for n in numbers_list.split("\n") if n.strip()]
        has_account = []
        no_account = []
        
        for number in numbers:
            try:
                await self.client.send_code(number)
                has_account.append(number)
            except errors.PhoneNumberInvalid:
                no_account.append(f"{number} - অবৈধ নাম্বার")
            except errors.PhoneNumberBanned:
                no_account.append(f"{number} - ব্যান করা নাম্বার")
            except errors.PhoneNumberUnoccupied:
                no_account.append(number)
            except Exception as e:
                no_account.append(f"{number} - এরর: {str(e)}")
        
        # ফরম্যাটেড রেসপন্স তৈরি
        response_message = ""
        
        if has_account:
            response_message += f"✅ রেজিস্টার্ড নাম্বার ({len(has_account)} টি):\n"
            response_message += "\n".join(has_account) + "\n\n"
        
        if no_account:
            response_message += f"❎ নন-রেজিস্টার্ড নাম্বার ({len(no_account)} টি):\n"
            response_message += "\n".join(no_account)
        
        return {
            "message": response_message,
            "has_account": has_account,
            "no_account": no_account,
            "next_step": "completed"
        }

# ফ্লাস্ক এন্ডপয়েন্টস
bot = TelegramCheckerBot()

@app.route("/start", methods=["POST"])
def start():
    user_id = request.json.get("user_id")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(bot.initialize_client(user_id))
    response = loop.run_until_complete(bot.request_credentials(user_id))
    loop.close()
    return jsonify(response)

@app.route("/process", methods=["POST"])
def process():
    user_id = request.json.get("user_id")
    user_input = request.json.get("input")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    session_data = user_sessions.get(user_id, {})
    
    if session_data.get("step") == "wait_for_number":
        response = loop.run_until_complete(bot.process_phone_number(user_id, user_input))
    elif session_data.get("step") == "wait_for_otp":
        response = loop.run_until_complete(bot.process_otp(user_id, user_input))
    elif session_data.get("step") == "wait_for_2fa":
        response = loop.run_until_complete(bot.process_2fa(user_id, user_input))
    elif session_data.get("step") == "wait_for_number_list":
        response = loop.run_until_complete(bot.check_numbers(user_id, user_input))
    else:
        response = {"error": "অজানা স্টেপ", "next_step": "error"}
    
    loop.close()
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

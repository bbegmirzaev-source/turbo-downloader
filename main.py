import telebot
from telebot import types
import sqlite3
import yt_dlp
import os
from flask import Flask
from threading import Thread

TOKEN = "8692887677:AAE4bNG-McXCUwnv5dYsRboGFlv2FyIFzQc"
ADMIN_ID = 7801965871
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- BAZA ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

# --- BUYRUQLAR ---
@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.chat.id,))
    conn.commit()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
               types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    bot.send_message(message.chat.id, "Tilni tanlang / Выберите язык:", reply_markup=markup)

@bot.message_handler(commands=['stat'])
def get_stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        count = cursor.fetchone()[0]
        bot.reply_to(message, f"📊 <b>Bot foydalanuvchilari:</b> {count} ta.")

@bot.message_handler(commands=['reklama'])
def reklama(message):
    if message.chat.id == ADMIN_ID:
        msg = bot.reply_to(message, "📝 Reklama matnini yuboring:")
        bot.register_next_step_handler(msg, send_reklama)

def send_reklama(message):
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    count = 0
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            count += 1
        except: continue
    bot.reply_to(message, f"✅ Reklama {count} ta foydalanuvchiga yuborildi.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_lang(call):
    lang = call.data.split('_')[1]
    text = "👋 <b>Assalomu alaykum!</b>\n🔗 Iltimos, video havolasini yuboring:" if lang == 'uz' else "👋 <b>Здравствуйте!</b>\n🔗 Пожалуйста, отправьте ссылку на видео:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# --- YUKLASH ---
import requests

@bot.message_handler(func=lambda message: message.text and "pin.it" in message.text)
def downloader(message):
    status = bot.reply_to(message, "⏳ <b>Havola kengaytirilmoqda...</b>")
    try:
        # Qisqa havolani to'liq manzilga aylantirish
        url = message.text
        session = requests.Session()
        resp = session.head(url, allow_redirects=True)
        long_url = resp.url
        
        # Endi to'liq manzil bilan API'ga so'rov yuboramiz
        api_url = f"https://pinterest-video-api.vercel.app/api?url={long_url}"
        response = requests.get(api_url).json()
        
        if 'video_url' in response:
            bot.send_video(message.chat.id, response['video_url'])
            bot.delete_message(message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ <b>API javob bermadi. Pinterest himoyasi faol.</b>", message.chat.id, status.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ <b>Xatolik:</b> {e}", message.chat.id, status.message_id)
# --- SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()

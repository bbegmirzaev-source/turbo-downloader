import telebot
from telebot import types
import yt_dlp
import os
import sqlite3
from flask import Flask
from threading import Thread

TOKEN = "8692887677:AAE4bNG-McXCUwnv5dYsRboGFlv2FyIFzQc"
ADMIN_ID = 7801965871  # O'z ID raqamingizni yozing
bot = telebot.TeleBot(TOKEN)

# Ma'lumotlar bazasi
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

# Render uchun port ochish
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# Til sozlamalari
USER_LANG = {}

@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.chat.id,))
    conn.commit()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
               types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    bot.send_message(message.chat.id, "Salom! Tilni tanlang / Выберите язык:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    USER_LANG[call.message.chat.id] = call.data
    text = "Link yuboring!" if call.data == "lang_uz" else "Отправьте ссылку!"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['stat'])
def stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        bot.reply_to(message, f"👥 Bot foydalanuvchilari: {cursor.fetchone()[0]}")

@bot.message_handler(commands=['reklama'])
def reklama(message):
    if message.chat.id == ADMIN_ID:
        msg = bot.reply_to(message, "Reklama matnini yuboring:")
        bot.register_next_step_handler(msg, send_reklama)

def send_reklama(message):
    cursor.execute('SELECT id FROM users')
    for user in cursor.fetchall():
        try: bot.send_message(user[0], message.text)
        except: pass
    bot.reply_to(message, "✅ Reklama yuborildi.")

@bot.message_handler(func=lambda message: True)
def downloader(message):
    url = message.text
    if not url.startswith("http"): return
    msg = bot.reply_to(message, "⏳ Yuklanmoqda...")
    
    ydl_opts = {
        'format': 'best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            bot.send_video(message.chat.id, open(filename, 'rb'))
            bot.delete_message(message.chat.id, msg.message_id)
            os.remove(filename)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {str(e)[:50]}", message.chat.id, msg.message_id)

bot.infinity_polling()
# main.py ning eng oxiriga buni qo'ying
if __name__ == '__main__':
    bot.remove_webhook()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

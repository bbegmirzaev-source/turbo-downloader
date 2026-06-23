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

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "👋 Assalomu alaykum! Video havolasini yuboring.")

@bot.message_handler(commands=['stat'])
def get_stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        count = cursor.fetchone()[0]
        bot.reply_to(message, f"📊 Bot foydalanuvchilari: {count} ta.")

@bot.message_handler(commands=['reklama'])
def reklama(message):
    if message.chat.id == ADMIN_ID:
        msg = bot.reply_to(message, "📝 Reklama matnini yuboring:")
        bot.register_next_step_handler(msg, send_reklama)

def send_reklama(message):
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    for user in users:
        try: bot.send_message(user[0], message.text)
        except: pass
    bot.reply_to(message, "✅ Reklama yuborildi.")

@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def downloader(message):
    status = bot.reply_to(message, "⏳ Yuklanmoqda...")
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.mp4',
            'quiet': True,
            'nocheckcertificate': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([message.text])
        
        if os.path.exists('video.mp4'):
            with open('video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video)
            os.remove('video.mp4')
            bot.delete_message(message.chat.id, status.message_id)
        else:
            raise Exception("Fayl topilmadi")
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", message.chat.id, status.message_id)

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()

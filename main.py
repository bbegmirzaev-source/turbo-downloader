import telebot
from telebot import types
import sqlite3
import yt_dlp
import os
from flask import Flask
from threading import Thread

# --- KONFIGURATSIYA ---
TOKEN = "8692887677:AAE4bNG-McXCUwnv5dYsRboGFlv2FyIFzQc"
ADMIN_ID = 7801965871
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- BAZA BILAN ISHLASH ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

# --- BUYRUQLAR ---
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
        bot.reply_to(message, f"📊 <b>Bot foydalanuvchilari:</b> {count} ta.")

@bot.message_handler(commands=['reklama'])
def start_reklama(message):
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

# --- VIDEO YUKLASH ---
@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def downloader(message):
    if "youtube.com" in message.text or "youtu.be" in message.text:
        bot.reply_to(message, "❌ YouTube qo'llab-quvvatlanmaydi.")
        return
    
    status = bot.reply_to(message, "⏳ Yuklanmoqda...")
    
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'vid_{message.chat.id}.mp4',
            'quiet': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([message.text])
        
        filename = f'vid_{message.chat.id}.mp4'
        
        if os.path.exists(filename):
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video)
            os.remove(filename)
            bot.delete_message(message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ Video topilmadi.", message.chat.id, status.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: Pinterest himoyasi faol.", message.chat.id, status.message_id)

# --- SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()

import telebot
from telebot import types
import yt_dlp
import os
import sqlite3

# TOKENINGIZNI VA ADMIN IDINGIZNI SHU YERGA YOZING
TOKEN = "8692887677:AAGWsUowGR_TaHit0BfEv_XRvvG-g710Dwg"
ADMIN_ID = 7801965871 

bot = telebot.TeleBot(TOKEN)

# Baza yaratish
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

# --- START VA TIL TANLASH ---
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"))
    markup.add(types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "Salom! Tilni tanlang / Выберите язык:", reply_markup=main_menu())

# --- ADMIN PANEL ---
@bot.message_handler(commands=['stat'])
def stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        count = cursor.fetchone()[0]
        bot.reply_to(message, f"👥 Jami foydalanuvchilar: {count}")

@bot.message_handler(commands=['reklama'])
def reklama(message):
    if message.chat.id == ADMIN_ID:
        msg = bot.reply_to(message, "Reklama matnini yuboring:")
        bot.register_next_step_handler(msg, send_reklama)

def send_reklama(message):
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    for user in users:
        try: bot.send_message(user[0], message.text)
        except: pass
    bot.reply_to(message, "✅ Reklama barchaga yuborildi!")

# --- VIDEO YUKLASH ---
@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    if not url.startswith("http"): return

    msg = bot.reply_to(message, "⏳ Yuklanmoqda...")
    ydl_opts = {
        'format': 'best',
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            bot.edit_message_text("✅ Yuklandi! Yuborilmoqda...", message.chat.id, msg.message_id)
            bot.send_video(message.chat.id, open(filename, 'rb'))
            os.remove(filename)
            bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {str(e)}", message.chat.id, msg.message_id)

bot.polling(none_stop=True)
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

t = Thread(target=run)
t.start()


import telebot
from telebot import types
import sqlite3
import yt_dlp
import os
from flask import Flask
from threading import Thread

TOKEN = "8692887677:AAE4bNG-McXCUwnv5dYsRboGFlv2FyIFzQc"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- BAZA VA TIL ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

LANGS = {
    'uz': {'welcome': "👋 <b>Assalomu alaykum!</b>\nMen video yuklovchi botman.", 'ask': "🔗 Iltimos, video havolasini yuboring:"},
    'ru': {'welcome': "👋 <b>Здравствуйте!</b>\nЯ бот для скачивания видео.", 'ask': "🔗 Пожалуйста, отправьте ссылку на видео:"}
}

@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.chat.id,))
    conn.commit()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
               types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    bot.send_message(message.chat.id, "Tilni tanlang / Выберите язык:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_lang(call):
    lang = call.data.split('_')[1]
    bot.edit_message_text(LANGS[lang]['welcome'] + "\n\n" + LANGS[lang]['ask'], 
                          call.message.chat.id, call.message.message_id)

# --- YUKLASH FUNKSIYASI ---
@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def downloader(message):
    status = bot.reply_to(message, "⏳ <b>Yuklanmoqda...</b>")
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.mp4',
            'quiet': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([message.text])
        
        if os.path.exists('video.mp4'):
            with open('video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video)
            os.remove('video.mp4')
            bot.delete_message(message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ <b>Fayl topilmadi.</b>", message.chat.id, status.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ <b>Xatolik:</b> {e}", message.chat.id, status.message_id)

# --- FLASK SERVER (RENDER UCHUN) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()

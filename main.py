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

# --- TIL VA MATNLAR ---
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

@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def downloader(message):
    if "youtube.com" in message.text or "youtu.be" in message.text:
        bot.reply_to(message, "❌ <b>Uzr, bu bot YouTube videolarini qo'llab-quvvatlamaydi.</b>")
        return
    
    status = bot.reply_to(message, "⏳ <b>Yuklanmoqda...</b>")
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'nocheckcertificate': True,
            'postprocessors': [], # Ffmpeg ishlatmaslik uchun
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            filename = ydl.prepare_filename(info)
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video)
            os.remove(filename)
            bot.delete_message(message.chat.id, status.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ <b>Xatolik yuz berdi.</b>", message.chat.id, status.message_id)

# --- FLASK SERVER (Render uchun) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()


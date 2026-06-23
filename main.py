import telebot
from telebot import types
import yt_dlp
import os
import sqlite3

# O'z ma'lumotlaringizni kiriting
TOKEN = "8692887677:AAE4bNG-McXCUwnv5dYsRboGFlv2FyIFzQc"
ADMIN_ID = 7801965871 

bot = telebot.TeleBot(TOKEN)
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.chat.id,))
    conn.commit()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"))
    markup.add(types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    bot.send_message(message.chat.id, "Salom! Tilni tanlang / Выберите язык:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "lang_uz":
        bot.edit_message_text("Yaxshi! Endi yuklamoqchi bo'lgan YouTube video havolasini yuboring.", call.message.chat.id, call.message.message_id)
    elif call.data == "lang_ru":
        bot.edit_message_text("Отлично! Теперь отправьте ссылку на видео YouTube.", call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['stat'])
def stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        count = cursor.fetchone()[0]
        bot.reply_to(message, f"👥 Botdagi jami obunachilar: {count}")

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

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    if "youtube.com" not in url and "youtu.be" not in url: return
    
    msg = bot.reply_to(message, "⏳ Yuklanmoqda...")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        with ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'noplaylist': True,
    # YouTube'ni chalg'itish uchun
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'referer': 'https://www.google.com/',
}
)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {str(e)}", message.chat.id, msg.message_id)

bot.infinity_polling()

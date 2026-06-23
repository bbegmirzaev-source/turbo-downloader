import telebot
from telebot import types
import sqlite3
import yt_dlp
import os

TOKEN = "8692887677:AAE4bNG-McXCUwnv5dYsRboGFlv2FyIFzQc"
ADMIN_ID = 7801965871 # O'z ID raqamingizni kiriting
bot = telebot.TeleBot(TOKEN)

# Ma'lumotlar bazasini ulash
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
conn.commit()

# Til sozlamalari lug'ati
LANGS = {
    'uz': {'start': "Salom! Men video yuklovchi botman.", 'send_link': "Iltimos, video havolasini yuboring."},
    'ru': {'start': "Привет! Я бот для скачивания видео.", 'send_link': "Пожалуйста, отправьте ссылку на видео."}
}
USER_LANG = {}

@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?)', (message.chat.id,))
    conn.commit()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
               types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    bot.send_message(message.chat.id, "Tilni tanlang / Выберите язык:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_lang(call):
    lang = call.data.split('_')[1]
    USER_LANG[call.message.chat.id] = lang
    bot.edit_message_text(LANGS[lang]['send_link'], call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['stat'])
def get_stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        count = cursor.fetchone()[0]
        bot.reply_to(message, f"👥 Bot foydalanuvchilari soni: {count}")

@bot.message_handler(commands=['reklama'])
def start_reklama(message):
    if message.chat.id == ADMIN_ID:
        msg = bot.reply_to(message, "Reklama matnini yuboring:")
        bot.register_next_step_handler(msg, send_reklama)

def send_reklama(message):
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    count = 0
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            count += 1
        except: pass
    bot.reply_to(message, f"✅ Reklama {count} ta foydalanuvchiga yuborildi.")

@bot.message_handler(func=lambda message: True)
def downloader(message):
    if "youtube.com" in message.text or "youtu.be" in message.text:
        bot.reply_to(message, "❌ Uzr, bu bot YouTube bilan ishlamaydi.")
        return
    
    msg = bot.reply_to(message, "⏳ Yuklanmoqda...")
    try:
        ydl_opts = {'format': 'best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            filename = ydl.prepare_filename(info)
            bot.send_video(message.chat.id, open(filename, 'rb'))
            bot.delete_message(message.chat.id, msg.message_id)
            os.remove(filename)
    except Exception as e:
        bot.edit_message_text("❌ Xatolik yuz berdi.", message.chat.id, msg.message_id)

bot.infinity_polling()

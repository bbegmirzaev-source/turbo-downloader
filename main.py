import telebot
from telebot import types
import sqlite3
import yt_dlp
import os

# --- KONFIGURATSIYA ---
TOKEN = "8692887677:AAE4bNG-McXCUwnv5dYsRboGFlv2FyIFzQc"
ADMIN_ID = 7801965871  # O'z ID raqamingizni shu yerga yozing
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
    # Foydalanuvchini bazaga qo'shish
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

# --- STATISTIKA (Admin uchun) ---
@bot.message_handler(commands=['stat'])
def get_stat(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute('SELECT count(*) FROM users')
        count = cursor.fetchone()[0]
        bot.reply_to(message, f"📊 <b>Bot foydalanuvchilari soni:</b> {count} ta.")

# --- REKLAMA (Admin uchun) ---
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

# --- VIDEO YUKLASH (YouTube'siz) ---
@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def downloader(message):
    # YouTube'ni bloklash
    if "youtube.com" in message.text or "youtu.be" in message.text:
        bot.reply_to(message, "❌ <b>Uzr, bu bot YouTube videolarini qo'llab-quvvatlamaydi.</b>")
        return
    
    status = bot.reply_to(message, "⏳ <b>Yuklanmoqda...</b>")
    try:
                ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            filename = ydl.prepare_filename(info)
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video)
            os.remove(filename) # Server xotirasini tozalash
            bot.delete_message(message.chat.id, status.message_id)
    except Exception:
        bot.edit_message_text("❌ <b>Xatolik yuz berdi.</b> Havolani tekshiring.", message.chat.id, status.message_id)

bot.infinity_polling()

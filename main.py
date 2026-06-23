import os
import sqlite3
import telebot
import yt_dlp
import time
from telebot import types
from flask import Flask
from threading import Thread

# Server 24/7 uxlab qolmasligi uchun kichik Web-server
app = Flask('')
@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlamoqda!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 1. BOT SOZLAMALARI
TOKEN = "8692887677:AAGWsUowGR_TaHit0BfEv_XRvvG-g710Dwg"
ADMIN_ID = 7801965871

bot = telebot.TeleBot(TOKEN)

# 2. MA'LUMOTLAR BAZASI
conn = sqlite3.connect("bot_bazasi.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS foydalanuvchilar (
        user_id INTEGER UNIQUE
    )
""")
conn.commit()

def bazaga_qosh(user_id):
    try:
        cursor.execute("INSERT OR IGNORE INTO foydalanuvchilar (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except Exception:
        pass

# 3. START BUYRUG'I
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bazaga_qosh(message.from_user.id)
    bot.reply_to(message, "Salom! Men Instagram, TikTok va YouTube'dan video yuklovchi professional botman.\nMenga shunchaki video havolasini (linkini) yuboring!")

# 4. ADMIN BUYRUQLARI
@bot.message_handler(commands=['stat'])
def admin_stat(message):
    if message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT COUNT(user_id) FROM foydalanuvchilar")
        count = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"📊 **Bot statistikasi:**\n\n👤 Jami foydalanuvchilar soni: {count} ta")

@bot.message_handler(commands=['reklama'])
def start_reklama(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "📝 Reklama matnini yoki rasmini yuboring:")
        bot.register_next_step_handler(msg, send_reklama_to_all)

def send_reklama_to_all(message):
    cursor.execute("SELECT user_id FROM foydalanuvchilar")
    users = cursor.fetchall()
    for user in users:
        try:
            bot.copy_message(chat_id=user[0], from_chat_id=message.chat.id, message_id=message.message_id)
            time.sleep(0.05)
        except Exception:
            pass
    bot.send_message(message.chat.id, "✅ Reklama barchaga yuborildi!")

# 5. HAVOLALARNI TUTISH VA FORMAT TANLASH
@bot.message_handler(func=lambda message: message.text and ("instagram.com" in message.text or "tiktok.com" in message.text or "youtube.com" in message.text or "youtu.be" in message.text))
def handle_links(message):
    url = message.text.strip()
    bazaga_qosh(message.from_user.id)
    
    if "youtube.com" in url or "youtu.be" in url:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_720 = types.InlineKeyboardButton("🎬 720p (Yaxshi)", callback_data=f"yt|720|{url}")
        btn_360 = types.InlineKeyboardButton("🎬 360p (Past)", callback_data=f"yt|360|{url}")
        btn_mp3 = types.InlineKeyboardButton("🎵 MP3 (Audio)", callback_data=f"yt|mp3|{url}")
        markup.add(btn_720, btn_360, btn_mp3)
        bot.send_message(message.chat.id, "🎥 YouTube videosi aniqlandi! Yuklash formatini tanlang:", reply_markup=markup)
    else:
        status = bot.send_message(message.chat.id, "⚡️ Video yuklab olinmoqda...")
        try:
            ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s', 'format': 'best', 'merge_output_format': 'mp4', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if not filename.endswith('.mp4'):
                    filename = os.path.splitext(filename)[0] + '.mp4'
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=f"✨ @{bot.get_me().username} orqali yuklab olindi")
            bot.delete_message(message.chat.id, status.message_id)
            os.remove(filename)
        except Exception as e:
            bot.edit_message_text(f"❌ Xatolik: {str(e)}", message.chat.id, status.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('yt|'))
def callback_youtube(call):
    _, format_type, url = call.data.split('|', 2)
    bot.edit_message_text("⏳ Soʻrovingiz qayta ishlanmoqda, kuting...", call.message.chat.id, call.message.message_id)
    try:
        if format_type == 'mp3':
            ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s', 'format': 'bestaudio/best', 'quiet': True}
        elif format_type == '720':
            ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s', 'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]', 'merge_output_format': 'mp4', 'quiet': True}
        else:
            ydl_opts = {'outtmpl': 'downloads/%(id)s.%(ext)s', 'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]', 'merge_output_format': 'mp4', 'quiet': True}
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                bot.delete_message(call.message.chat.id, call.message.message_id)
                with open(filename, 'rb') as audio:
                    bot.send_audio(call.message.chat.id, audio, caption=f"🎵 @{bot.get_me().username} orqali yuklandi")
            else:
                if not filename.endswith('.mp4'):
                    filename = os.path.splitext(filename)[0] + '.mp4'
                bot.delete_message(call.message.chat.id, call.message.message_id)
                with open(filename, 'rb') as video:
                    bot.send_video(call.message.chat.id, video, caption=f"🎬 Sifat: {format_type}p\n✨ @{bot.get_me().username} orqali yuklandi")
        os.remove(filename)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Xatolik: {str(e)}")

# 6. BOTNI ISHGA TUSHIRISH
if __name__ == '__main__':
    keep_alive() # Web-serverni yoqish
    print("🔥 Bot Koyeb server uchun tayyor...")
    bot.infinity_polling()

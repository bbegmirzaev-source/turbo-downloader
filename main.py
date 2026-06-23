import telebot
import yt_dlp
import os
from flask import Flask
from threading import Thread

TOKEN = "8692887677:AAE4bNG-McXCUwnv5dYsRboGFlv2FyIFzQc"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- YUKLASH FUNKSIYASI ---
@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def downloader(message):
    status = bot.reply_to(message, "⏳ Yuklanmoqda...")
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.mp4',
            'quiet': True,
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

# --- FLASK SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()

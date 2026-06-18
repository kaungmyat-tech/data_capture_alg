import telebot
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise SystemExit("❌ TELEGRAM_TOKEN environment variable not set.\n   Run: export TELEGRAM_TOKEN='your_bot_token'")

bot = telebot.TeleBot(TOKEN)

print("Telegram Bot စတင်နေပါပြီ... Bot ထဲကို CSV ဖိုင် ပို့ပေးလိုက်ပါ။")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.file_name.endswith('.csv'):
        print(f"ဖိုင်တွေ့ပါပြီ: {message.document.file_name}")

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open("raww_addrA.csv", 'wb') as new_file:
            new_file.write(downloaded_file)

        with open("last_chat_id.txt", 'w') as f:
            f.write(str(message.chat.id))
        
        print(f"✅ Chat ID သိမ်းပြီး: {message.chat.id}")
        print("✅ raww_addrA.csv သိမ်းပြီး။ ./script.py ကို Run နိုင်ပါပြီ။")
        
        bot.reply_to(message, "✅ ဖိုင်လက်ခံရရှိပါပြီ။ စာရင်းစစ်ဆေးခြင်း စတင်ပါမည်...")
        os._exit(0)
    else:
        bot.reply_to(message, "❌ CSV ဖိုင်သာ ပို့ပေးပါ။")

bot.polling(none_stop=True)

import telebot
import re
import productRepository
import privateMessages
import groupMessages
import threading
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get BOT_TOKEN from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found! Make sure it's in the .env file")

bot = telebot.TeleBot(BOT_TOKEN)

# Group chat ID (message.chat.id)
GROUP_CHAT_ID = -4861053438

# === ADMINS ===
ADMIN_IDS = [1283838300]  # ضع ارقام الـ user_id الخاصة بالادمن هنا

# User states
user_states = {}
SHIPPING_FEE = 5.00


# === OFFERS SYSTEM ===
offers = [
    "🎉 عرض خاص اليوم: اشترِ المنتج أ الآن واحصل على خصم 10%! 🌟\nتفضل بزيارة موقعنا: https://yourstore.com",
    "🔥 لا تفوت الفرصة: المنتج ب مع توصيل مجاني عند الشراء الآن 🚚\nزر موقعنا: https://yourstore.com",
    "⭐ عروض حصرية: تسوق الآن واحصل على هدية مجانية 🎁\nالمزيد على موقعنا: https://yourstore.com",
    "💥 تخفيضات نهاية الأسبوع! وفر حتى 20% على جميع المنتجات 🛒\nتسوق من هنا: https://yourstore.com",
]
offer_index = 0


def send_offers() -> None:
    global offer_index
    try:
        bot.send_message(GROUP_CHAT_ID, offers[offer_index])
        offer_index = (offer_index + 1) % len(offers)
    except Exception as e:
        print(f"خطأ أثناء إرسال العرض: {e}")
    threading.Timer(10800, send_offers).start()  # كل 3 ساعات

# === HELPERS ===


def is_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))


# === BOT HANDLERS ===

# Admin command to list products


@bot.message_handler(commands=['list'])
def handle_list(message) -> None:
    privateMessages.listCommand(message, bot, ADMIN_IDS, productRepository)


@bot.message_handler(func=lambda message: True)
def handle_message(message) -> None:
    groupMessages.messageHandler(
        message, bot, ADMIN_IDS, productRepository, user_states, SHIPPING_FEE)


# === MAIN ===
if __name__ == '__main__':
    print("Bot is running...")
    productRepository.init_db()
    # productRepository.insert_sample_products()  # Uncomment only on first run
    # send_offers()
    bot.infinity_polling()

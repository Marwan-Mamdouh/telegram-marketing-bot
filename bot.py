import telebot
import re
import productRepository
import sessionRepository
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


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("buy_"):
        prod_id = int(data.split("_")[1])
        product = productRepository.get_product(prod_id)
        if product:
            bot.answer_callback_query(call.id, "تم اختيار المنتج ✅")
            bot.send_message(chat_id, f"👍 جاري بدء طلب {product[1]}")
            # put user in order state
            # sessionRepository.save_session(user_id, 'waiting_for_product', {})
            user_states[user_id] = {'state': 'waiting_for_quantity', 'data': {
                'product_id': product[0],
                'product_name': product[1],
                'price': product[3]
            }}
            bot.send_message(chat_id, "كم عدد الوحدات التي تريد (مثال: 1, 2)؟")

    elif data.startswith("similar_"):
        prod_id = int(data.split("_")[1])
        product = productRepository.get_product(prod_id)
        if product:
            query = product[1]  # search by product name
            related = productRepository.semantic_search(query)
            related = [p for p in related if p[0] != prod_id]  # exclude self
            if related:
                bot.answer_callback_query(call.id, "منتجات مشابهة 🎯")
                for rel in related[:3]:
                    groupMessages.send_product_with_buttons(
                        bot, chat_id, rel)
            else:
                bot.answer_callback_query(
                    call.id, "لا يوجد منتجات مشابهة حالياً")
    elif data.startswith("next_page_") or data.startswith("prev_page_"):
        parts = data.split("_")
        direction, page, query = parts[0], int(parts[2]), "_".join(parts[3:])

        # Re-run search for products
        products = productRepository.semantic_search(query)
        if not products:
            products = productRepository.search_products_by_name(query)

        if products:
            groupMessages.send_products_page(
                bot, chat_id, products, page=page, query=query)
        else:
            bot.send_message(chat_id, "❌ لم يتم العثور على منتجات.")


# === MAIN ===
if __name__ == '__main__':
    print("Bot is running...")
    productRepository.init_db()
    sessionRepository.init_session_db()
    # productRepository.insert_sample_products()  # Uncomment only on first run
    # send_offers()
    bot.infinity_polling()

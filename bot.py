import telebot
import re
import sqlite3
import threading

# Replace with your actual bot token
BOT_TOKEN = '8301310830:AAH8fzg8wBRAZATsxgsBIYIYTvBjy2opzMU'
bot = telebot.TeleBot(BOT_TOKEN)

# Group chat ID (replace this after checking with print(message.chat.id))
GROUP_CHAT_ID = -4861053438

# === ADMINS ===
ADMIN_IDS = [1283838300]  # ضع ارقام الـ user_id الخاصة بالادمن هنا

# User states
user_states = {}
SHIPPING_FEE = 5.00

# === DATABASE SETUP ===


def init_db() -> None:
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        link TEXT NOT NULL,
        stock INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

# Insert sample products (run once)


def insert_sample_products() -> None:
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    products = [
        ("المنتج أ", "هذا منتج رائع لتلبية جميع احتياجاتك.",
         19.99, "https://yourstore.com/productA", 15),
        ("المنتج ب", "المنتج ب يقدم جودة وقيمة ممتازة.",
         29.99, "https://yourstore.com/productB", 7),
    ]
    cursor.executemany(
        "INSERT INTO products (name, description, price, link, stock) VALUES (?, ?, ?, ?, ?)", products)
    conn.commit()
    conn.close()

# Fetch all products


def get_all_products() -> list:
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Fetch single product by id


def get_product(prod_id: str):
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, price, link FROM products WHERE id=?", (prod_id,))
    product = cursor.fetchone()
    conn.close()
    return product


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

# === DATABASE HELPERS ===

# Fetch single product by name (case-insensitive search)


def get_product_by_name(name: str):
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, price, link FROM products WHERE name LIKE ?", ('%' + name + '%',))
    product = cursor.fetchone()
    conn.close()
    return product


def list_products():
    rows = get_all_products()
    if not rows:
        return "لا توجد منتجات متاحة حالياً."
    product_list = "المنتجات المتاحة:\n"
    for row in rows:
        product_list += f"{row[0]}: {row[1]} - {row[2]}$)\n"
    return product_list

# === BOT HANDLERS ===

# Admin command to list products


@bot.message_handler(commands=['list'])
def handle_list(message) -> None:
    if message.from_user.id in ADMIN_IDS:
        products = get_all_products()
        if not products:
            bot.reply_to(message, "📦 لا توجد منتجات حالياً.")
        else:
            msg = "📋 قائمة المنتجات:\n"
            for p in products:
                msg += f"{p[0]}: {p[1]} - {p[2]}$)\n"
            bot.reply_to(message, msg)
    else:
        bot.reply_to(message, "❌ هذا الامر متاح للادمن فقط.")


@bot.message_handler(func=lambda message: True)
def handle_message(message) -> None:
    chat_type = message.chat.type
    user_id = message.from_user.id
    text = message.text.strip()

    # Normal user in private chat
    if chat_type == 'private' and user_id not in ADMIN_IDS:
        bot.reply_to(message, "اهلا بيك في متجرنا، تحب تتفرج علي منتجاتنا ؟")
        return

    # === PRODUCT INFO HANDLING ===
    if chat_type in ['group', 'supergroup']:
        # Case 1: search by product ID
        if text.isdigit():
            product = get_product(int(text))
            if product:
                response = f"معلومات عن {product[1]}:\n" \
                    f"الوصف: {product[2]}\n" \
                    f"السعر: {product[3]}$\n" \
                    f"رابط الشراء: {product[4]}"
                bot.reply_to(message, response)
                return

        # Case 2: search by product NAME
        else:
            product = get_product_by_name(text)
            if product:
                response = f"معلومات عن {product[1]}:\n" \
                    f"الوصف: {product[2]}\n" \
                    f"السعر: {product[3]}$\n" \
                    f"رابط الشراء: {product[4]}"
                bot.reply_to(message, response)
                return

    # Start order
    if 'طلب' in text or 'اطلب' in text:
        user_states[user_id] = {'state': 'waiting_for_product', 'data': {}}
        product_list = list_products()
        bot.reply_to(
            message, f"رائع! لنقم بعمل الطلب.\n{product_list}\nالرجاء إرسال رقم المنتج (مثال: 1).")
        return

    # Handle order steps
    if user_id in user_states:
        state = user_states[user_id]['state']
        data = user_states[user_id]['data']

        if state == 'waiting_for_product':
            if text.isdigit():
                product = get_product(int(text))
                if product:
                    data['product_id'] = product[0]
                    data['product_name'] = product[1]
                    data['price'] = product[3]
                    user_states[user_id]['state'] = 'waiting_for_quantity'
                    bot.reply_to(
                        message, "اختيار ممتاز! كم عدد الوحدات التي تريد (مثال: 1, 2)؟")
                else:
                    bot.reply_to(
                        message, "رقم المنتج غير صحيح. الرجاء إدخال رقم صالح.")
            else:
                bot.reply_to(message, "الرجاء إدخال رقم المنتج (مثال: 1).")
            return

        elif state == 'waiting_for_quantity':
            try:
                quantity = int(text)
                if quantity > 0:
                    data['quantity'] = quantity
                    user_states[user_id]['state'] = 'waiting_for_address'
                    bot.reply_to(message, "تم! ما هو عنوان الشحن الخاص بك؟")
                else:
                    raise ValueError
            except ValueError:
                bot.reply_to(
                    message, "الرجاء إدخال رقم صحيح للكمية (مثال: 1).")
            return

        elif state == 'waiting_for_address':
            data['address'] = message.text
            subtotal = data['price'] * data['quantity']
            total = subtotal + SHIPPING_FEE
            confirmation = f"ملخص الطلب:\n" \
                f"المنتج: {data['product_name']} (ID: {data['product_id']})\n" \
                f"الكمية: {data['quantity']}\n" \
                f"المجموع الفرعي: ${subtotal:.2f}\n" \
                f"رسوم الشحن: ${SHIPPING_FEE:.2f}\n" \
                f"الإجمالي: ${total:.2f}\n" \
                f"العنوان: {data['address']}\n" \
                f"شكراً لك! تم تسجيل طلبك."
            bot.reply_to(message, confirmation)
            del user_states[user_id]
            return


# === MAIN ===
if __name__ == '__main__':
    print("Bot is running...")
    init_db()
    # insert_sample_products()  # Uncomment only on first run
    send_offers()
    bot.infinity_polling()

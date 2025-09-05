from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sessionRepository


def messageHandler(message, bot, ADMIN_IDS: list[int], productRepository, SHIPPING_FEE: float) -> None:
    chat_type = message.chat.type
    user_id: int = message.from_user.id
    text: str = message.text.strip()

    # Normal user in private chat
    if chat_type == 'private' and user_id not in ADMIN_IDS:
        bot.reply_to(message, "اهلا بيك في متجرنا، تحب تتفرج علي منتجاتنا ؟")
        return

    # === PRODUCT INFO HANDLING ===
    if chat_type in ['group', 'supergroup']:
        # Case 1: search by product ID
        if text.isdigit():
            product = productRepository.get_product(int(text))
            if product:
                send_product_with_buttons(bot, message.chat.id, product)
                return
        else:
            # Case 2: semantic / fuzzy search
            products: list = productRepository.semantic_search(text)
            if not products:
                products = productRepository.search_products_by_name(text)

            if products:
                for product in products:
                    send_product_with_buttons(bot, message.chat.id, product)
                return

    # === START ORDER ===
    if 'طلب' in text or 'اطلب' in text:
        setOrder(user_id, productRepository, bot, message)
        # sessionRepository.save_session(user_id, 'waiting_for_product', {})
        # product_list = productRepository.list_products()
        # bot.reply_to(
        #     message, f"رائع! لنقم بعمل الطلب.\n{product_list}\nالرجاء إرسال رقم المنتج (مثال: 1).")
        # return

    # === HANDLE ORDER STEPS ===
    session = sessionRepository.get_session(user_id)
    if session:
        state = session['state']
        data = session['data']

        if state == 'waiting_for_product':
            if text.isdigit():
                product = productRepository.get_product(int(text))
                if product:
                    data['product_id'] = product[0]
                    data['product_name'] = product[1]
                    data['price'] = product[3]
                    sessionRepository.save_session(
                        user_id, 'waiting_for_quantity', data)
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
                    sessionRepository.save_session(
                        user_id, 'waiting_for_address', data)
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
            sessionRepository.delete_session(user_id)
            return

# ----------------------------------------------------------------------


def send_product_with_buttons(bot, chat_id, product):
    """
    Send product info with InlineKeyboard buttons
    """
    response: str = f"📦 {product[1]}\n" \
        f"الوصف: {product[2]}\n" \
        f"السعر: {product[3]}$"

    keyboard = InlineKeyboardMarkup()

    # Always add buy button
    keyboard.add(
        InlineKeyboardButton("🛒 شراء الآن", callback_data=f"buy_{product[0]}")
    )

    # Add product link button only if valid
    if product[4] and product[4].startswith("http") and len(product[4]) > len("https://"):
        keyboard.add(
            InlineKeyboardButton("🔗 رابط المنتج", url=product[4])
        )

    # Add similar products button
    keyboard.add(
        InlineKeyboardButton(
            "🎯 منتجات مشابهة", callback_data=f"similar_{product[0]}")
    )

    bot.send_message(chat_id, response, reply_markup=keyboard)


def send_products_page(bot, chat_id, products, page=0, page_size=5, query=""):
    """
    Send a paginated list of products with navigation buttons.
    """
    start = page * page_size
    end = start + page_size
    current_page_products = products[start:end]

    if not current_page_products:
        bot.send_message(chat_id, "❌ لا يوجد منتجات في هذه الصفحة")
        return

    # Send each product in the page
    for product in current_page_products:
        send_product_with_buttons(bot, chat_id, product)

    # Build navigation keyboard
    nav_keyboard = InlineKeyboardMarkup()
    buttons: list = []

    if page > 0:
        buttons.append(InlineKeyboardButton(
            "◀️ السابق", callback_data=f"prev_page_{page-1}_{query}"))
    if end < len(products):
        buttons.append(InlineKeyboardButton(
            "التالي ▶️", callback_data=f"next_page_{page+1}_{query}"))

    if buttons:
        nav_keyboard.row(*buttons)
        bot.send_message(
            chat_id,
            f"📄 صفحة {page+1} من {((len(products)-1)//page_size)+1}",
            reply_markup=nav_keyboard
        )


def setOrder(user_id, productRepository, bot, message):
    sessionRepository.save_session(user_id, 'waiting_for_product', {})
    product_list: list = productRepository.list_products()
    bot.reply_to(
        message, f"رائع! لنقم بعمل الطلب.\n{product_list}\nالرجاء إرسال رقم المنتج (مثال: 1).")
    return


def callBackHandler(call, productRepository, bot):
    user_id: int = call.from_user.id
    chat_id: int = call.message.chat.id
    data = call.data

    if data.startswith("buy_"):
        prod_id: int = int(data.split("_")[1])
        product = productRepository.get_product(prod_id)
        if product:
            bot.answer_callback_query(call.id, "تم اختيار المنتج ✅")

            # --- Save session for this user ---
            sessionRepository.save_session(user_id, 'waiting_for_quantity', {
                'product_id': product[0],
                'product_name': product[1],
                'price': product[3]
            })

            # Tell user in group to continue in private chat
            bot.send_message(
                chat_id,
                f"✅ تم اختيار {product[1]}\n"
                "الرجاء الانتقال إلى المحادثة الخاصة مع البوت لإكمال عملية الشراء 📨"
            )

            # Send a private message to the user (if allowed)
            try:
                bot.send_message(
                    user_id,
                    f"👋 أهلاً! لقد اخترت {product[1]}.\n"
                    "كم عدد الوحدات التي تريد (مثال: 1, 2)؟"
                )
            except Exception:
                bot.send_message(
                    chat_id,
                    "⚠️ الرجاء بدء محادثة خاصة مع البوت أولاً ثم أعد المحاولة."
                )

    elif data.startswith("similar_"):
        prod_id: int = int(data.split("_")[1])
        product = productRepository.get_product(prod_id)
        if product:
            query = product[1]  # search by product name
            related: list = productRepository.semantic_search(query)
            related: list = [p for p in related if p[0] != prod_id]  # exclude self
            if related:
                bot.answer_callback_query(call.id, "منتجات مشابهة 🎯")
                for rel in related[:3]:
                    send_product_with_buttons(bot, chat_id, rel)
            else:
                bot.answer_callback_query(
                    call.id, "لا يوجد منتجات مشابهة حالياً")

    elif data.startswith("next_page_") or data.startswith("prev_page_"):
        parts: str = data.split("_")
        direction, page, query = parts[0], int(parts[2]), "_".join(parts[3:])

        # Re-run search for products
        products: list = productRepository.semantic_search(query)
        if not products:
            products: list = productRepository.search_products_by_name(query)

        if products:
            send_products_page(bot, chat_id, products, page=page, query=query)
        else:
            bot.send_message(chat_id, "❌ لم يتم العثور على منتجات.")

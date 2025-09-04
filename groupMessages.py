from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def messageHandler(message, bot, ADMIN_IDS: list, productRepository, user_states: dict, SHIPPING_FEE: float) -> None:
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
            product = productRepository.get_product(int(text))
            if product:
                send_product_with_buttons(bot, message.chat.id, product)
                return

            # Case 2: fuzzy search by NAME (Arabic friendly, multiple matches)
            # Case 2: semantic search (NLP embeddings)
        else:
            products = productRepository.semantic_search(text)
            if not products:
                products = productRepository.search_products_by_name(text)

            if products:
                for product in products:
                    send_product_with_buttons(bot, message.chat.id, product)
                return

    # Start order
    if 'طلب' in text or 'اطلب' in text:
        user_states[user_id] = {'state': 'waiting_for_product', 'data': {}}
        product_list = productRepository.list_products()
        bot.reply_to(
            message, f"رائع! لنقم بعمل الطلب.\n{product_list}\nالرجاء إرسال رقم المنتج (مثال: 1).")
        return

    # Handle order steps
    if user_id in user_states:
        state = user_states[user_id]['state']
        data = user_states[user_id]['data']

        if state == 'waiting_for_product':
            if text.isdigit():
                product = productRepository.get_product(int(text))
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

# ----------------------------------------------------------------------


def send_product_with_buttons(bot, chat_id, product):
    """
    Send product info with InlineKeyboard buttons
    """
    response = f"📦 {product[1]}\n" \
        f"الوصف: {product[2]}\n" \
        f"السعر: {product[3]}$"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🛒 شراء الآن", callback_data=f"buy_{product[0]}"),
        InlineKeyboardButton("🔗 رابط المنتج", url=product[4])
    )
    keyboard.add(
        InlineKeyboardButton(
            "🎯 منتجات مشابهة", callback_data=f"similar_{product[0]}")
    )

    bot.send_message(chat_id, response, reply_markup=keyboard)

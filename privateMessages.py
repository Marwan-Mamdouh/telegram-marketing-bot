import sessionRepository


def listCommand(message, bot, ADMIN_IDS: list[int], productRepository) -> None:
    if message.from_user.id in ADMIN_IDS:
        products: list = productRepository.get_all_products()
        if not products:
            bot.reply_to(message, "📦 لا توجد منتجات حالياً.")
        else:
            msg: str = "📋 قائمة المنتجات:\n"
            for p in products:
                msg += f"{p[0]}: {p[1]} - {p[2]}$)\n"
            bot.reply_to(message, msg)
    else:
        bot.reply_to(message, "❌ هذا الامر متاح للادمن فقط.")


def privateMessageHandler(message, bot, ADMIN_IDS: list[int], productRepository, SHIPPING_FEE: float):
    user_id: int = message.from_user.id
    text: str = message.text.strip()

    # Ignore admins in private
    if user_id in ADMIN_IDS:
        bot.reply_to(message, "مرحباً أيها الأدمن 👑")
        return

    session = sessionRepository.get_session(user_id)
    if not session:
        bot.reply_to(
            message, "👋 أهلاً! يمكنك اختيار منتج من الجروب والعودة هنا لإكمال الطلب.")
        return

    state = session['state']
    data = session['data']

    if state == 'waiting_for_quantity':
        try:
            quantity = int(text)
            if quantity > 0:
                data['quantity'] = quantity
                sessionRepository.save_session(
                    user_id, 'waiting_for_address', data)
                bot.reply_to(
                    message, "✅ تم تسجيل الكمية!\nالرجاء إدخال عنوان الشحن الخاص بك 🏠")
            else:
                raise ValueError
        except ValueError:
            bot.reply_to(
                message, "⚠️ الرجاء إدخال رقم صحيح للكمية (مثال: 1، 2).")
        return

    elif state == 'waiting_for_address':
        data['address'] = text
        subtotal: float = data['price'] * data['quantity']
        total: float = subtotal + SHIPPING_FEE

        confirmation: str = f"📦 ملخص الطلب:\n" \
            f"المنتج: {data['product_name']} (ID: {data['product_id']})\n" \
            f"الكمية: {data['quantity']}\n" \
            f"المجموع الفرعي: ${subtotal:.2f}\n" \
            f"رسوم الشحن: ${SHIPPING_FEE:.2f}\n" \
            f"الإجمالي: ${total:.2f}\n" \
            f"📍 العنوان: {data['address']}\n\n" \
            f"✅ شكراً لك! تم تسجيل طلبك."

        bot.reply_to(message, confirmation)
        sessionRepository.delete_session(user_id)
        return

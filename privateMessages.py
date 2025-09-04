
# @bot.message_handler(commands=['list'])
def listCommand(message, bot, ADMIN_IDS, productRepository) -> None:
    if message.from_user.id in ADMIN_IDS:
        products = productRepository.get_all_products()
        if not products:
            bot.reply_to(message, "📦 لا توجد منتجات حالياً.")
        else:
            msg = "📋 قائمة المنتجات:\n"
            for p in products:
                msg += f"{p[0]}: {p[1]} - {p[2]}$)\n"
            bot.reply_to(message, msg)
    else:
        bot.reply_to(message, "❌ هذا الامر متاح للادمن فقط.")

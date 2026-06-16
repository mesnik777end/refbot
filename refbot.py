import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# ВСТАВЬТЕ ВАШ ТОКЕН ЗДЕСЬ
TOKEN = "8212812232:AAF5WazaAZyPFKCXz8o6plHBwlY_Z0H7zg0"

# База данных пользователей (в памяти, для простоты)
users_data = {}

class UserData:
    def __init__(self):
        self.balance = 0.0
        self.referrals = 0
        self.last_bonus = None
        self.referral_code = None

# Генерация реферального кода
def generate_referral_code(user_id):
    import hashlib
    code = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
    return code

# Кнопки главного меню
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("💰 Заработать", callback_data="earn")],
        [InlineKeyboardButton("💎 Вывести", callback_data="withdraw")],
        [InlineKeyboardButton("🎁 Бонус", callback_data="bonus")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Проверяем, есть ли реферальный код в ссылке
    if context.args:
        ref_code = context.args[0]
        # Находим пригласившего
        for uid, data in users_data.items():
            if data.referral_code == ref_code and uid != user_id:
                # Начисляем бонус пригласившему
                users_data[uid].balance += 2.0
                users_data[uid].referrals += 1
                
                # Уведомление пригласившему
                try:
                    await context.bot.send_message(
                        chat_id=uid,
                        text=f"🎉 Новый реферал!\n\n"
                             f"Пользователь @{user.username or user.first_name} перешел по вашей ссылке.\n"
                             f"Вам начислено +2 🌟\n"
                             f"Всего рефералов: {users_data[uid].referrals}"
                    )
                except:
                    pass
                break
    
    # Инициализация пользователя
    if user_id not in users_data:
        users_data[user_id] = UserData()
        users_data[user_id].referral_code = generate_referral_code(user_id)
        # Приветственный бонус
        users_data[user_id].balance = 0.25
    
    # Текст приветствия
    welcome_text = (
        f"🌟 Привет, {user.first_name}!\n\n"
        f"💰 Твой баланс: {users_data[user_id].balance:.2f} 🌟\n"
        f"👥 Приглашено тобой: {users_data[user_id].referrals}\n\n"
        f"Выбери действие:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

# Обработчик кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = users_data.get(user_id)
    
    if not user_data:
        await query.edit_message_text("❌ Пожалуйста, начните с /start")
        return
    
    if query.data == "earn":
        # Кнопка "Заработать"
        ref_link = f"t.me/{(await context.bot.get_me()).username}?start={user_data.referral_code}"
        
        earn_text = (
            f"🎁 Получай +2 🌟 за каждого приглашенного друга!\n\n"
            f"📌 Твоя реферальная ссылка:\n"
            f"`{ref_link}`\n\n"
            f"🔴 Приглашай по этой ссылке своих друзей, "
            f"отправляй её во все чаты и зарабатывай Звёзды!\n\n"
            f"👥 Приглашено тобой: {user_data.referrals}"
        )
        
        keyboard = [
            [InlineKeyboardButton("📤 Отправить Ссылку Друзьям", switch_inline_query=ref_link)],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]
        
        await query.edit_message_text(
            earn_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "withdraw":
        # Кнопка "Вывести"
        withdraw_text = (
            f"💎 Вывод Звёзд\n\n"
            f"💰 Заработано: {user_data.balance:.2f} 🌟\n\n"
            f"Выбери сумму для вывода:\n"
            f"📢 Канал с выводами: @StarsoVEarnOut"
        )
        
        keyboard = [
            [InlineKeyboardButton("15 🌟", callback_data="withdraw_15"),
             InlineKeyboardButton("25 🌟", callback_data="withdraw_25")],
            [InlineKeyboardButton("50 🌟", callback_data="withdraw_50"),
             InlineKeyboardButton("100 🌟", callback_data="withdraw_100")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]
        
        await query.edit_message_text(
            withdraw_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith("withdraw_"):
        # Обработка вывода
        amount = float(query.data.split("_")[1])
        
        if user_data.balance >= amount:
            user_data.balance -= amount
            await query.edit_message_text(
                f"✅ Заявка на вывод {amount} 🌟 отправлена!\n\n"
                f"Ожидайте обработки в течение 24 часов.\n"
                f"Остаток: {user_data.balance:.2f} 🌟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 В меню", callback_data="back")]
                ])
            )
            # Здесь можно добавить отправку заявки админу
        else:
            await query.edit_message_text(
                f"❌ Недостаточно средств!\n\n"
                f"Твой баланс: {user_data.balance:.2f} 🌟\n"
                f"Запрошено: {amount} 🌟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ])
            )
    
    elif query.data == "bonus":
        # Кнопка "Бонус"
        today = datetime.now().date()
        
        if user_data.last_bonus and user_data.last_bonus == today:
            await query.edit_message_text(
                f"⏳ Ты уже получал бонус сегодня!\n\n"
                f"Возвращайся завтра!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ])
            )
        else:
            user_data.balance += 1.0
            user_data.last_bonus = today
            
            await query.edit_message_text(
                f"🎁 Вам начислена 1 звезда как бонус!\n\n"
                f"💰 Твой баланс: {user_data.balance:.2f} 🌟\n\n"
                f"Приходи завтра снова!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 В меню", callback_data="back")]
                ])
            )
    
    elif query.data == "back":
        # Возврат в главное меню
        welcome_text = (
            f"🌟 Привет, {query.from_user.first_name}!\n\n"
            f"💰 Твой баланс: {user_data.balance:.2f} 🌟\n"
            f"👥 Приглашено тобой: {user_data.referrals}\n\n"
            f"Выбери действие:"
        )
        await query.edit_message_text(
            welcome_text,
            reply_markup=get_main_keyboard()
        )

# Команда /balance (проверка баланса)
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = users_data.get(user_id)
    
    if user_data:
        await update.message.reply_text(
            f"💰 Твой баланс: {user_data.balance:.2f} 🌟\n"
            f"👥 Рефералов: {user_data.referrals}"
        )
    else:
        await update.message.reply_text("❌ Начни с /start")

# Обработка неизвестных команд
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Неизвестная команда.\n"
        "Используй /start для начала"
    )

def main():
    # Проверяем, что токен не пустой
    if not TOKEN:
        print("❌ Ошибка: Токен не найден!")
        return
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    print("🌟 Бот StarsoVEarn запущен и работает 24/7!")
    app.run_polling()

if __name__ == "__main__":
    main()
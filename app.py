import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8721036900:AAEwk-tRJvgP0NVtsg3U3GOg1_3shj5nTB8"
ADMIN_ID = 7604556074  # Ваш Telegram ID для получения уведомлений

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class SupportStates(StatesGroup):
    waiting_for_topic = State()

def get_next_ticket_number():
    file_path = "tickets.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("0")
    
    with open(file_path, "r", encoding="utf-8") as f:
        current_number = int(f.read().strip())
    
    next_number = current_number + 1
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(next_number))
        
    return next_number

START_TEXT = (
    "<tg-emoji emoji-id=\"6028315147754278596\">🙂</tg-emoji> Добро пожаловать в Morgodon Shop\n\n"
    "Для покупки товаров используйте кнопки ниже <tg-emoji emoji-id=\"6039802767931871481\">⬇️</tg-emoji>"
)

def get_buttons():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Магазин\u200b", callback_data="shop", icon_custom_emoji_id="5920332557466997677")],
        [InlineKeyboardButton(text="Профиль\u200b", callback_data="profile", icon_custom_emoji_id="6035084557378654059")],
        [InlineKeyboardButton(text="Поддержка\u200b", callback_data="support", icon_custom_emoji_id="6039422865189638057")],
        [InlineKeyboardButton(text="Правила\u200b", callback_data="rules", icon_custom_emoji_id="6028435952299413210")]
    ])
    return keyboard

def get_main_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главная\u200b", callback_data="main", icon_custom_emoji_id="5938537205847822613")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(START_TEXT, reply_markup=get_buttons(), parse_mode="HTML")

# --- ОБРАБОТЧИКИ НАЖАТИЙ НА КНОПКИ ---

@dp.callback_query(lambda c: c.data == 'shop')
async def process_shop(callback_query: types.CallbackQuery):
    await callback_query.answer()
    text = "<tg-emoji emoji-id=\"5920332557466997677\">🏪</tg-emoji> Вы перешли в Магазин. Выберите товар:"
    await callback_query.message.edit_text(text, reply_markup=get_main_button(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'profile')
async def process_profile(callback_query: types.CallbackQuery):
    await callback_query.answer()
    text = "<tg-emoji emoji-id=\"6035084557378654059\">👤</tg-emoji> Это ваш Профиль. Ваш баланс: 0 руб."
    await callback_query.message.edit_text(text, reply_markup=get_main_button(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'rules')
async def process_rules(callback_query: types.CallbackQuery):
    await callback_query.answer()
    text = (
        "<tg-emoji emoji-id=\"6032636795387121097\">🛡</tg-emoji> Перед использованием бота, пожалуйста прочтите правила указанные ниже <tg-emoji emoji-id=\"5963087934696459905\">⬇️</tg-emoji>\n\n"
        "<tg-emoji emoji-id=\"6039630677182254664\">📂</tg-emoji> <a href=\"https://telegra.ph\">Пользовательское соглашение</a>\n"
        "<tg-emoji emoji-id=\"6039630677182254664\">📂</tg-emoji> <a href=\"https://telegra.ph\">Политика конфиденциальности</a>"
    )
    await callback_query.message.edit_text(
        text, 
        reply_markup=get_main_button(), 
        parse_mode="HTML",
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

@dp.callback_query(lambda c: c.data == 'support')
async def process_support(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    text = (
        "<tg-emoji emoji-id=\"6021418126061605425\">📞</tg-emoji> <b>Техническая поддержка</b>\n\n"
        "<tg-emoji emoji-id=\"6039450962865688331\">📝</tg-emoji> Введите <b>тему вашего обращения</b>"
    )
    await callback_query.message.edit_text(text, reply_markup=None, parse_mode="HTML")
    await state.set_state(SupportStates.waiting_for_topic)

# --- ПРИЕМ ТЕКСТА И ОТПРАВКА АДМИНУ ---
@dp.message(SupportStates.waiting_for_topic)
async def ticket_topic_received(message: types.Message, state: FSMContext):
    ticket_id = get_next_ticket_number()
    
    # Данные отправителя для формирования красивых ссылок
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"
    user_fullname = message.from_user.full_name
    
    # 1. Текст, который увидит пользователь в боте
    user_text = (
        "<tg-emoji emoji-id=\"6039450962865688331\">📝</tg-emoji> Ваше сообщение было <b>отправлено в поддержку</b>, ожидайте <b>ответа</b>\n"
        f"<tg-emoji emoji-id=\"5870998024779468554\">🔢</tg-emoji> Номер вашей заявки: <code>#{ticket_id}</code>"
    )
    await message.answer(user_text, reply_markup=get_main_button(), parse_mode="HTML")
    
    # 2. Формируем сообщение-уведомление для ВАС (администратора)
    admin_text = (
        f"🚨 <b>Новое обращение в поддержку! Tiket #{ticket_id}</b>\n\n"
        f"👤 <b>Пользователь:</b> {user_fullname}\n"
        f"🔗 <b>Юзернейм:</b> {username}\n"
        f"🆔 <b>ID аккаунта:</b> <a href='tg://user?id={user_id}'>{user_id}</a>\n\n"
        f"💬 <b>Текст обращения:</b>\n<i>{message.text}</i>"
    )
    
    # Отправляем уведомление вам в ЛС (чтобы сработало, вы должны быть один раз запущены в этом боте через /start)
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
    except Exception as e:
        print(f"Не удалось отправить уведомление админу: {e}")
        
    await state.clear()

@dp.callback_query(lambda c: c.data == 'main')
async def process_main(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.clear()
    await callback_query.message.edit_text(START_TEXT, reply_markup=get_buttons(), parse_mode="HTML")

# -------------------------------------

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    async def main_runner():
        await bot.delete_webhook(drop_pending_updates=True)
        await main()
    asyncio.run(main_runner())
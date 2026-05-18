import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8721036900:AAEwk-tRJvgP0NVtsg3U3GOg1_3shj5nTB8"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ОПРЕДЕЛЕНИЕ СОСТОЯНИЙ (FSM) ---
class SupportStates(StatesGroup):
    waiting_for_topic = State()  # Ожидание ввода темы от пользователя

# --- ФУНКЦИЯ ДЛЯ РАБОТЫ С ФАЙЛОМ ТИКЕТОВ ---
def get_next_ticket_number():
    file_path = "tickets.txt"
    # Если файла нет, создаем его со значением 0
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("0")
    
    # Читаем текущий номер
    with open(file_path, "r", encoding="utf-8") as f:
        current_number = int(f.read().strip())
    
    # Увеличиваем на 1
    next_number = current_number + 1
    
    # Сохраняем новый номер обратно в файл
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(next_number))
        
    return next_number

# --- КЛАВИАТУРЫ ---
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
    await state.clear()  # Сбрасываем состояния, если пользователь ввел /start заново
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

# --- ИЗМЕНЕННАЯ КНОПКА ПОДДЕРЖКИ ---
@dp.callback_query(lambda c: c.data == 'support')
async def process_support(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    text = (
        "<tg-emoji emoji-id=\"6021418126061605425\">📞</tg-emoji> <b>Техническая поддержка</b>\n\n"
        "<tg-emoji emoji-id=\"6039450962865688331\">📝</tg-emoji> Введите <b>тему вашего обращения</b>"
    )
    
    # Изменяем текст сообщения (кнопки убираем, передавая reply_markup=None)
    await callback_query.message.edit_text(text, reply_markup=None, parse_mode="HTML")
    
    # Включаем режим ожидания сообщения от пользователя
    await state.set_state(SupportStates.waiting_for_topic)

# --- ОБРАБОТЧИК ДЛЯ ПРИЕМА ТЕКСТА ТЕМЫ ---
@dp.message(SupportStates.waiting_for_topic)
async def ticket_topic_received(message: types.Message, state: FSMContext):
    # Получаем следующий номер тикета из файла
    ticket_id = get_next_ticket_number()
    
    # Текст сообщения об успешной отправке
    text = (
        "<tg-emoji emoji-id=\"6039450962865688331\">📝</tg-emoji> Ваше сообщение было <b>отправлено в поддержку</b>, ожидайте <b>ответа</b>\n"
        f"<tg-emoji emoji-id=\"5870998024779468554\">🔢</tg-emoji> Номер вашей заявки: <code>#{ticket_id}</code>"
    )
    
    # Отправляем ответное сообщение с кнопкой "Главная"
    await message.answer(text, reply_markup=get_main_button(), parse_mode="HTML")
    
    # Сбрасываем состояние FSM, чтобы бот снова реагировал на обычные команды
    await state.clear()

# --- КНОПКА ГЛАВНАЯ ---
@dp.callback_query(lambda c: c.data == 'main')
async def process_main(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.clear()  # На всякий случай сбрасываем FSM при выходе на главную
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
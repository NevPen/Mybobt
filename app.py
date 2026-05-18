import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8721036900:AAEwk-tRJvgP0NVtsg3U3GOg1_3shj5nTB8"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_buttons():
    # Передаем ID премиум-эмодзи в параметр icon_custom_emoji_id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Магазин", 
            callback_data="shop", 
            icon_custom_emoji_id="5920332557466997677"
        )],
        [InlineKeyboardButton(
            text="Профиль", 
            callback_data="profile", 
            icon_custom_emoji_id="6035084557378654059"
        )],
        [InlineKeyboardButton(
            text="Поддержка", 
            callback_data="support", 
            icon_custom_emoji_id="6039422865189638057"
        )],
        [InlineKeyboardButton(
            text="Правила", 
            callback_data="rules", 
            icon_custom_emoji_id="6028435952299413210"
        )]
    ])
    return keyboard

@dp.message(Command("start"))
async def start(message: types.Message):
    # Текст сообщения
    text = (
        "<tg-emoji emoji-id=\"6028315147754278596\">🙂</tg-emoji> Добро пожаловать в Morgodon Shop\n"
        "Для покупки товаров используйте кнопки ниже <tg-emoji emoji-id=\"6039802767931871481\">⬇️</tg-emoji>"
    )
    await message.answer(text, reply_markup=get_buttons(), parse_mode="HTML")

# --- ОБРАБОТЧИКИ НАЖАТИЙ НА КНОПКИ ---

@dp.callback_query(lambda c: c.data == 'shop')
async def process_shop(callback_query: types.CallbackQuery):
    await callback_query.answer()
    text = "<tg-emoji emoji-id=\"5920332557466997677\">🏪</tg-emoji> Вы перешли в Магазин. Выберите товар:"
    await callback_query.message.answer(text, parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'profile')
async def process_profile(callback_query: types.CallbackQuery):
    await callback_query.answer()
    text = "<tg-emoji emoji-id=\"6035084557378654059\">👤</tg-emoji> Это ваш Профиль. Ваш баланс: 0 руб."
    await callback_query.message.answer(text, parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'support')
async def process_support(callback_query: types.CallbackQuery):
    await callback_query.answer()
    text = "<tg-emoji emoji-id=\"6039422865189638057\">📣</tg-emoji> Связь с Поддержкой: @admin_username"
    await callback_query.message.answer(text, parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'rules')
async def process_rules(callback_query: types.CallbackQuery):
    await callback_query.answer()
    text = "<tg-emoji emoji-id=\"6028435952299413210\">ℹ️</tg-emoji> Правила магазина: будьте вежливы."
    await callback_query.message.answer(text, parse_mode="HTML")

# -------------------------------------

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    async def main_runner():
        await bot.delete_webhook(drop_pending_updates=True)
        await main()
    asyncio.run(main_runner())
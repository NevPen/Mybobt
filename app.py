import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8721036900:AAEwk-tRJvgP0NVtsg3U3GOg1_3shj5nTB8"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_buttons():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="Правила", callback_data="rules")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start(message: types.Message):
    text = """Добро пожаловать в Morgodon Shop

Для покупки товаров используйте кнопки ниже"""
    await message.answer(text, reply_markup=get_buttons())

# Кнопки есть, но они не работают (ничего не делают)
# Никаких обработчиков для callback_data нет

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
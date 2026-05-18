import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8721036900:AAEwk-tRJvgP0NVtsg3U3GOg1_3shj5nTB8"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_buttons():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f3ea Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="\U0001f464 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="\U0001f4e3 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="\u2139\ufe0f Правила", callback_data="rules")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start(message: types.Message):
    text = """\U0001f642 Добро пожаловать в Morgodon Shop

Для покупки товаров используйте кнопки ниже \u2b07\ufe0f"""
    await message.answer(text, reply_markup=get_buttons())

async def main():
    print("Бот запущен с кастомными эмодзи")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
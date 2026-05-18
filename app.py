import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ЗАМЕНИ НА СВОЙ ТОКЕН
BOT_TOKEN = "8140555522:AAHxFNC8k1DmIvBRak-6JCrUkdebtIJHmlY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Кнопки как на экране
def get_buttons():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Магазин")],
            [KeyboardButton(text="Профиль")],
            [KeyboardButton(text="Поддержка")],
            [KeyboardButton(text="Правила")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Нажимаем кнопку старт → появляется текст
@dp.message(Command("start"))
async def start(message: types.Message):
    text = """Добро пожаловать в Morgodon Shop

Для покупки товаров используйте кнопки ниже"""
    await message.answer(text, reply_markup=get_buttons())

# Заглушки для кнопок (чтобы бот реагировал)
@dp.message(lambda m: m.text == "Магазин")
async def shop(message: types.Message):
    await message.answer("Товары скоро появятся")

@dp.message(lambda m: m.text == "Профиль")
async def profile(message: types.Message):
    await message.answer("Ваш профиль")

@dp.message(lambda m: m.text == "Поддержка")
async def support(message: types.Message):
    await message.answer("Связь с поддержкой")

@dp.message(lambda m: m.text == "Правила")
async def rules(message: types.Message):
    await message.answer("Правила магазина")

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
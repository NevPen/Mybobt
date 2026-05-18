import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8721036900:AAEwk-tRJvgP0NVtsg3U3GOg1_3shj5nTB8"
ADMIN_ID = 7604556074  # Ваш Telegram ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Множество для временного хранения заблокированных пользователей
banned_users = set()

# --- СОСТОЯНИЯ (FSM) ---
class SupportStates(StatesGroup):
    waiting_for_topic = State()       
    waiting_for_admin_reply = State() 

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С НОМЕРАМИ ЗАЯВОК ---
def get_current_ticket_number():
    file_path = "tickets.txt"
    if not os.path.exists(file_path):
        return 0
    with open(file_path, "r", encoding="utf-8") as f:
        return int(f.read().strip())

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

# --- ТЕКСТА И КЛАВИАТУРЫ ---
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

def get_admin_inline_buttons(user_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Заблокировать\u200b", callback_data=f"ban_{user_id}", icon_custom_emoji_id="5935757052042285202"),
            InlineKeyboardButton(text="Ответить\u200b", callback_data=f"reply_{user_id}", icon_custom_emoji_id="6028346797368283073")
        ]
    ])
    return keyboard

# --- ГЛОБАЛЬНАЯ ПРОВЕРКА НА БАН ---
@dp.message(lambda message: message.from_user.id in banned_users)
@dp.callback_query(lambda callback: callback.from_user.id in banned_users)
async def process_banned(event):
    if isinstance(event, types.Message):
        await event.answer("Вы заблокированы в техподдержке магазина.")
    elif isinstance(event, types.CallbackQuery):
        await event.answer("Вы заблокированы администрацией.", show_alert=True)

# --- КОМАНДА /START ---
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(START_TEXT, reply_markup=get_buttons(), parse_mode="HTML")

# --- ОБРАБОТЧИКИ НАЖАТИЙ НА КНОПКИ ПОЛЬЗОВАТЕЛЕМ ---

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

# --- ПРИЕМ ТЕКСТА ОБРАЩЕНИЯ ОТ ПОЛЬЗОВАТЕЛЯ ---
@dp.message(SupportStates.waiting_for_topic)
async def ticket_topic_received(message: types.Message, state: FSMContext):
    ticket_id = get_next_ticket_number()
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"
    user_fullname = message.from_user.full_name
    
    user_text = (
        "<tg-emoji emoji-id=\"6039450962865688331\">📝</tg-emoji> Ваше сообщение было <b>отправлено в поддержку</b>, ожидайте <b>ответа</b>\n"
        f"<tg-emoji emoji-id=\"5870998024779468554\">🔢</tg-emoji> Номер вашей заявки: <code>#{ticket_id}</code>"
    )
    await message.answer(user_text, reply_markup=get_main_button(), parse_mode="HTML")
    
    admin_text = (
        f"<tg-emoji emoji-id=\"6039614175917903752\">✏️</tg-emoji> <b>Новое обращение в поддержку! Tiket #{ticket_id}</b>\n\n"
        f"<tg-emoji emoji-id=\"6035084557378654059\">👤</tg-emoji><b>Пользователь:</b> {user_fullname}\n"
        f"<tg-emoji emoji-id=\"5769289093221454192\">🔗</tg-emoji><b>Юзернейм:</b> {username}\n"
        f"<tg-emoji emoji-id=\"5884366771913233289\">🆔</tg-emoji> <b>ID аккаунта:</b> {user_id}\n\n"
        f"<tg-emoji emoji-id=\"6030833407339008632\">💬</tg-emoji> <b>Текст обращения:</b>\n"
        f"<i>{message.text}</i>"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=get_admin_inline_buttons(user_id), parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка уведомления админа: {e}")
        
    await state.clear()

@dp.callback_query(lambda c: c.data == 'main')
async def process_main(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.clear()
    await callback_query.message.edit_text(START_TEXT, reply_markup=get_buttons(), parse_mode="HTML")

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ДЛЯ АДМИНИСТРАТОРА ---

@dp.callback_query(lambda c: c.data.startswith('ban_'))
async def admin_ban_user(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        return await callback_query.answer("Доступ запрещен.")
    
    target_user_id = int(callback_query.data.split('_')[1])
    banned_users.add(target_user_id)
    
    await callback_query.answer("Пользователь заблокирован!", show_alert=True)
    await callback_query.message.reply(f"❌ Пользователь <code>{target_user_id}</code> успешно внесён в чёрный список.", parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith('reply_'))
async def admin_reply_start(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        return await callback_query.answer("Доступ запрещен.")
    
    target_user_id = int(callback_query.data.split('_')[1])
    
    await state.update_data(reply_to_user_id=target_user_id)
    await state.set_state(SupportStates.waiting_for_admin_reply)
    
    await callback_query.answer()
    await callback_query.message.reply("✍️ Напишите ответное сообщение для пользователя:")

# --- ОТПРАВКА ОТВЕТА ПОЛЬЗОВАТЕЛЮ ---
@dp.message(SupportStates.waiting_for_admin_reply)
async def admin_send_reply_message(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    target_user_id = data.get("reply_to_user_id")
    ticket_id = get_current_ticket_number()
    
    reply_text = (
        f"<tg-emoji emoji-id=\"6021418126061605425\">📞</tg-emoji> Ваш тикет <b>#{ticket_id}</b> был <b>обработан</b>\n"
        f"<tg-emoji emoji-id=\"5771851822897566479\">📝</tg-emoji> Ответ: {message.text}\n"
        f"<tg-emoji emoji-id=\"6021681257232994766\">🔒</tg-emoji> Ваш тикет был <b>автоматически закрыт</b>"
    )
    
    try:
        await bot.send_message(chat_id=target_user_id, text=reply_text, reply_markup=get_main_button(), parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки! Пользователь мог заблокировать бота: {e}")
        
    await state.clear()

# --- СТАРТ БОТА ---
async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    async def main_runner():
        await bot.delete_webhook(drop_pending_updates=True)
        await main()
    asyncio.run(main_runner())
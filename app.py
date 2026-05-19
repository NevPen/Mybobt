import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Токен вашего бота
BOT_TOKEN = "8690556428:AAHV7WiJMeGKvmsOGYdNodK1BQZcf4S4aJA"
ADMIN_ID = 7604556074  # Ваш Telegram ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище блокировок в памяти
banned_users = {}
ticket_counter = 0

# --- РАБОТА С БАЗОЙ ДАННЫХ ТОВАРОВ (JSON) ---
DATA_FILE = "shop_data.json"

def load_shop_data():
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "lebro_vip": {
                "1_day": {"price": "0", "vip_link": "", "keys": []},
                "7_days": {"price": "0", "vip_link": "", "keys": []},
                "30_days": {"price": "0", "vip_link": "", "keys": []},
                "forever": {"price": "0", "vip_link": "", "keys": []}
            },
            "lebro_lite": {
                "1_day": {"price": "0", "vip_link": "", "keys": []},
                "7_days": {"price": "0", "vip_link": "", "keys": []}
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)
        return initial_data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_shop_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- СОСТОЯНИЯ (FSM) ---
class SupportStates(StatesGroup):
    waiting_for_topic = State()        
    waiting_for_admin_reply = State()  
    waiting_for_ban_reason = State()   

class AdminStates(StatesGroup):
    waiting_for_price = State()     
    waiting_for_vip_link = State()  
    waiting_for_key = State()       

# --- ТЕКСТА И КЛАВИАТУРЫ ---
START_TEXT = (
    "<tg-emoji emoji-id=\"6028315147754278596\">🙂</tg-emoji> Добро пожаловать в Morgodon Shop\n\n"
    "Для покупки товаров используйте кнопки ниже <tg-emoji emoji-id=\"6039802767931871481\">⬇️</tg-emoji>"
)

def get_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Магазин\u200b", callback_data="shop", icon_custom_emoji_id="5920332557466997677")],
        [InlineKeyboardButton(text="Профиль\u200b", callback_data="profile", icon_custom_emoji_id="6035084557378654059")],
        [InlineKeyboardButton(text="Поддержка\u200b", callback_data="support", icon_custom_emoji_id="6039422865189638057")],
        [InlineKeyboardButton(text="Правила\u200b", callback_data="rules", icon_custom_emoji_id="6028435952299413210")]
    ])

def get_main_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главная\u200b", callback_data="main", icon_custom_emoji_id="5938537205847822613")]
    ])

def get_shop_categories():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Lebro Cheat\u200b", callback_data="prod_lebro", icon_custom_emoji_id="5886285355279193209")],
        [InlineKeyboardButton(text="Главная\u200b", callback_data="main", icon_custom_emoji_id="5938537205847822613")]
    ])

def get_lebro_versions():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Lite\u200b", callback_data="ver_lebro_lite", icon_custom_emoji_id="5893057118545646106"),
            InlineKeyboardButton(text="Vip\u200b", callback_data="ver_lebro_vip", icon_custom_emoji_id="5893236738372932548")
        ],
        [InlineKeyboardButton(text="Главная\u200b", callback_data="main", icon_custom_emoji_id="5938537205847822613")]
    ])

def get_user_periods_keyboard(version_type):
    current_data = load_shop_data()
    version_items = current_data.get(version_type, {})
    keyboard_structure = []
    
    labels = {
        "1_day": "1 день",
        "7_days": "7 дней",
        "30_days": "30 дней",
        "forever": "Навсегда"
    }
    
    for period, item_data in version_items.items():
        keys_list = item_data.get("keys", [])
        count = len(keys_list)
        
        if count > 0:  
            button_text = f"{labels[period]}\u200b"
            keyboard_structure.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"buy_{version_type}_{period}",
                icon_custom_emoji_id="5836907383292436018"
            )])
            
    keyboard_structure.append([InlineKeyboardButton(text="Главная\u200b", callback_data="main", icon_custom_emoji_id="5938537205847822613")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_structure)

def get_payment_keyboard(version_type, period):
    # Добавил кнопку "Перевод на карту" (dummy_card) и кнопку связи с @morgodon
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить (написать @morgodon)", url="https://t.me/morgodon")],
        [InlineKeyboardButton(text="Перевод на карту\u200b", callback_data="dummy_card", icon_custom_emoji_id="5841094056251230188")],
        [InlineKeyboardButton(text="Главная\u200b", callback_data="main", icon_custom_emoji_id="5938537205847822613")]
    ])

# КЛАВИАТУРЫ АДМИН-ПАНЕЛИ
def get_admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Vip\u200b", callback_data="adm_choose_vip", icon_custom_emoji_id="5893236738372932548")],
        [InlineKeyboardButton(text="Lite\u200b", callback_data="adm_choose_lite", icon_custom_emoji_id="5893057118545646106")]
    ])

def get_admin_periods_keyboard(version):
    if version == "vip":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 день\u200b", callback_data="add_vip_1d", icon_custom_emoji_id="5836907383292436018")],
            [InlineKeyboardButton(text="7 дней\u200b", callback_data="add_vip_7d", icon_custom_emoji_id="5836907383292436018")],
            [InlineKeyboardButton(text="30 дней\u200b", callback_data="add_vip_30d", icon_custom_emoji_id="5836907383292436018")],
            [InlineKeyboardButton(text="Навсегда\u200b", callback_data="add_vip_forever", icon_custom_emoji_id="5836907383292436018")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 день\u200b", callback_data="add_lite_1d", icon_custom_emoji_id="5836907383292436018")],
            [InlineKeyboardButton(text="7 дней\u200b", callback_data="add_lite_7d", icon_custom_emoji_id="5836907383292436018")]
        ])

def get_admin_inline_buttons(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Заблокировать\u200b", callback_data=f"ban_{user_id}", icon_custom_emoji_id="5935757052042285202"),
            InlineKeyboardButton(text="Ответить\u200b", callback_data=f"reply_{user_id}", icon_custom_emoji_id="6028346797368283073")
        ]
    ])

# --- ПРОВЕРКА НА БАН ---
@dp.message(lambda message: message.from_user.id in banned_users)
@dp.callback_query(lambda callback: callback.from_user.id in banned_users)
async def process_banned(event):
    user_id = event.from_user.id
    reason = banned_users.get(user_id, "Не указана")
    text_ban = (
        "<tg-emoji emoji-id=\"6030563507299160824\">❗️</tg-emoji>Вы заблокированы администратором<tg-emoji emoji-id=\"6030563507299160824\">❗️</tg-emoji>\n"
        f"<tg-emoji emoji-id=\"6039422865189638057\">📣</tg-emoji>Причина: {reason}"
    )
    if isinstance(event, types.Message):
        await event.answer(text_ban, parse_mode="HTML")
    elif isinstance(event, types.CallbackQuery):
        await event.answer("Доступ ограничен.", show_alert=True)

# --- АДМИН-КОМАНДА /BOOM ---
@dp.message(Command("boom"))
async def admin_panel_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.clear()
    await message.answer("Добавить версии lebro", reply_markup=get_admin_main_keyboard())

# --- КОМАНДА /START ---
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(START_TEXT, reply_markup=get_buttons(), parse_mode="HTML")

# --- ЛОГИКА ВЗАИМОДЕЙСТВИЯ С МАГАЗИНОМ ---

@dp.callback_query(lambda c: c.data == 'shop')
async def process_shop(callback_query: types.CallbackQuery):
    await callback_query.answer()  
    try:
        await callback_query.message.delete()
    except:
        pass
    text = "<tg-emoji emoji-id=\"5870563425628721113\">🛍</tg-emoji> <b>Выберите нужный товар</b>"
    await callback_query.message.answer(text, reply_markup=get_shop_categories(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'prod_lebro')
async def process_lebro_cheat(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    text = "<b>Выберите версию Lebro Cheat</b>"
    await callback_query.message.answer(text, reply_markup=get_lebro_versions(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data in ['ver_lebro_lite', 'ver_lebro_vip'])
async def user_select_version(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    version_type = "lebro_lite" if callback_query.data == "ver_lebro_lite" else "lebro_vip"
    
    current_data = load_shop_data()
    version_dict = current_data.get(version_type, {})
    has_items = any(len(item_data.get("keys", [])) > 0 for item_data in version_dict.values())
    
    if not has_items:
        text = "<tg-emoji emoji-id=\"5920046907782074235\">📝</tg-emoji>Нет в наличии"
        await callback_query.message.answer(text, reply_markup=get_main_button(), parse_mode="HTML")
    else:
        text = "<b>Выберите период подписки:</b>"
        await callback_query.message.answer(text, reply_markup=get_user_periods_keyboard(version_type), parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith('buy_'))
async def user_view_product_details(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    
    data_str = callback_query.data.replace("buy_", "")
    if data_str.startswith("lebro_vip_"):
        version_type = "lebro_vip"
        period = data_str.replace("lebro_vip_", "")
    else:
        version_type = "lebro_lite"
        period = data_str.replace("lebro_lite_", "")
        
    current_data = load_shop_data()
    item_data = current_data.get(version_type, {}).get(period, {})
    
    keys_list = item_data.get("keys", [])
    price = item_data.get("price", "0")
    count = len(keys_list)
    
    labels_ver = {"lebro_vip": "Vip", "lebro_lite": "Lite"}
    labels_per = {"1_day": "1D", "7_days": "7D", "30_days": "30D", "forever": "Навсегда"}
    
    text_details = (
        f"Выбран товар - Lebro Cheat ({labels_ver.get(version_type)} {labels_per.get(period)})\n\n"
        f"Товара в наличии - {count}\n"
        f"Цена - {price} руб.\n\n"
        "Для оплаты воспользуйтесь кнопками ниже"
    )
    
    await callback_query.message.answer(text_details, reply_markup=get_payment_keyboard(version_type, period), parse_mode="HTML")

# Заглушка для кнопки "Перевод на карту"
@dp.callback_query(lambda c: c.data == 'dummy_card')
async def process_dummy_card(callback_query: types.CallbackQuery):
    # Показываем всплывающее окно
    await callback_query.answer("Оплата картой временно недоступна, для покупки напишите @morgodon", show_alert=True)

# --- СИСТЕМА ДОБАВЛЕНИЯ ТОВАРОВ АДМИНИСТРАТОРА ---

@dp.callback_query(lambda c: c.data in ['adm_choose_vip', 'adm_choose_lite'])
async def admin_select_version(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID: return
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    version = "vip" if callback_query.data == "adm_choose_vip" else "lite"
    await callback_query.message.answer(f"Выберите период для настройки версии {version.upper()}:", reply_markup=get_admin_periods_keyboard(version))

# Карта сопоставления инлайн-кнопок админки с базой JSON
ADMIN_CALLBACK_MAP = {
    "add_vip_1d": ("lebro_vip", "1_day"),
    "add_vip_7d": ("lebro_vip", "7_days"),
    "add_vip_30d": ("lebro_vip", "30_days"),
    "add_vip_forever": ("lebro_vip", "forever"),
    "add_lite_1d": ("lebro_lite", "1_day"),
    "add_lite_7d": ("lebro_lite", "7_days")
}

@dp.callback_query(lambda c: c.data in ADMIN_CALLBACK_MAP.keys())
async def admin_select_period(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID: return
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    
    version_type, period = ADMIN_CALLBACK_MAP[callback_query.data]
    await state.update_data(target_version=version_type, target_period=period)
    await state.set_state(AdminStates.waiting_for_price)
    
    await callback_query.message.answer("Введите цену товара:")

@dp.message(AdminStates.waiting_for_price)
async def admin_price_received(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.update_data(item_price=message.text)
    
    await state.set_state(AdminStates.waiting_for_vip_link)
    await message.reply("ссылка вип канал:")

@dp.message(AdminStates.waiting_for_vip_link)
async def admin_vip_link_received(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.update_data(item_vip_link=message.text)
    
    await state.set_state(AdminStates.waiting_for_key)
    await message.reply("напишите ключ:")

@dp.message(AdminStates.waiting_for_key)
async def admin_key_received(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    
    state_data = await state.get_data()
    version_type = state_data.get("target_version")
    period = state_data.get("target_period")
    price = state_data.get("item_price")
    vip_link = state_data.get("item_vip_link")
    
    current_data = load_shop_data()
    
    if version_type in current_data and period in current_data[version_type]:
        current_data[version_type][period]["price"] = price
        current_data[version_type][period]["vip_link"] = vip_link
        current_data[version_type][period]["keys"].append(message.text)
        save_shop_data(current_data)
        await message.answer("товар в магазине")
    else:
        await message.answer("❌ Произошла ошибка внутренней структуры категорий.")
        
    await state.clear()

# --- РАЗДЕЛ ПРОФИЛЬ ---

@dp.callback_query(lambda c: c.data == 'profile')
async def process_profile(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    
    user_id = callback_query.from_user.id
    username = f"@{callback_query.from_user.username}" if callback_query.from_user.username else "Нет"
    
    text = (
        "<tg-emoji emoji-id=\"6035084557378654059\">👤</tg-emoji> <b>Ваш профиль:</b>\n"
        f"<tg-emoji emoji-id=\"5884366771913233289\">🆔</tg-emoji> <b>ID аккаунта:</b> <code>{user_id}</code>\n"
        f"<tg-emoji emoji-id=\"5769289093221454192\">🔗</tg-emoji> <b>Юзернейм:</b> {username}\n"
        f"<tg-emoji emoji-id=\"5836907383292436018\">💎</tg-emoji> <b>Баланс:</b> <code>0 руб.</code>"
    )
    await callback_query.message.answer(text, reply_markup=get_main_button(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'rules')
async def process_rules(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    text = (
        "<tg-emoji emoji-id=\"6032636795387121097\">🛡</tg-emoji> Перед использованием бота, пожалуйста прочтите правила указанные ниже <tg-emoji emoji-id=\"5963087934696459905\">⬇️</tg-emoji>\n\n"
        "<tg-emoji emoji-id=\"6039630677182254664\">📂</tg-emoji> <a href=\"https://telegra.ph\">Пользовательское соглашение</a>\n"
        "<tg-emoji emoji-id=\"6039630677182254664\">📂</tg-emoji> <a href=\"https://telegra.ph\">Политика конфиденциальности</a>"
    )
    await callback_query.message.answer(text, reply_markup=get_main_button(), parse_mode="HTML", link_preview_options=LinkPreviewOptions(is_disabled=True))

@dp.callback_query(lambda c: c.data == 'support')
async def process_support(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    text = (
        "<tg-emoji emoji-id=\"6021418126061605425\">📞</tg-emoji> <b>Техническая поддержка</b>\n\n"
        "<tg-emoji emoji-id=\"6039450962865688331\">📝</tg-emoji> Введите <b>тему вашего обращения</b>"
    )
    await callback_query.message.answer(text, reply_markup=None, parse_mode="HTML")
    await state.set_state(SupportStates.waiting_for_topic)

@dp.message(SupportStates.waiting_for_topic)
async def ticket_topic_received(message: types.Message, state: FSMContext):
    global ticket_counter
    ticket_counter += 1
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"
    user_fullname = message.from_user.full_name
    
    user_text = (
        "<tg-emoji emoji-id=\"6039450962865688331\">📝</tg-emoji> Ваше сообщение было <b>отправлено в поддержку</b>, ожидайте <b>ответа</b>\n"
        f"<tg-emoji emoji-id=\"5870998024779468554\">🔢</tg-emoji> Номер вашей заявки: <code>#{ticket_counter}</code>"
    )
    await message.answer(user_text, reply_markup=get_main_button(), parse_mode="HTML")
    
    admin_text = (
        f"<tg-emoji emoji-id=\"6039614175917903752\">✏️</tg-emoji> <b>Новое обращение в поддержку! Tiket #{ticket_counter}</b>\n\n"
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

@dp.callback_query(lambda c: c.data.startswith('ban_'))
async def admin_ban_start(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID: return
    target_user_id = int(callback_query.data.split('_')[1])
    await state.update_data(ban_user_id=target_user_id)
    await state.set_state(SupportStates.waiting_for_ban_reason)
    await callback_query.answer()
    await callback_query.message.reply("<tg-emoji emoji-id=\"5850309953293653168\">⚙️</tg-emoji>Напишите причину блокировки:", parse_mode="HTML")

@dp.message(SupportStates.waiting_for_ban_reason)
async def admin_ban_reason_received(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    target_user_id = data.get("ban_user_id")
    banned_users[target_user_id] = message.text
    text_ban = (
        "<tg-emoji emoji-id=\"6030563507299160824\">❗️</tg-emoji>Вы заблокированы администратором<tg-emoji emoji-id=\"6030563507299160824\">❗️</tg-emoji>\n"
        f"<tg-emoji emoji-id=\"6039422865189638057\">📣</tg-emoji>Причина: {message.text}"
    )
    try:
        await bot.send_message(chat_id=target_user_id, text=text_ban, parse_mode="HTML")
    except Exception as e:
        print(f"Не удалось отправить карточку бана: {e}")
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith('reply_'))
async def admin_reply_start(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID: return
    target_user_id = int(callback_query.data.split('_')[1])
    await state.update_data(reply_to_user_id=target_user_id)
    await state.set_state(SupportStates.waiting_for_admin_reply)
    await callback_query.answer()
    await callback_query.message.reply("<tg-emoji emoji-id=\"6039404727542747508\">⌨️</tg-emoji>Напишите ответ пользователю:", parse_mode="HTML")

@dp.message(SupportStates.waiting_for_admin_reply)
async def admin_send_reply_message(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    target_user_id = data.get("reply_to_user_id")
    reply_text = (
        f"<tg-emoji emoji-id=\"6021418126061605425\">📞</tg-emoji> Ваш тикет <b>#{ticket_counter}</b> был <b>обработан</b>\n"
        f"<tg-emoji emoji-id=\"5771851822897566479\">📝</tg-emoji> Ответ: {message.text}\n"
        f"<tg-emoji emoji-id=\"6021681257232994766\">🔒</tg-emoji> Ваш тикет был <b>автоматически закрыт</b>"
    )
    try:
        await bot.send_message(chat_id=target_user_id, text=reply_text, reply_markup=get_main_button(), parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")
    await state.clear()

@dp.callback_query(lambda c: c.data == 'main')
async def process_main(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    try:
        await callback_query.message.delete()
    except:
        pass
    await state.clear()
    await callback_query.message.answer(START_TEXT, reply_markup=get_buttons(), parse_mode="HTML")

# --- СТАРТ БОТА ---
async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    async def main_runner():
        await bot.delete_webhook(drop_pending_updates=True)
        await main()
    asyncio.run(main_runner())
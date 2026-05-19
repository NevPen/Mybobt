import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8690556428:AAHV7WiJMeGKvmsOGYdNodK1BQZcf4S4aJA"
ADMIN_ID = 7604556074 
PHOTO_PATH = "banner.jpg" 
DATA_FILE = "shop_data.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилища в памяти
banned_users = {}
ticket_counter = 0

# --- СОСТОЯНИЯ (FSM) ---
class SupportStates(StatesGroup):
    waiting_for_topic = State()        
    waiting_for_admin_reply = State()  
    waiting_for_ban_reason = State()   

class AdminStates(StatesGroup):
    waiting_for_price = State()     
    waiting_for_vip_link = State()  
    waiting_for_key = State()       

# --- РАБОТА С JSON ---
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

# --- КЛАВИАТУРЫ ПОЛЬЗОВАТЕЛЯ ---
def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Магазин", callback_data="shop", icon_custom_emoji_id="5920332557466997677")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile", icon_custom_emoji_id="6035084557378654059")],
        [InlineKeyboardButton(text="Поддержка", callback_data="support", icon_custom_emoji_id="6039422865189638057")],
        [InlineKeyboardButton(text="Правила", callback_data="rules", icon_custom_emoji_id="6028435952299413210")]
    ])

def get_shop_cats_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Lebro Cheat", callback_data="prod_lebro", icon_custom_emoji_id="5886285355279193209")],
        [InlineKeyboardButton(text="Главная", callback_data="main", icon_custom_emoji_id="5938537205847822613")]
    ])

def get_versions_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Lite", callback_data="ver_lebro_lite", icon_custom_emoji_id="5893057118545646106"),
         InlineKeyboardButton(text="Vip", callback_data="ver_lebro_vip", icon_custom_emoji_id="5893236738372932548")],
        [InlineKeyboardButton(text="Главная", callback_data="main", icon_custom_emoji_id="5938537205847822613")]
    ])

def get_periods_kb(version_type):
    data = load_shop_data()
    items = data.get(version_type, {})
    kb = []
    labels = {"1_day": "1 день", "7_days": "7 дней", "30_days": "30 дней", "forever": "Навсегда"}
    for period, val in items.items():
        if len(val["keys"]) > 0:
            kb.append([InlineKeyboardButton(text=labels[period], callback_data=f"buy_{version_type}_{period}", icon_custom_emoji_id="5836907383292436018")])
    kb.append([InlineKeyboardButton(text="Главная", callback_data="main", icon_custom_emoji_id="5938537205847822613")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_pay_kb(version_type, period):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перевод на карту", callback_data=f"pay_card_{version_type}_{period}", icon_custom_emoji_id="5769126056262898415")],
        [InlineKeyboardButton(text="Telegram Stars", url="https://t.me/morgodon", icon_custom_emoji_id="6028338546736107668")],
        [InlineKeyboardButton(text="Назад", callback_data=f"ver_{version_type}", icon_custom_emoji_id="6039519841256214245")]
    ])

# --- КЛАВИАТУРЫ АДМИНА ---
def get_admin_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить VIP", callback_data="adm_add_vip")],
        [InlineKeyboardButton(text="➕ Добавить LITE", callback_data="adm_add_lite")],
        [InlineKeyboardButton(text="❌ Удалить товар", callback_data="adm_del_main")]
    ])

def get_admin_periods_kb(version, prefix="add"):
    if "vip" in version:
        periods = [("1 день", "1d"), ("7 дней", "7d"), ("30 дней", "30d"), ("Навсегда", "forever")]
    else:
        periods = [("1 день", "1d"), ("7 дней", "7d")]
    
    kb = [[InlineKeyboardButton(text=p[0], callback_data=f"{prefix}_{version}_{p[1]}")] for p in periods]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ПРОВЕРКА БЛОКИРОВКИ ---
@dp.message(lambda m: m.from_user.id in banned_users)
@dp.callback_query(lambda c: c.from_user.id in banned_users)
async def check_ban(event):
    reason = banned_users.get(event.from_user.id, "Не указана")
    text = f"❗️Вы заблокированы❗️\nПричина: {reason}"
    if isinstance(event, types.Message):
        await event.answer(text)
    else:
        await event.answer(text, show_alert=True)

# --- ОСНОВНЫЕ КОМАНДЫ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🙂 Добро пожаловать в Morgodon Shop\n\nДля покупки товаров используйте кнопки ниже ⬇️", reply_markup=get_main_kb())

@dp.message(Command("boom"))
async def cmd_boom(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.clear()
        await message.answer("Панель управления магазином:", reply_markup=get_admin_main_kb())

# --- ЛОГИКА МАГАЗИНА ---
@dp.callback_query(F.data == "main")
async def call_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try: await call.message.delete()
    except: pass
    await call.message.answer("🙂 Добро пожаловать в Morgodon Shop\n\nДля покупки товаров используйте кнопки ниже ⬇️", reply_markup=get_main_kb())

@dp.callback_query(F.data == "shop")
async def call_shop(call: types.CallbackQuery):
    await call.message.edit_text("🛍 <b>Выберите нужный товар</b>", reply_markup=get_shop_cats_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "prod_lebro")
async def call_lebro(call: types.CallbackQuery):
    await call.message.edit_text("<b>Выберите версию Lebro Cheat</b>", reply_markup=get_versions_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("ver_"))
async def call_ver_select(call: types.CallbackQuery):
    v_type = call.data.replace("ver_", "")
    await call.message.edit_text("<b>Выберите период подписки:</b>", reply_markup=get_periods_kb(v_type), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def call_buy_item(call: types.CallbackQuery):
    await call.message.delete()
    data_str = call.data.replace("buy_", "")
    v_type = "lebro_vip" if "lebro_vip" in data_str else "lebro_lite"
    period = data_str.replace(f"{v_type}_", "")
    
    data = load_shop_data()
    item = data[v_type][period]
    
    labels_v = {"lebro_vip": "Vip", "lebro_lite": "Lite"}
    labels_p = {"1_day": "1D", "7_days": "7D", "30_days": "30D", "forever": "Навсегда"}
    
    # Исправленный текст (в наличии / без лишних точек)
    text = (
        f"📂Выбран товар - <b>Lebro Cheat ({labels_p[period]}-{labels_v[v_type]})</b>\n\n"
        f"📂Товара в наличии - <code>{len(item['keys'])}</code>\n"
        f"🪙Цена - <code>{item['price']} руб</code>\n\n"
        "Для оплаты воспользуйтесь кнопками ниже⬇️"
    )

    if os.path.exists(PHOTO_PATH):
        await call.message.answer_photo(FSInputFile(PHOTO_PATH), caption=text, reply_markup=get_pay_kb(v_type, period), parse_mode="HTML")
    else:
        await call.message.answer(text, reply_markup=get_pay_kb(v_type, period), parse_mode="HTML")

@dp.callback_query(F.data.startswith("pay_card_"))
async def call_pay_details(call: types.CallbackQuery):
    data_str = call.data.replace("pay_card_", "")
    v_type = "lebro_vip" if "lebro_vip" in data_str else "lebro_lite"
    period = data_str.replace(f"{v_type}_", "")
    
    data = load_shop_data()
    price = data[v_type][period]["price"]
    
    labels_v = {"lebro_vip": "Vip", "lebro_lite": "Lite"}
    labels_p = {"1_day": "1D", "7_days": "7D", "30_days": "30D", "forever": "Навсегда"}

    pay_text = (
        "🌐<b>Перевод на карту</b>\n\n"
        f"📥Товар: {labels_p[period]}-{labels_v[v_type]}\n"
        f"🪙Цена: {price} руб\n\n"
        "💰Банк: Сбер\n"
        "👤Получатель: Дамир. Ф\n"
        "👛Номер: <code>+79373521278</code>\n\n"
        "➕В комментарии к переводу укажите свой юзернейм.\n"
        "📷После оплаты отправьте боту скриншот оплаты."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Telegram Stars", url="https://t.me/morgodon", icon_custom_emoji_id="6028338546736107668")],
        [InlineKeyboardButton(text="Назад", callback_data=f"buy_{v_type}_{period}", icon_custom_emoji_id="6039519841256214245")]
    ])
    
    await call.message.edit_caption(caption=pay_text, reply_markup=kb, parse_mode="HTML")

# --- ПРОФИЛЬ И ПРАВИЛА ---
@dp.callback_query(F.data == "profile")
async def call_profile(call: types.CallbackQuery):
    text = (f"👤 <b>Ваш профиль:</b>\n"
            f"🆔 ID: <code>{call.from_user.id}</code>\n"
            f"🔗 Юзер: @{call.from_user.username if call.from_user.username else 'нет'}\n"
            f"💎 Баланс: 0 руб")
    await call.message.edit_text(text, reply_markup=get_back_main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "rules")
async def call_rules(call: types.CallbackQuery):
    text = "🛡 <b>Правила магазина</b>\n\n1. Возврата нет.\n2. Перепродажа ключей запрещена."
    await call.message.edit_text(text, reply_markup=get_back_main_kb(), parse_mode="HTML")

def get_back_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Главная", callback_data="main")]])

# --- ПОДДЕРЖКА ---
@dp.callback_query(F.data == "support")
async def call_support(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("📞 Опишите вашу проблему (введите тему):")
    await state.set_state(SupportStates.waiting_for_topic)

@dp.message(SupportStates.waiting_for_topic)
async def process_support(message: types.Message, state: FSMContext):
    global ticket_counter
    ticket_counter += 1
    await message.answer(f"✅ Сообщение отправлено. Тикет #{ticket_counter}", reply_markup=get_back_main_kb())
    
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ответить", callback_data=f"reply_{message.from_user.id}"),
         InlineKeyboardButton(text="Бан", callback_data=f"ban_{message.from_user.id}")]
    ])
    await bot.send_message(ADMIN_ID, f"🆘 <b>Тикет #{ticket_counter}</b>\nОт: {message.from_user.id}\nТекст: {message.text}", reply_markup=adm_kb, parse_mode="HTML")
    await state.clear()

# --- АДМИНСКИЕ ДЕЙСТВИЯ (ДОБАВЛЕНИЕ/УДАЛЕНИЕ) ---
@dp.callback_query(F.data.startswith("adm_add_"))
async def adm_select_ver(call: types.CallbackQuery):
    ver = "vip" if "vip" in call.data else "lite"
    await call.message.edit_text(f"Выберите период для {ver.upper()}:", reply_markup=get_admin_periods_kb(f"lebro_{ver}"))

ADMIN_MAP = {
    "add_lebro_vip_1d": ("lebro_vip", "1_day"),
    "add_lebro_vip_7d": ("lebro_vip", "7_days"),
    "add_lebro_vip_30d": ("lebro_vip", "30_days"),
    "add_lebro_vip_forever": ("lebro_vip", "forever"),
    "add_lebro_lite_1d": ("lebro_lite", "1_day"),
    "add_lebro_lite_7d": ("lebro_lite", "7_days")
}

@dp.callback_query(lambda c: c.data in ADMIN_MAP)
async def adm_start_add(call: types.CallbackQuery, state: FSMContext):
    v, p = ADMIN_MAP[call.data]
    await state.update_data(v=v, p=p)
    await call.message.answer("Введите цену:")
    await state.set_state(AdminStates.waiting_for_price)

@dp.message(AdminStates.waiting_for_price)
async def adm_price(message: types.Message, state: FSMContext):
    await state.update_data(pr=message.text)
    await message.answer("Ссылка на VIP канал:")
    await state.set_state(AdminStates.waiting_for_vip_link)

@dp.message(AdminStates.waiting_for_vip_link)
async def adm_link(message: types.Message, state: FSMContext):
    await state.update_data(lnk=message.text)
    await message.answer("Введите ключ:")
    await state.set_state(AdminStates.waiting_for_key)

@dp.message(AdminStates.waiting_for_key)
async def adm_finish(message: types.Message, state: FSMContext):
    s = await state.get_data()
    data = load_shop_data()
    data[s['v']][s['p']]["price"] = s['pr']
    data[s['v']][s['p']]["vip_link"] = s['lnk']
    data[s['v']][s['p']]["keys"].append(message.text)
    save_shop_data(data)
    await message.answer("✅ Товар добавлен!", reply_markup=get_admin_main_kb())
    await state.clear()

# --- ОТВЕТ И БАН ---
@dp.callback_query(F.data.startswith("reply_"))
async def adm_reply_start(call: types.CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[1])
    await state.update_data(target=uid)
    await call.message.answer("Введите ответ:")
    await state.set_state(SupportStates.waiting_for_admin_reply)

@dp.message(SupportStates.waiting_for_admin_reply)
async def adm_reply_send(message: types.Message, state: FSMContext):
    d = await state.get_data()
    await bot.send_message(d['target'], f"📞 Ответ поддержки:\n{message.text}")
    await message.answer("Отправлено.")
    await state.clear()

@dp.callback_query(F.data.startswith("ban_"))
async def adm_ban_start(call: types.CallbackQuery, state: FSMContext):
    uid = int(call.data.split("_")[1])
    await state.update_data(target=uid)
    await call.message.answer("Причина бана:")
    await state.set_state(SupportStates.waiting_for_ban_reason)

@dp.message(SupportStates.waiting_for_ban_reason)
async def adm_ban_finish(message: types.Message, state: FSMContext):
    d = await state.get_data()
    banned_users[d['target']] = message.text
    await message.answer("Пользователь забанен.")
    await state.clear()

# --- СТАРТ ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

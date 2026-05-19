import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Токен вашего бота
BOT_TOKEN = "8690556428:AAHV7WiJMeGKvmsOGYdNodK1BQZcf4S4aJA"

# ID канала для отзывов (Обязательно замени на ID своего канала, должен начинаться с -100)
REVIEWS_CHANNEL_ID = -1002345678901  

# Список ID администраторов (Дамир и morgodon)
ADMIN_IDS = [7604556074, 6100964004]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище блокировок в памяти
banned_users = {}
ticket_counter = 0

# Словари для красивого вывода в нужном формате
LABELS_VER = {"lebro_vip": "vip", "lebro_lite": "lite"}
LABELS_PER = {"1_day": "1D", "7_days": "7D", "30_days": "30D", "forever": "FOREVER"}

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
    waiting_for_decline_reason = State()  

class PurchaseStates(StatesGroup):
    waiting_for_receipt = State()

class ReviewStates(StatesGroup):
    waiting_for_review = State()

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

# --- ИСПРАВЛЕННАЯ КЛАВИАТУРА ПЕРИОДОВ (Короткие кнопки: 1D, 7D и т.д.) ---
def get_user_periods_keyboard(version_type):
    current_data = load_shop_data()
    version_items = current_data.get(version_type, {})
    keyboard_structure = []
    
    for period, item_data in version_items.items():
        keys_list = item_data.get("keys", [])
        if len(keys_list) > 0:  
            button_text = f"💎 {LABELS_PER.get(period, period)}"
            keyboard_structure.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"buy_{version_type}_{period}"
            )])
            
    keyboard_structure.append([InlineKeyboardButton(text="Главная\u200b", callback_data="main", icon_custom_emoji_id="5938537205847822613")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_structure)

def get_payment_keyboard(version_type, period):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перевод на карту\u200b", callback_data=f"pay_card_{version_type}_{period}", icon_custom_emoji_id="5769126056262898415")],
        [InlineKeyboardButton(text="Telegram Stars", url="https://t.me/morgodon", icon_custom_emoji_id="6028338546736107668")],
        [InlineKeyboardButton(text="Назад\u200b", callback_data=f"ver_{version_type}", icon_custom_emoji_id="6039519841256214245")]
    ])

def get_after_card_payment_keyboard(version_type, period):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад\u200b", callback_data=f"buy_{version_type}_{period}", icon_custom_emoji_id="6039519841256214245")]
    ])

def get_admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить VIP\u200b", callback_data="adm_choose_vip")],
        [InlineKeyboardButton(text="➕ Добавить LITE\u200b", callback_data="adm_choose_lite")],
        [InlineKeyboardButton(text="❌ Удалить товар\u200b", callback_data="adm_delete_main")]
    ])

def get_admin_periods_keyboard(version, prefix="add"):
    if version == "vip" or version == "lebro_vip":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 день\u200b", callback_data=f"{prefix}_vip_1d")],
            [InlineKeyboardButton(text="7 дней\u200b", callback_data=f"{prefix}_vip_7d")],
            [InlineKeyboardButton(text="30 дней\u200b", callback_data=f"{prefix}_vip_30d")],
            [InlineKeyboardButton(text="Навсегда\u200b", callback_data=f"{prefix}_vip_forever")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 день\u200b", callback_data=f"{prefix}_lite_1d")],
            [InlineKeyboardButton(text="7 дней\u200b", callback_data=f"{prefix}_lite_7d")]
        ])

def get_receipt_admin_buttons(user_id: int, version: str, period: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"rcpt_accept_{user_id}_{version}_{period}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"rcpt_decline_{user_id}_{version}_{period}")
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

# --- ОБРАБОТКА ПОЛУЧЕНИЯ ЧЕКА ---
@dp.message(F.photo | F.document)
async def handle_receipt(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state in [AdminStates.waiting_for_price, AdminStates.waiting_for_vip_link, AdminStates.waiting_for_key, ReviewStates.waiting_for_review]:
        return
    if message.from_user.id in ADMIN_IDS and current_state in [AdminStates.waiting_for_price, AdminStates.waiting_for_vip_link, AdminStates.waiting_for_key]:
        return

    user_data = await state.get_data()
    chosen_version = user_data.get("pay_version", "Неизвестно")
    chosen_period = user_data.get("pay_period", "Неизвестно")
    
    version_title = LABELS_VER.get(chosen_version, chosen_version)
    period_title = LABELS_PER.get(chosen_period, chosen_period)

    user_reply_text = "<tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> Чек отправлен на проверку. Ожидайте подтверждения."
    await message.reply(user_reply_text, parse_mode="HTML")
    
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"
    info_text = (
        f"<tg-emoji emoji-id=\"6039573425268201570\">📤</tg-emoji> <b>Получен новый чек на проверку!</b>\n\n"
        f"<tg-emoji emoji-id=\"6035084557378654059\">👤</tg-emoji> <b>Пользователь:</b> {message.from_user.full_name}\n"
        f"<tg-emoji emoji-id=\"6028171274939797252\">🔗</tg-emoji> <b>Юзернейм:</b> {username}\n"
        f"<tg-emoji emoji-id=\"6032693626394382504\">👤</tg-emoji> <b>ID:</b> <code>{message.from_user.id}</code>\n\n"
        f"📦 <b>Товар:</b> Lebro ({period_title}-{version_title})"
    )
    
    reply_markup = get_receipt_admin_buttons(message.from_user.id, chosen_version, chosen_period)
    
    for admin_id in ADMIN_IDS:
        try:
            if message.photo:
                await bot.send_photo(chat_id=admin_id, photo=message.photo[-1].file_id, caption=info_text, reply_markup=reply_markup, parse_mode="HTML")
            elif message.document:
                await bot.send_document(chat_id=admin_id, document=message.document.file_id, caption=info_text, reply_markup=reply_markup, parse_mode="HTML")
        except:
            pass
    
    await state.clear()

# --- ИСПРАВЛЕННАЯ ВЫДАЧА ТОВАРА (Скриншот 1) ---
@dp.callback_query(F.data.startswith("rcpt_accept_"))
async def admin_accept_receipt(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS: return
    await callback_query.answer()
    
    data_parts = callback_query.data.split("_")
    target_user_id = int(data_parts[2])
    version_type = f"{data_parts[3]}_{data_parts[4]}"
    
    if len(data_parts) == 7:
        period = f"{data_parts[5]}_{data_parts[6]}"
    else:
        period = data_parts[5]

    current_data = load_shop_data()
    item_data = current_data.get(version_type, {}).get(period, {})
    keys_list = item_data.get("keys", [])
    vip_link = item_data.get("vip_link", "https://t.me/morgodon")

    if not keys_list:
        await callback_query.message.reply("❌ Ошибка! В базе закончились ключи.")
        return

    user_key = keys_list.pop(0)
    save_shop_data(current_data)

    version_title = LABELS_VER.get(version_type, version_type)
    period_title = LABELS_PER.get(period, period).lower()

    # Новый текст выдачи товара с нужным эмодзи и форматированием
    success_text = (
        f"<tg-emoji emoji-id=\"6041720006973067267\">👍</tg-emoji>Ваш чек оплаты был подтверждён.\n"
        f"Спасибо за покупку <b>Lebro ({period_title}-{version_title})</b>\n\n"
        f"Ключ: —- <code>{user_key}</code>"
    )
    
    # Безопасная проверка ссылки
    if not vip_link or not vip_link.startswith("http"):
        vip_url = "https://t.me/morgodon"
    else:
        vip_url = vip_link

    success_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Приват", url=vip_url)],
        [InlineKeyboardButton(text="Написать отзыв", callback_data=f"leave_review_{period_title}_{version_title}")]
    ])
    
    try:
        await bot.send_message(chat_id=target_user_id, text=success_text, reply_markup=success_kb, parse_mode="HTML")
        await callback_query.message.edit_caption(caption=callback_query.message.caption + "\n\n🟢 <b>Чек успешно подтвержден!</b>", reply_markup=None, parse_mode="HTML")
    except Exception as e:
        await callback_query.message.reply(f"❌ Не удалось отправить сообщение пользователю: {e}")

@dp.callback_query(F.data.startswith("rcpt_decline_"))
async def admin_decline_receipt(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS: return
    await callback_query.answer()
    
    data_parts = callback_query.data.split("_")
    target_user_id = int(data_parts[2])
    
    await state.update_data(decline_user_id=target_user_id, decline_msg_id=callback_query.message.message_id)
    await state.set_state(AdminStates.waiting_for_decline_reason)
    
    await callback_query.message.reply("📝 Напишите причину отклонения чека:")

@dp.message(AdminStates.waiting_for_decline_reason)
async def admin_reason_received(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    
    state_data = await state.get_data()
    target_user_id = state_data.get("decline_user_id")
    decline_msg_id = state_data.get("decline_msg_id")
    reason = message.text

    decline_text = (
        f"<tg-emoji emoji-id=\"6042029429301973188\">☹️</tg-emoji> Ваш чек оплаты был отклонен.\n"
        f"<b>Причина:</b> {reason}"
    )
    
    try:
        await bot.send_message(chat_id=target_user_id, text=decline_text, parse_mode="HTML")
        await message.answer("🔴 Чек отклонен, причина отправлена пользователю.")
        try:
            for admin_id in ADMIN_IDS:
                await bot.edit_message_caption(chat_id=admin_id, message_id=decline_msg_id, caption=f"🔴 <b>Чек отклонен.</b>\nПричина: {reason}", reply_markup=None)
        except:
            pass
    except Exception as e:
        await message.answer(f"❌ Не удалось уведомить пользователя: {e}")
        
    await state.clear()

# --- ИСПРАВЛЕННАЯ СИСТЕМА ОТЗЫВОВ (Пересылка сообщений от имени юзера) ---
@dp.callback_query(F.data.startswith("leave_review_"))
async def start_review_process(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data_parts = callback_query.data.replace("leave_review_", "").split("_")
    p_title = data_parts[0]
    v_title = data_parts[1]
    
    await state.update_data(review_product=f"Lebro ({p_title}-{v_title})")
    await state.set_state(ReviewStates.waiting_for_review)
    
    # Новый текст запроса отзыва
    await callback_query.message.answer("<tg-emoji emoji-id=\"6028205772117118673\">⬆️</tg-emoji>Пожалуйста, напишите ваш отзыв одним сообщением.")

@dp.message(ReviewStates.waiting_for_review)
async def process_user_review(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    product_name = state_data.get("review_product", "Lebro")
    
    # 1. Отправляем карточку купленного товара над отзывом
    header_text = (
        f"Товар: <b>{product_name}</b>\n"
        f"Отзыв —"
    )
    
    try:
        # Отправляем шапку отзыва в канал
        await bot.send_message(chat_id=REVIEWS_CHANNEL_ID, text=header_text, parse_mode="HTML")
        
        # 2. ПЕРЕСЫЛАЕМ сообщение пользователя! Будет плашка "Переслано от пользователя"
        await bot.forward_message(
            chat_id=REVIEWS_CHANNEL_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
            
        # Новый текст благодарности за отзыв
        await message.answer("<tg-emoji emoji-id=\"6043847274210005137\">😝</tg-emoji>Спасибо большое за ваш отзыв", reply_markup=get_main_button(), parse_mode="HTML")
    except Exception as e:
        await message.answer("❌ Не удалось отправить отзыв в канал. Проверьте права бота.")
        print(f"Ошибка отзывов: {e}")
        
    await state.clear()

# --- ОСТАЛЬНАЯ ЛОГИКА БОТА ---
@dp.message(Command("boom"))
async def admin_panel_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await state.clear()
    await message.answer("Панель управления магазином:", reply_markup=get_admin_main_keyboard())

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(START_TEXT, reply_markup=get_buttons(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'shop')
async def process_shop(callback_query: types.CallbackQuery):
    await callback_query.answer()  
    try: await callback_query.message.delete()
    except: pass
    text = "<tg-emoji emoji-id=\"5870563425628721113\">🛍</tg-emoji> <b>Выберите нужный товар</b>"
    await callback_query.message.answer(text, reply_markup=get_shop_categories(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'prod_lebro')
async def process_lebro_cheat(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    text = "<b>Выберите версию Lebro Cheat</b>"
    await callback_query.message.answer(text, reply_markup=get_lebro_versions(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data in ['ver_lebro_lite', 'ver_lebro_vip'])
async def user_select_version(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
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
    try: await callback_query.message.delete()
    except: pass
    
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
    
    v_title = LABELS_VER.get(version_type, version_type)
    p_title = LABELS_PER.get(period, period)
    
    text_details = (
        f"<tg-emoji emoji-id=\"6039630677182254664\">📂</tg-emoji>Выбран товар - <b>Lebro Cheat ({p_title}-{v_title})</b>\n\n"
        f"📂Товара в наличии - <code>{count}</code>\n"
        f"💰Цена - <code>{price}  руб</code>\n\n"
        "Для оплаты воспользуйтесь кнопками ниже 👇"
    )
    
    if os.path.exists("banner.jpg"):
        photo = FSInputFile("banner.jpg")
        await callback_query.message.answer_photo(photo=photo, caption=text_details, reply_markup=get_payment_keyboard(version_type, period), parse_mode="HTML")
    else:
        await callback_query.message.answer(text_details, reply_markup=get_payment_keyboard(version_type, period), parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith('pay_card_'))
async def process_card_payment_details(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    data_str = callback_query.data.replace("pay_card_", "")
    if data_str.startswith("lebro_vip_"):
        version_type = "lebro_vip"
        period = data_str.replace("lebro_vip_", "")
    else:
        version_type = "lebro_lite"
        period = data_str.replace("lebro_lite_", "")
        
    await state.update_data(pay_version=version_type, pay_period=period)
    await state.set_state(PurchaseStates.waiting_for_receipt)
        
    current_data = load_shop_data()
    item_data = current_data.get(version_type, {}).get(period, {})
    price = item_data.get("price", "0")
    
    v_title = LABELS_VER.get(version_type, version_type)
    p_title = LABELS_PER.get(period, period)
    
    payment_details_text = (
        "💳 <b>Перевод на карту</b>\n\n"
        f"📦 Товар: 1 день-Vip\n"
        f"💰 Цена: {price}  руб\n\n"
        "💳 Банк: Сбер\n"
        "👤 Получатель: Дамир. Ф\n"
        "👛 Номер: <code>+79373521278</code>\n\n"
        "💬 В комментарии к переводу укажите свой юзернейм.\n"
        "📷 После оплаты отправьте боту скриншот оплаты."
    )
    
    try:
         await callback_query.message.edit_caption(caption=payment_details_text, reply_markup=get_after_card_payment_keyboard(version_type, period), parse_mode="HTML")
    except Exception:
         await callback_query.message.edit_text(text=payment_details_text, reply_markup=get_after_card_payment_keyboard(version_type, period), parse_mode="HTML")

# --- СИСТЕМА ДОБАВЛЕНИЯ ТОВАРОВ АДМИНИСТРАТОРА ---
@dp.callback_query(lambda c: c.data in ['adm_choose_vip', 'adm_choose_lite'])
async def admin_select_version(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS: return
    await callback_query.answer()
    try: callback_query.message.delete()
    except: pass
    version = "vip" if callback_query.data == "adm_choose_vip" else "lite"
    await callback_query.message.answer(f"Выберите период для настройки версии {version.upper()}:", reply_markup=get_admin_periods_keyboard(version, prefix="add"))

ADMIN_CALLBACK_MAP = {
    "add_vip_1d": ("lebro_vip", "1_day"), "add_vip_7d": ("lebro_vip", "7_days"),
    "add_vip_30d": ("lebro_vip", "30_days"), "add_vip_forever": ("lebro_vip", "forever"),
    "add_lite_1d": ("lebro_lite", "1_day"), "add_lite_7d": ("lebro_lite", "7_days")
}

@dp.callback_query(lambda c: c.data in ADMIN_CALLBACK_MAP.keys())
async def admin_select_period(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id not in ADMIN_IDS: return
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    version_type, period = ADMIN_CALLBACK_MAP[callback_query.data]
    await state.update_data(target_version=version_type, target_period=period)
    await state.set_state(AdminStates.waiting_for_price)
    await callback_query.message.answer("Введите цену товара:")

@dp.message(AdminStates.waiting_for_price)
async def admin_price_received(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await state.update_data(item_price=message.text)
    await state.set_state(AdminStates.waiting_for_vip_link)
    await message.reply("ссылка вип канал:")

@dp.message(AdminStates.waiting_for_vip_link)
async def admin_vip_link_received(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await state.update_data(item_vip_link=message.text)
    await state.set_state(AdminStates.waiting_for_key)
    await message.reply("напишите ключ:")

@dp.message(AdminStates.waiting_for_key)
async def admin_key_received(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
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

# --- СИСТЕМА УДАЛЕНИЯ ТОВАРОВ (КЛЮЧЕЙ) ---
@dp.callback_query(lambda c: c.data == 'adm_delete_main')
async def admin_delete_main_menu(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS: return
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удалить из VIP", callback_data="del_ver_vip")],
        [InlineKeyboardButton(text="Удалить из LITE", callback_data="del_ver_lite")]
    ])
    await callback_query.message.answer("Из какой версии вы хотите удалить товар?", reply_markup=kb)

@dp.callback_query(lambda c: c.data in ['del_ver_vip', 'del_ver_lite'])
async def admin_delete_select_period(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS: return
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    version = "vip" if callback_query.data == "del_ver_vip" else "lite"
    await callback_query.message.answer(f"Выберите период для удаления ключей версии {version.upper()}:", reply_markup=get_admin_periods_keyboard(version, prefix="del"))

ADMIN_DEL_CALLBACK_MAP = {
    "del_vip_1d": ("lebro_vip", "1_day"), "del_vip_7d": ("lebro_vip", "7_days"),
    "del_vip_30d": ("lebro_vip", "30_days"), "del_vip_forever": ("lebro_vip", "forever"),
    "del_lite_1d": ("lebro_lite", "1_day"), "del_lite_7d": ("lebro_lite", "7_days")
}

@dp.callback_query(lambda c: c.data in ADMIN_DEL_CALLBACK_MAP.keys())
async def admin_list_keys_for_deletion(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS: return
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    version_type, period = ADMIN_DEL_CALLBACK_MAP[callback_query.data]
    current_data = load_shop_data()
    keys_list = current_data.get(version_type, {}).get(period, {}).get("keys", [])
    
    if not keys_list:
        await callback_query.message.answer("В этой категории нет доступных ключей.", reply_markup=get_main_button())
        return
        
    kb_structure = []
    for idx, key in enumerate(keys_list):
        kb_structure.append([InlineKeyboardButton(text=f"🗑 Удалить: {key}", callback_data=f"confirm_del_{version_type}_{period}_{idx}")])
    kb_structure.append([InlineKeyboardButton(text="Назад в панель", callback_data="adm_delete_main")])
    await callback_query.message.answer("Выберите ключ, который хотите безвозвратно удалить:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_structure))

@dp.callback_query(lambda c: c.data.startswith('confirm_del_'))
async def admin_execute_deletion(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS: return
    await callback_query.answer()
    data_parts = callback_query.data.replace("confirm_del_", "").split("_")
    
    if "vip" in data_parts[1]:
        version_type = f"{data_parts[0]}_{data_parts[1]}"
        period = f"{data_parts[2]}_{data_parts[3]}" if data_parts[2] in ["1", "7", "30"] else data_parts[2]
        idx = int(data_parts[-1])
    else:
        version_type = f"{data_parts[0]}_{data_parts[1]}"
        period = f"{data_parts[2]}_{data_parts[3]}"
        idx = int(data_parts[-1])
        
    current_data = load_shop_data()
    try:
        removed_key = current_data[version_type][period]["keys"].pop(idx)
        save_shop_data(current_data)
        await callback_query.answer(f"Удален ключ: {removed_key}", show_alert=True)
    except:
        await callback_query.answer("Ошибка: ключ уже удален", show_alert=True)
    try: await callback_query.message.delete()
    except: pass
    await callback_query.message.answer("Панель управления магазином:", reply_markup=get_admin_main_keyboard())

# --- РАЗДЕЛ ПРОФИЛЬ, ПРАВИЛА, ПОДДЕРЖКА ---
@dp.callback_query(lambda c: c.data == 'profile')
async def process_profile(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    user_id = callback_query.from_user.id
    username = f"@{callback_query.from_user.username}" if callback_query.from_user.username else "Нет"
    text = (
        "<tg-emoji emoji-id=\"6035084557378654059\">👤</tg-emoji> <b>Ваш профиль:</b>\n"
        f"🆔 <b>ID аккаунта:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Юзернейм:</b> {username}\n"
        f"💎 <b>Баланс:</b> <code>0 руб</code>"
    )
    await callback_query.message.answer(text, reply_markup=get_main_button(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == 'rules')
async def process_rules(callback_query: types.CallbackQuery):
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    text = (
        "🛡 Перед использованием бота, пожалуйста прочтите правила указанные ниже ⬇️\n\n"
        "📂 <a href=\"https://telegra.ph\">Пользовательское соглашение</a>\n"
        "📂 <a href=\"https://telegra.ph\">Политика конфиденциальности</a>"
    )
    await callback_query.message.answer(text, reply_markup=get_main_button(), parse_mode="HTML", link_preview_options=LinkPreviewOptions(is_disabled=True))

@dp.callback_query(lambda c: c.data == 'support')
async def process_support(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    text = (
        "📞 <b>Техническая поддержка</b>\n\n"
        "📝 Введите <b>тему вашего обращения</b>"
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
        "📝 Ваше сообщение было <b>отправлено в поддержку</b>, ожидайте <b>ответа</b>\n"
        f"🔢 Номер вашей заявки: <code>#{ticket_counter}</code>"
    )
    await message.answer(user_text, reply_markup=get_main_button(), parse_mode="HTML")
    
    admin_text = (
        f"✏️ <b>Новое обращение в поддержку! Tiket #{ticket_counter}</b>\n\n"
        f"👤<b>Пользователь:</b> {user_fullname}\n"
        f"🔗<b>Юзернейм:</b> {username}\n"
        f"🆔 <b>ID аккаунта:</b> {user_id}\n\n"
        f"💬 <b>Текст обращения:</b>\n"
        f"<i>{message.text}</i>"
    )
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=None, parse_mode="HTML")
        except: pass
    await state.clear()

@dp.callback_query(lambda c: c.data == 'main')
async def process_main(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    try: await callback_query.message.delete()
    except: pass
    await state.clear()
    await callback_query.message.answer(START_TEXT, reply_markup=get_buttons(), parse_mode="HTML")

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    async def main_runner():
        await bot.delete_webhook(drop_pending_updates=True)
        await main()
    asyncio.run(main_runner())
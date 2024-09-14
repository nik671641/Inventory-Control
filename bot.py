import asyncio
import json

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from aiogram.types.web_app_info import WebAppInfo
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode

from functions import *
from config import TOKEN
from translations import get_translation

# Включаем логирование
logging.basicConfig(level=logging.WARNING)

# Инициализируем бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

dp.include_router(router)
user_sections = {}
user_language_cache = {}
language_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Русский")],
        [KeyboardButton(text="Română")]
    ],
    resize_keyboard=True
)

markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Зарегистрироваться", web_app=WebAppInfo(
    url="https://my-idea1.ru/"))]], resize_keyboard=True)
rom_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Înscrieți-vă", web_app=WebAppInfo(
    url="https://my-idea1.ru/"))]], resize_keyboard=True)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Взять инструмент"), KeyboardButton(text="Вернуть инструмент")],
        [KeyboardButton(text="График работы"), KeyboardButton(text="Выбрать язык")]
    ],
    resize_keyboard=True
)
rom_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Obțineți instrumentul"), KeyboardButton(text="Returnați unealta")],
        [KeyboardButton(text="Programul de lucru"), KeyboardButton(text="Selectați limba")]
    ],
    resize_keyboard=True
)

sections_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Инструменты"), KeyboardButton(text="Аксессуар для инструментов")],
        [KeyboardButton(text="Ручной инструмент"), KeyboardButton(text="Средство личной защиты")],
        [KeyboardButton(text="Инструмент для внутренней отделки")],
        [KeyboardButton(text="Назад")],

    ],
    resize_keyboard=True
)
rom_sections_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Instrumente"), KeyboardButton(text="Accesoriu pentru unelte")],
        [KeyboardButton(text="Unealtă manuală"), KeyboardButton(text="Echipament de protecție individuală")],
        [KeyboardButton(text="Instrumente pentru decorațiuni interioare")],
        [KeyboardButton(text="Înapoi")],
    ],
    resize_keyboard=True
)


async def get_user_language(chat_id: int) -> str:
    if chat_id in user_language_cache:
        return user_language_cache[chat_id]

    pool = await connect_to_db()
    async with pool.acquire() as connection:
        user = await connection.fetchrow("SELECT language FROM id_users WHERE chat_id = $1", chat_id)
        language = user.get('language', 'ru') if user else 'ru'

    user_language_cache[chat_id] = language

    return language


# Обработка команды /start
@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    chat_id = message.chat.id
    pool = await connect_to_db()

    async with pool.acquire() as connection:
        # Проверка, существует ли пользователь в базе данных
        user = await connection.fetchrow("SELECT * FROM id_users WHERE chat_id = $1", chat_id)

        if user:
            language = user_language_cache.get(chat_id,
                                               user.get('language', None))  # Проверить, есть ли язык у пользователя
            if language is None:
                # Если язык не выбран, предлагаем выбрать язык
                reply = await message.answer(get_translation('ru', 'language_prompt'), reply_markup=language_menu)
            else:
                # Отправить главное меню на выбранном языке
                main_menu_markup = rom_main_menu if language == 'ro' else main_menu
                reply = await message.answer(get_translation(language, 'already_registered'),
                                             reply_markup=main_menu_markup)
        else:
            # Если пользователя нет в базе данных, предлагаем выбрать язык
            reply = await message.answer(get_translation('ru', 'language_prompt'), reply_markup=language_menu)

    await handle_user_message(message)
    await handle_bot_message(message, reply)


@router.message(Command(commands=["menu"]))
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    pool = await connect_to_db()
    language = await get_user_language(chat_id)
    main_menu_markup = rom_main_menu if language == 'ro' else main_menu
    main_markup = rom_markup if language == 'ro' else markup
    choose_section = get_translation('ro', 'choose_section') if language == 'ro' else get_translation('ru',
                                                                                                      'choose_section')
    start_message = get_translation('ro', 'start_message', name=user_name) if language == 'ro' else get_translation(
        'ru',
        'start_message', name=user_name)
    async with pool.acquire() as connection:
        # Проверка наличия пользователя в базе данных
        user = await connection.fetchrow(
            "SELECT * FROM id_users WHERE chat_id = $1",
            chat_id
        )

        if user and chat_id:
            # Если пользователь уже существует, отправляем сообщение
            reply = await message.answer(choose_section, reply_markup=main_menu_markup)
            await handle_user_message(message)
            await handle_bot_message(message, reply)
        else:
            reply = await message.answer(start_message, reply_markup=main_markup)
            await handle_user_message(message)
            await handle_bot_message(message, reply)


@router.message(F.text.in_(["Русский", "Română"]))
async def handle_language_selection(message: Message):
    chat_id = message.chat.id
    selected_language = 'ru' if message.text == 'Русский' else 'ro'

    pool = await connect_to_db()
    async with pool.acquire() as connection:
        # Проверяем, есть ли пользователь в базе данных
        user = await connection.fetchrow("SELECT chat_id FROM id_users WHERE chat_id = $1", chat_id)

        # Если пользователь не найден, выводим приветственное сообщение и добавляем его в базу
        if not user:
            user_name = message.from_user.first_name
            start_message = get_translation(selected_language, 'start_message', name=user_name)
            main_menu_markup = rom_markup if selected_language == 'ro' else markup
            reply = await message.answer(start_message, reply_markup=main_menu_markup)

            # Вставляем запись о пользователе в базу
            await connection.execute("""
                    INSERT INTO id_users (chat_id, language) 
                    VALUES ($1, $2);
                """, chat_id, selected_language)
        else:
            # Если пользователь уже есть в базе, просто обновляем его язык
            await connection.execute("""
                    UPDATE id_users 
                    SET language = $1 
                    WHERE chat_id = $2;
                """, selected_language, chat_id)
            # Обновляем меню на выбранном языке
            main_menu_markup = rom_main_menu if selected_language == 'ro' else main_menu
            reply = await message.answer(get_translation(selected_language, 'choose_section'),
                                         reply_markup=main_menu_markup)

        # Обновляем кэш языка
        user_language_cache[chat_id] = selected_language

        # Дополнительные функции
        await handle_user_message(message)
        await handle_bot_message(message, reply)


@router.message(F.content_type == 'web_app_data')
async def web_app(message: types.Message):
    chat_id = message.chat.id
    # Разбор JSON-данных из сообщения
    res = json.loads(message.web_app_data.data)

    # Подключение к базе данных
    pool = await connect_to_db()
    if res['builder'] and res['name'] and res['surname']:
        async with pool.acquire() as connection:
            # Выполнение SQL-запроса для вставки данных в таблицу
            async with connection.transaction():
                # Insert data into the id_users table
                await connection.execute("""
                                    UPDATE id_users 
                                    SET builder_number = $2, Имя = $3, Фамилия = $4
                                    WHERE chat_id = $1
                                    """,
                                         chat_id, res['builder'], res['name'], res['surname'])

                language = user_language_cache.get(chat_id)
                choose_tool = get_translation('ro', 'choose_section') if language == 'ro' else get_translation('ru',
                                                                                                               'choose_section')
                main_menu_markup = rom_main_menu if language == 'ro' else main_menu

                reply = await message.answer(choose_tool, reply_markup=main_menu_markup)
                await handle_user_message(message)
                await handle_bot_message(message, reply)
    else:
        await message.answer('Error')
    # Освобождение ресурсов пула подключения
    await pool.close()


# Обработка кнопки "Взять инструмент"
@router.message(F.text.in_(["Взять инструмент", "Obțineți instrumentul"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    language = await get_user_language(chat_id)

    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu
    reply = await message.answer(get_translation(language, 'choose_section'), reply_markup=sections_menu_markup)

    await handle_user_message(message)
    await handle_bot_message(message, reply)


# Обработка кнопки "Вернуть инструмент"
@router.message(F.text.in_(["Вернуть инструмент", "Returnați unealta"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    await get_user_language(chat_id)
    await send_user_tools(message)


@router.message(F.text.in_(["Выбрать язык", "Selectați limba"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    language = await get_user_language(chat_id)

    reply = await message.answer(get_translation(language, 'language_prompt'),
                                 reply_markup=language_menu)

    await handle_user_message(message)
    await handle_bot_message(message, reply)


# Обработка кнопки "Инструменты"
@router.message(F.text.in_(["Инструменты", "Instrumente"]))
async def table_tool(message: Message):
    user_sections[message.chat.id] = "tools"

    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)

    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu
    reply = await message.answer("️🛠️", reply_markup=sections_menu_markup)

    await display_tools(message, 1, 21)
    await handle_bot_message(message, reply)


# Обработка кнопки "Аксессуар для инструментов"
@router.message(F.text.in_(["Аксессуар для инструментов", "Accesoriu pentru unelte"]))
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "accessories"

    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu
    reply = await message.answer("️🛠️", reply_markup=sections_menu_markup)

    await display_tools(message, 26, 103)
    await handle_bot_message(message, reply)


# Обработка кнопки "Ручной инструмент"
@router.message(F.text.in_(["Ручной инструмент", "Unealtă manuală"]))
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "hand_tools"

    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu

    reply = await message.answer("🪛", reply_markup=sections_menu_markup)
    await display_tools(message, 107, 140)
    await handle_bot_message(message, reply)


# Обработка кнопки "Средство личной защиты"
@router.message(F.text.in_(["Средство личной защиты", "Echipament de protecție individuală"]))
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "personal_protection"

    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu

    reply = await message.answer("⛑️", reply_markup=sections_menu_markup)
    await display_tools(message, 142, 153)
    await handle_bot_message(message, reply)


# Обработка кнопки "Инструмент для внутренней отделки"
@router.message(F.text.in_(["Инструмент для внутренней отделки", "Instrumente pentru decorațiuni interioare"]))
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "interior_tools"

    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu

    reply = await message.answer("🔨", reply_markup=sections_menu_markup)
    await display_tools(message, 155, 182)
    await handle_bot_message(message, reply)


# Обработка кнопки "Назад"
@router.message(F.text.in_(["Назад", "Înapoi"]))
async def handle_back(message: Message):
    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)

    if language == 'ru':
        start_message_text = get_translation('ru', 'choose_section')
        markup = main_menu  # Основное меню на русском
    elif language == 'ro':
        start_message_text = get_translation('ro', 'choose_section')
        markup = rom_main_menu  # Основное меню на румынском
    else:
        # Если язык не установлен, предлагаем выбрать язык
        start_message_text = get_translation('ru', 'language_prompt')
        markup = language_menu  # Клавиатура для выбора языка

    reply = await message.answer(start_message_text, reply_markup=markup)
    await handle_user_message(message)
    await handle_bot_message(message, reply)


@router.callback_query(F.data == "back_to_tools")
async def handle_back_to_tools(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    current_section = user_sections.get(chat_id, "tools")  # Используем текущее состояние пользователя

    if current_section == "tools":
        await display_tools(callback_query.message, 1, 21)
    elif current_section == "accessories":
        await display_tools(callback_query.message, 26, 103)
    elif current_section == "hand_tools":
        await display_tools(callback_query.message, 107, 140)
    elif current_section == "personal_protection":
        await display_tools(callback_query.message, 142, 153)
    elif current_section == "interior_tools":
        await display_tools(callback_query.message, 155, 182)
    else:
        await callback_query.message.answer("ERROR", reply_markup=main_menu)

    await callback_query.answer()


@router.callback_query(F.data == "back_to_tools2")
async def handle_back_to_tools(callback_query: types.CallbackQuery):
    await send_user_tools(callback_query.message)


async def display_tools(message: Message, start: int, end: int):
    logging.info("Fetching tools from database")
    text = message.text
    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    # Получаем список инструментов из базы данных
    tools = await fetch_tools(start, end)

    # Создаем список кнопок для клавиатуры, разделяя их на строки по 2 кнопки
    ru_keyboard_buttons = [
        [InlineKeyboardButton(text=tool['Инструменты'], callback_data=f"tool:{tool['id']}:{tool['Осталось']}")
         for tool in tools[i:i + 2]]
        for i in range(0, len(tools), 2)
    ]
    ro_keyboard_buttons = [
        [InlineKeyboardButton(text=tool['instrumente'], callback_data=f"tool:{tool['id']}:{tool['Осталось']}")
         for tool in tools[i:i + 2]]
        for i in range(0, len(tools), 2)
    ]

    # Создаем клавиатуру с кнопками
    lang_keyboard_buttons = ro_keyboard_buttons if language == 'ro' else ru_keyboard_buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=lang_keyboard_buttons)
    keyboard1 = message.reply_markup
    if keyboard1 and isinstance(keyboard1, InlineKeyboardMarkup):
        # Поиск кнопки с callback_data
        for row in keyboard1.inline_keyboard:
            for button in row:
                if button.callback_data == 'back_to_tools':
                    choose_tool = get_translation('ro', 'choose_tool') if language == 'ro' else get_translation('ru',
                                                                                                                'choose_tool')
                    await message.edit_text(choose_tool, reply_markup=keyboard)

    elif text == 'Инструменты' or 'Аксессуар для инструментов' or 'Ручной инструмент' or 'Средство личной защиты' or 'Инструмент для внутренней отделки' or 'Instrumente' or 'Accesoriu pentru unelte' or 'Unealtă manuală' or 'Echipament de protecție individuală' or 'Instrumente pentru decorațiuni interioare':
        choose_tool = get_translation('ro', 'choose_tool') if language == 'ro' else get_translation('ru', 'choose_tool')
        reply = await message.answer(choose_tool, reply_markup=keyboard)
        await handle_user_message(message)
        await handle_bot_message(message, reply)
    return keyboard


# Обработчик для выбора инструмента (callback handler)
@router.callback_query(F.data.startswith('tool:'))
async def process_tool_choice(callback_query: types.CallbackQuery):
    logging.info(f"Callback query received: {callback_query.data}")
    # Разделяем callback_data и извлекаем ID инструмента и количество

    # Split the callback data by colon and extract tool_id and tool_quantity
    _, tool_id, tools_quantity = callback_query.data.split(":")
    tool_id = int(tool_id)
    tools_quantity = int(tools_quantity)
    # Показ количества и кнопок увеличения/уменьшения
    await show_quantity_selection(callback_query.message, tool_id, tools_quantity)


async def show_quantity_selection(message: Message, tool_id: int, tools_quantity: int, current_quantity: int = 1):
    # Создаем inline-кнопки для изменения количества
    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    confirm = get_translation('ro', 'confirm') if language == 'ro' else get_translation('ru', 'confirm')
    back = get_translation('ro', 'back') if language == 'ro' else get_translation('ru', 'back')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"decrease:{tool_id}:{tools_quantity}:{current_quantity}"),
            InlineKeyboardButton(text=str(current_quantity), callback_data="ignore"),
            InlineKeyboardButton(text="➕", callback_data=f"increase:{tool_id}:{tools_quantity}:{current_quantity}")
        ],
        [InlineKeyboardButton(text=confirm, callback_data=f"confirm:{tool_id}:{current_quantity}")],
        [InlineKeyboardButton(text=back, callback_data=f"back_to_tools")],
    ])

    tools = await fetch_tools_quantity(tool_id)

    ru_tool_name = tools['Инструменты'].upper()
    ro_tool_name = tools['instrumente'].upper()
    tool_name = ro_tool_name if language == 'ro' else ru_tool_name
    tool_quantity = tools['Осталось']
    info_tool = get_translation('ro', 'info_tool', tool_name=tool_name,
                                tool_quantity=tool_quantity) if language == 'ro' else get_translation('ru',
                                                                                                      'info_tool',
                                                                                                      tool_name=tool_name,
                                                                                                      tool_quantity=tool_quantity)
    # Инструмент: {tool_name}\nОсталось на складе: {tool_quantity}" f"\nВыберите количество инструмента
    await message.edit_text(info_tool, reply_markup=keyboard, parse_mode=ParseMode.HTML)


# Обработчики для увеличения/уменьшения количества
@router.callback_query(lambda c: c.data and (c.data.startswith('increase:') or c.data.startswith('decrease:')))
async def change_quantity(callback_query: types.CallbackQuery):
    _, tool_id, tools_quantity, current_quantity = callback_query.data.split(':')
    current_quantity = int(current_quantity)
    tools_quantity = int(tools_quantity)
    chat_id = callback_query.message.chat.id

    language = user_language_cache.get(chat_id)
    error0 = get_translation('ro', 'error0') if language == 'ro' else get_translation('ru', 'error0')
    error1 = get_translation('ro', 'error1') if language == 'ro' else get_translation('ru', 'error1')

    if 'increase' in callback_query.data and current_quantity < tools_quantity:
        current_quantity += 1
        await show_quantity_selection(callback_query.message, int(tool_id), tools_quantity, current_quantity)
    elif 'decrease' in callback_query.data and current_quantity > 1:
        current_quantity -= 1
        await show_quantity_selection(callback_query.message, int(tool_id), tools_quantity, current_quantity)

    else:
        if current_quantity < tools_quantity:
            await callback_query.answer(error0,
                                        show_alert=True)
        elif current_quantity >= 1:
            await callback_query.answer(
                error1,
                show_alert=True)


@router.callback_query(F.data.startswith('confirm:'))
async def confirm_choice(callback_query: types.CallbackQuery):
    _, tool_id, quantity = callback_query.data.split(':')
    tool_id = int(tool_id)
    quantity = int(quantity)
    chat_id = callback_query.message.chat.id

    language = user_language_cache.get(chat_id)
    insufficient_stock = get_translation('ro', 'insufficient_stock') if language == 'ro' else get_translation('ru',
                                                                                                              'insufficient_stock')
    tool_not_found = get_translation('ro', 'tool_not_found') if language == 'ro' else get_translation('ru',
                                                                                                      'tool_not_found')

    # Подключение к базе данных
    pool = await connect_to_db()
    async with pool.acquire() as connection:
        # Проверка наличия инструмента в базе данных и получение текущего количества
        tool = await connection.fetchrow(
            "SELECT Инструменты, instrumente, Осталось FROM tools WHERE id = $1", tool_id
        )
        if tool:
            ru_tool_name = tool['Инструменты']
            ro_tool_name = tool['instrumente']
            remaining_quantity = int(tool['Осталось'])
            tool_name = ro_tool_name if language == 'ro' else ru_tool_name
            if remaining_quantity >= quantity:
                # Fetch all rows where chat_id matches the user's chat_id
                users = await connection.fetch(
                    "SELECT Инструменты, Количество, instrumente FROM user_tool WHERE chat_id = $1",
                    chat_id
                )

                # Flag to check if tool is found for this user
                tool_found = False

                for user in users:
                    ru_user_tool = user['Инструменты']
                    ro_user_tool = user['instrumente']
                    user_tool = ro_user_tool if language == 'ro' else ru_user_tool

                    if user_tool == tool_name:
                        new_quantity1 = quantity + int(user['Количество'])
                        await connection.execute(
                            "UPDATE user_tool SET Количество = $1 WHERE chat_id = $2 AND Инструменты = $3 AND instrumente = $4",
                            str(new_quantity1), chat_id, ru_tool_name, ro_tool_name
                        )
                        new_quantity = remaining_quantity - quantity
                        await connection.execute(
                            "UPDATE tools SET Осталось = $1 WHERE id = $2",
                            str(new_quantity), tool_id
                        )
                        tool_found = True
                        break  # No need to continue loop if tool is found

                if not tool_found:
                    # If tool is not found for the user, insert a new record
                    await connection.execute(
                        "INSERT INTO user_tool (Инструменты, Количество, chat_id, instrumente) VALUES ($1, $2, $3, $4)",
                        ru_tool_name, str(quantity), chat_id, ro_tool_name
                    )
                    new_quantity = remaining_quantity - quantity
                    await connection.execute(
                        "UPDATE tools SET Осталось = $1 WHERE id = $2",
                        str(new_quantity), tool_id
                    )

                chose_an_instrument = get_translation('ro', 'chose_an_instrument', tool_name=tool_name,
                                                      quantity=quantity) if language == 'ro' else get_translation('ru',
                                                                                                                  'chose_an_instrument',
                                                                                                                  tool_name=tool_name,
                                                                                                                  quantity=quantity)
                # Отправка подтверждения пользователю
                await callback_query.answer(chose_an_instrument)

                current_section = user_sections.get(chat_id, "tools")

                # Вывод меню инструментов в зависимости от текущего раздела
                if current_section == "tools":
                    await display_tools(callback_query.message, 1, 21)
                elif current_section == "accessories":
                    await display_tools(callback_query.message, 26, 103)
                elif current_section == "hand_tools":
                    await display_tools(callback_query.message, 107, 140)
                elif current_section == "personal_protection":
                    await display_tools(callback_query.message, 142, 153)
                elif current_section == "interior_tools":
                    await display_tools(callback_query.message, 155, 182)
            else:
                await callback_query.answer(insufficient_stock,
                                            show_alert=True)
        else:
            await callback_query.answer(tool_not_found, show_alert=True)

    await pool.close()


async def send_user_tools(message: types.Message):
    """Функция для отправки пользователю списка его инструментов в виде инлайн-кнопок."""
    user_id = message.chat.id  # Получение ID пользователя
    language = user_language_cache.get(user_id)
    registered_instruments = get_translation('ro', 'registered_instruments') if language == 'ro' else get_translation(
        'ru', 'registered_instruments')
    choose_tool = get_translation('ro', 'choose_tool') if language == 'ro' else get_translation('ru', 'choose_tool')
    # print('---------send_user_tools---------')
    # print('user_id-------->',user_id)
    # print('message-------->',message)
    # Получение данных из базы данных
    user_tool = await fetch_user_tools(user_id)

    # print('tools-------->',tools)

    # Если нет инструментов для пользователя
    if not user_tool:
        reply = await message.answer(registered_instruments)
        await handle_user_message(message)
        await handle_bot_message(message, reply)
        return

    # Создание инлайн-кнопок
    ru_keyboard_buttons = []
    ro_keyboard_buttons = []
    for tool in user_tool:
        if user_id == tool['chat_id']:
            if language == "ru":
                ru_keyboard_buttons.append(
                    [InlineKeyboardButton(text=tool['Инструменты'],
                                          callback_data=f"ret_tool:{tool['uuid']}")])
            else:
                ro_keyboard_buttons.append(
                    [InlineKeyboardButton(text=tool['instrumente'],
                                          callback_data=f"ret_tool:{tool['uuid']}")])

    lang_keyboard_buttons = ro_keyboard_buttons if language == 'ro' else ru_keyboard_buttons
    # Проверяем, если список кнопок пуст
    if not lang_keyboard_buttons:
        reply = await message.answer(registered_instruments)
        await handle_user_message(message)
        await handle_bot_message(message, reply)
        return

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=lang_keyboard_buttons)

    keyboard1 = message.reply_markup
    if keyboard1 and isinstance(keyboard1, InlineKeyboardMarkup):
        # Поиск кнопки с callback_data
        for row in keyboard1.inline_keyboard:
            for button in row:
                if button.callback_data == 'back_to_tools2':
                    await message.edit_text(choose_tool, reply_markup=keyboard)
    elif user_id:
        reply = await message.answer(choose_tool, reply_markup=keyboard)
        await handle_user_message(message)
        await handle_bot_message(message, reply)
    return keyboard


# Обработчик для выбора инструмента, который хочет вернуть
@router.callback_query(F.data.startswith('ret_tool:'))
async def process_tool_return(callback_query: types.CallbackQuery):
    # Получаем callback_data
    callback_data = callback_query.data
    chat_id = callback_query.message.chat.id
    print('callback_data--------->', callback_data)
    language = user_language_cache.get(chat_id)
    # Извлекаем uuid инструмента из callback_data
    tool_uuid = callback_data.split(':')[1]
    print('tool_uuid--------->', tool_uuid)

    # Теперь вы можете использовать tool_uuid для выполнения нужных действий.
    # Например, получить данные инструмента из базы данных по uuid.
    user_tool = await fetch_tool_by_uuid(tool_uuid)
    print(user_tool)

    if user_tool:
        ru_tool_name = user_tool['Инструменты']
        ro_tool_name = user_tool['instrumente']
        tool_quantity = user_tool['Количество']
        tool_name = ro_tool_name if language == 'ro' else ru_tool_name
        print("---------process_tool_return---------")
        print("tool_name---------", tool_name)
        await show_return_quantity_selection(callback_query.message, tool_uuid, tool_quantity, tool_quantity)

    # Оповещаем пользователя, что запрос обработан
    await callback_query.answer()


# Функция для отображения количества инструмента и кнопок увеличения/уменьшения для возврата
async def show_return_quantity_selection(message: types.Message, tool_uuid: str, tool_quantity,
                                         current_quantity: int = 1):
    # print("---------show_return_quantity_selection---------")
    # print("tool_name---------", tool_name)
    # print("tool_quantity---------", tool_quantity)
    # print("current_quantity---------\n", current_quantity)
    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    confirm = get_translation('ro', 'confirm') if language == 'ro' else get_translation('ru', 'confirm')
    back = get_translation('ro', 'back') if language == 'ro' else get_translation('ru', 'back')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"decrease_return:{tool_uuid}:{current_quantity}"),
            InlineKeyboardButton(text=f"{current_quantity}", callback_data="ignore"),
            InlineKeyboardButton(text="➕", callback_data=f"increase_return:{tool_uuid}:{current_quantity}")
        ],
        [InlineKeyboardButton(text=confirm, callback_data=f"confirm_return:{tool_uuid}:{current_quantity}")],
        [InlineKeyboardButton(text=back, callback_data=f"back_to_tools2")],

    ])

    user_tool = await fetch_tool_by_uuid(tool_uuid)
    ru_user_tool = user_tool['Инструменты']
    ro_user_tool = user_tool['instrumente']
    user_tool = ro_user_tool if language == 'ro' else ru_user_tool
    info_tool1 = get_translation('ro', 'info_tool1', tool_name=user_tool,
                                 tool_quantity=tool_quantity) if language == 'ro' else get_translation('ru',
                                                                                                       'info_tool1',
                                                                                                       tool_name=user_tool,
                                                                                                       tool_quantity=tool_quantity)
    # Инструмент: {tool_name}\nОсталось на складе: {tool_quantity}" f"\nВыберите количество инструмента
    await message.edit_text(info_tool1, reply_markup=keyboard, parse_mode=ParseMode.HTML)


# Обработчики для увеличения/уменьшения количества возвращаемого инструмента
@router.callback_query(
    lambda c: c.data and (c.data.startswith('increase_return:') or c.data.startswith('decrease_return:')))
async def change_return_quantity(callback_query: types.CallbackQuery):
    print(callback_query.data.split(':'))
    _, tool_uuid, current_quantity = callback_query.data.split(':')
    chat_id = callback_query.message.chat.id
    language = user_language_cache.get(chat_id)
    error0 = get_translation('ro', 'error0') if language == 'ro' else get_translation('ru', 'error0')
    error2 = get_translation('ro', 'error2') if language == 'ro' else get_translation('ru', 'error2')

    user_tool = await fetch_tool_by_uuid(tool_uuid)

    ru_tool_name = user_tool['Инструменты']
    ro_tool_name = user_tool['instrumente']
    tool_name = ro_tool_name if language == 'ro' else ru_tool_name
    tool_quantity = int(user_tool['Количество'])
    current_quantity = int(current_quantity)

    print("---------change_return_quantity---------")
    print("tool_name---------", tool_name)
    print("tool_quantity---------", tool_quantity)
    print("current_quantity---------", current_quantity)

    # Логика изменения количества
    if 'increase_return' in callback_query.data and current_quantity < tool_quantity:
        current_quantity += 1
        await show_return_quantity_selection(callback_query.message, tool_uuid, tool_quantity, current_quantity)
    elif 'decrease_return' in callback_query.data and current_quantity > 1:
        current_quantity -= 1
        await show_return_quantity_selection(callback_query.message, tool_uuid, tool_quantity, current_quantity)
    else:
        if current_quantity < tool_quantity:
            await callback_query.answer(error0,
                                        show_alert=True)
        elif current_quantity >= 1:
            await callback_query.answer(
                error2,
                show_alert=True)
    await callback_query.answer()


# Обработчик для подтверждения возврата
@router.callback_query(F.data.startswith('confirm_return:'))
async def confirm_tool_return(callback_query: types.CallbackQuery):
    _, tool_uuid, quantity = callback_query.data.split(':')
    quantity = int(quantity)
    chat_id = callback_query.message.chat.id
    language = user_language_cache.get(chat_id)

    user_tool = await fetch_tool_by_uuid(tool_uuid)
    ru_user_tool = user_tool['Инструменты']
    ro_user_tool = user_tool['instrumente']
    tool_name = ro_user_tool if language == 'ro' else ru_user_tool

    language = user_language_cache.get(chat_id)
    tool_not_found1 = get_translation('ro', 'tool_not_found1') if language == 'ro' else get_translation('ru',
                                                                                                        'tool_not_found1')
    tool_not_found = get_translation('ro', 'tool_not_found') if language == 'ro' else get_translation('ru',
                                                                                                      'tool_not_found')
    tool_return = get_translation('ro', 'tool_return') if language == 'ro' else get_translation('ru', 'tool_return')

    # Подключение к базе данных
    pool = await connect_to_db()
    async with pool.acquire() as connection:
        # Check if the tool exists in the database
        tool = await connection.fetchrow(
            "SELECT Инструменты, instrumente, Осталось FROM tools WHERE Инструменты = $1 OR instrumente = $1", tool_name
        )

        if tool:
            user_tool = await connection.fetchrow(
                "SELECT uuid, Количество FROM user_tool WHERE chat_id = $1 AND Инструменты = $2 OR instrumente = $2",
                chat_id, tool_name
            )
            # print('tool',tool)

            if user_tool:
                user_tool_quantity = int(user_tool['Количество'])
                remaining_quantity = int(tool['Осталось'])
                # print('user_tool', user_tool)
                # Update tool quantity in the main table
                new_quantity = remaining_quantity + quantity
                await connection.execute(
                    "UPDATE tools SET Осталось = $1 WHERE Инструменты = $2 OR instrumente = $2",
                    str(new_quantity), tool_name
                )

                if quantity >= user_tool_quantity:
                    # Remove the tool from user records if all are returned
                    await connection.execute(
                        "DELETE FROM user_tool WHERE uuid = $1",
                        user_tool['uuid']
                    )
                else:
                    # Update the user's tool quantity if only part is returned
                    new_user_quantity = user_tool_quantity - quantity
                    await connection.execute(
                        "UPDATE user_tool SET Количество = $1 WHERE uuid = $2",
                        str(new_user_quantity), user_tool['uuid']
                    )

                # Проверяем, есть ли еще зарегистрированные инструменты у пользователя
                tools = await fetch_user_tools(chat_id)

                if tools:
                    # Если у пользователя еще остались инструменты, отправляем обновленный список
                    await send_user_tools(callback_query.message)
                else:
                    # Если у пользователя не осталось инструментов, удаляем сообщение с выбором количества
                    await callback_query.message.delete()
                    main_menu_markup = rom_main_menu if language == 'ro' else main_menu
                    # Отправляем сообщение о том, что у него больше нет инструментов
                    reply = await callback_query.message.answer(tool_return, reply_markup=main_menu_markup)
                    await handle_bot_message(callback_query.message, reply)
            else:
                await callback_query.answer(tool_not_found1, show_alert=True)
        else:
            await callback_query.answer(tool_not_found, show_alert=True)

    await pool.close()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

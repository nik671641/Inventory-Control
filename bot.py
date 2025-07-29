import json
import random

from functions import *
from keyboard import *
import logging

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode

from datetime import timedelta
from config import TOKEN
from translations import get_translation
from datetime import datetime
from asyncpg import UniqueViolationError

# Включаем логирование
logging.basicConfig(level=logging.WARNING)

# Инициализируем бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

dp.include_router(router)
user_sections = {}
user_language_cache = {}
user_geo = {}

async def get_user_language(chat_id: int) -> str:
    if chat_id in user_language_cache:
        return user_language_cache[chat_id]

    pool = await connect_to_db()
    try:
        async with pool.acquire() as connection:
            user = await connection.fetchrow("SELECT language FROM id_users WHERE chat_id = $1", chat_id)
            language = user.get('language', 'ru') if user else None

        user_language_cache[chat_id] = language
    finally:
        # Закрытие пула соединений
        await pool.close()
    return language


async def fetch_geo_user(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
        SELECT name_project
        FROM warehouse 
        WHERE chat_id = $1;
    """
    try:
        rows = await conn.fetchrow(query, user_id)
        user_geo[user_id] = rows
    finally:
        await conn.close()


# Обработка команды /start
@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    chat_id = message.chat.id

    # Проверяем, существует ли пользователь в БД и является ли он администратором
    user = await fetch_admin_user_id(chat_id)

    if user and user.get('admin') == 'admin':
        # Если пользователь администратор
        logging.info("User is an admin.")
        language = await get_user_language(chat_id)  # Получаем язык администратора
        await handle_user_message(message)
        await handle_admin_user(message, language)

    else:
        if not user:
            # Если пользователя нет в базе данных, предлагаем выбрать язык
            logging.info("User is not in the database.")
            reply = await message.answer(get_translation('ru', 'language_prompt'), reply_markup=language_menu)

            await handle_bot_message(message, reply)

        else:
            # Если пользователь существует в базе данных, но не является администратором
            logging.info("User exists in the database but is not an admin.")
            language = await get_user_language(chat_id)

            # Если язык выбран, предлагаем выбрать проект стройки
            if language is not None:
                project_keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=project) for project in projects.keys()]],
                    resize_keyboard=True
                )
                reply = await message.answer("Selectați un proiect:", reply_markup=project_keyboard)

            else:
                # Если язык не выбран, предлагаем выбрать язык
                reply = await message.answer(get_translation('ru', 'language_prompt'), reply_markup=language_menu)

            await handle_user_message(message)
            await handle_bot_message(message, reply)


@router.message(lambda message: message.text in projects.keys())
async def handle_project_selection(message: types.Message):
    selected_project = message.text
    chat_id = message.chat.id 
    language = await fetch_admin_user_id(chat_id)

    ru_location_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить геолокацию", request_location=True)]], resize_keyboard=True)
    ro_location_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Trimiteți geolocalizarea", request_location=True)]], resize_keyboard=True)
    location_keyboard = ro_location_keyboard if language == 'ro' else ru_location_keyboard
    stroi_project = get_translation('ro', 'have_chosen_project',
                                    selected_project=selected_project) if language == 'ro' else get_translation('ru',
                                                                                                                'have_chosen_project',
                                                                                                                selected_project=selected_project)
    reply = await message.answer(stroi_project, reply_markup=location_keyboard)
    await handle_user_message(message)
    await handle_bot_message(message, reply)


# Основной обработчик геолокации
@router.message(F.content_type == types.ContentType.LOCATION)
async def handle_location(message: types.Message):
    user_latitude = message.location.latitude
    user_longitude = message.location.longitude
    chat_id = message.chat.id

    user = await fetch_admin_user_id(chat_id)
    language = await get_user_language(chat_id)

    # Извлекаем выбранный проект
    selected_project_text = message.reply_to_message.text.strip()
    selected_project = selected_project_text.split(" ")[-1]
    print("selected_project",selected_project)
    if selected_project not in projects:
        await message.answer("Ошибка: выбранный проект не найден. Пожалуйста, выберите проект еще раз.")
        return

    logging.info(f"Selected project: '{selected_project}'")

    # Проверяем местоположение пользователя относительно выбранного проекта
    is_within_project_radius = await check_user_location(user_latitude, user_longitude, selected_project)

    if is_within_project_radius:
        # Проверяем статус пользователя (админ или нет)

        if user:
            await handle_non_admin_user(message, language, selected_project)
            await add_geo(chat_id, selected_project)
            await fetch_geo_user(chat_id)
        else:
            # Если пользователь не найден в базе данных, предложите выбрать язык
            logging.info("User not found in database.")
            reply = await message.answer(get_translation('ru', 'language_prompt'), reply_markup=language_menu)
            await handle_bot_message(message, reply)

    else:
        project_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=project) for project in projects.keys()]],
                                               resize_keyboard=True)
        stroi_project_error = get_translation('ro', 'stroi_project_error', selected_project=selected_project) if language == 'ro' else get_translation(
            'ru', 'stroi_project_error', selected_project=selected_project)
        reply = await message.answer(stroi_project_error, reply_markup=project_keyboard)
        await handle_bot_message(message, reply)

    # Обрабатываем сообщение пользователя
    await handle_user_message(message)


@router.message(Command(commands=["menu"]))
async def cmd_menu(message: Message):

    chat_id = message.chat.id
    language = await get_user_language(chat_id)
    main_menu_markup = rom_main_menu if language == 'ro' else main_menu

    admin_menu = await fetch_chat_id_user(chat_id)
    choose_section = get_translation('ro', 'choose_section') if language == 'ro' else get_translation('ru',
                                                                                                      'choose_section')
    register = get_translation('ro', 'choose_a_publisher') if language == 'ro' else get_translation('ru',
                                                                                                    'choose_a_publisher')

    # Проверка наличия пользователя в базе данных
    geo = user_geo.get(chat_id)
    print(geo)
    if geo:
        user = await fetch_admin_user_id(chat_id)

        if user:
            user_id = user['admin']
            if user_id == 'admin':
                print("User is an admin")
                # Отправляем админское меню
                reply = await message.answer(register, reply_markup=admin_menu)
                await handle_user_message(message)
                await handle_bot_message(message, reply)

            else:
                print("User is not an admin")
                # Если пользователь не админ, отправляем обычное меню
                reply = await message.answer(choose_section, reply_markup=main_menu_markup)
                await handle_user_message(message)
                await handle_bot_message(message, reply)

        else:
            await error_user_geo(message, language)
    else:
        await error_user_geo(message, language)


@router.message(F.text.in_(["Русский", "Română"]))
async def handle_language_selection(message: Message):
    chat_id = message.chat.id
    selected_language = 'ru' if message.text == 'Русский' else 'ro'

    pool = await connect_to_db()

    try:
        async with pool.acquire() as connection:
            # Проверяем, есть ли пользователь в базе данных
            user = await connection.fetchrow("SELECT * FROM id_users WHERE chat_id = $1", chat_id)
            print("user", user)
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

                # Проверка на статус администратора
                if user['admin'] == 'admin':
                    print("User is an admin")
                    admin_menu = us_ro_markup if selected_language == 'ro' else us_ru_markup
                    register = get_translation('ro', 'register') if selected_language == 'ro' else get_translation('ru',
                                                                                                                   'register')
                    reply = await message.answer(register, reply_markup=admin_menu)
                else:
                    # Обновляем меню на выбранном языке
                    list_of_tools = get_translation('ro',
                                                    'choose_section') if selected_language == 'ro' else get_translation(
                        'ru', 'choose_section')
                    return_tools = rom_main_menu if selected_language == 'ro' else main_menu
                    reply = await message.answer(list_of_tools, reply_markup=return_tools)

            # Обновляем кэш языка
            user_language_cache[chat_id] = selected_language

        await handle_user_message(message)
        await handle_bot_message(message, reply)
    finally:
        # Закрываем пул соединений в любом случае
        await pool.close()


@router.message(F.content_type == 'web_app_data')
async def web_app(message: types.Message):
    chat_id = message.chat.id
    res = json.loads(message.web_app_data.data)
    pool = await connect_to_db()
    language = await get_user_language(chat_id)

    async with pool.acquire() as connection:
        # Проверка на статус администратора
        users = await fetch_admin_user_id(chat_id)
        if users and users['admin'] == 'admin':
            if res['name'] and res['surname']:
                # Генерация случайного числа до 15 цифр и вставка в базу данных
                while True:
                    random_number = random.randint(10 ** 14, 10 ** 15 - 1)  # Генерация 15-значного числа
                    try:
                        async with connection.transaction():
                            # Вставляем данные в таблицу chat_id_user
                            await connection.execute("""
                                INSERT INTO chat_id_user (chat_id, builder_number, Имя, Фамилия)
                                VALUES ($1, $2, $3, $4)
                            """, chat_id, str(random_number), res['name'], res['surname'])
                        break  # Успешно вставлено, выходим из цикла
                    except UniqueViolationError:
                        # Если возникает ошибка уникальности, генерируем новый random_number
                        continue

                print("User is an admin")
                choose_a_publisher = get_translation('ro',
                                                     'choose_a_publisher') if language == 'ro' else get_translation(
                    'ru',
                    'choose_a_publisher')
                keyboard = await fetch_chat_id_user(chat_id)
                reply = await message.answer(choose_a_publisher, reply_markup=keyboard)
                await handle_user_message(message)
                await handle_bot_message(message, reply)
            else:
                await message.answer('Error')
            # Ваш код для обработки данных веб-приложения администратором
        else:
            if res['builder'] and res['name'] and res['surname']:
                async with connection.transaction():
                    # Обновление данных в таблице id_users
                    await connection.execute("""
                        UPDATE id_users 
                        SET builder_number = $2, Имя = $3, Фамилия = $4
                        WHERE chat_id = $1
                    """, chat_id, res['builder'], res['name'], res['surname'])

                    language = user_language_cache.get(chat_id)
                    select_project = get_translation('ro',
                                                       'select_project') if language == 'ro' else get_translation(
                        'ru', 'select_project')
                    project_keyboard = ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text=project) for project in projects.keys()]],
                        resize_keyboard=True)
                    reply = await message.answer(select_project, reply_markup=project_keyboard)
                    await handle_user_message(message)
                    await handle_bot_message(message, reply)
            else:
                await message.answer('Error')

    await pool.close()


# Обработка кнопки "Взять инструмент"
@router.message(F.text.in_(["Взять инструмент", "Obține instrumentul"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    language = await get_user_language(chat_id)

    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu
    reply = await message.answer(get_translation(language, 'choose_section'), reply_markup=sections_menu_markup)

    await handle_user_message(message)
    await handle_bot_message(message, reply)



# Обработка кнопки "Вернуть инструмент"
@router.message(F.text.in_(["Вернуть инструмент", "Returnează instrumentul"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    await get_user_language(chat_id)
    await send_user_tools(message)


# Обработка кнопки "График работы"
@router.message(F.text.in_(["График работы", "Programul de lucru"]))
async def handle_take_tools(message: Message):
    logging.info("Handling 'График работы'")
    chat_id = message.chat.id
    language = await get_user_language(chat_id)
    working_time = ro_working_time if language == 'ro' else ru_working_time
    reply = await message.answer(get_translation(language, 'work_time_prompt2'),
                                 reply_markup=working_time)
    await handle_user_message(message)
    await handle_bot_message(message, reply)


@router.message(F.text.in_(["Выбрать язык", "Selectați o limbă"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    language = await get_user_language(chat_id)

    reply = await message.answer(get_translation(language, 'language_prompt'),
                                 reply_markup=language_menu)

    await handle_user_message(message)
    await handle_bot_message(message, reply)


@router.message(F.text.in_(["Список ваших инструментов", "O listă a uneltelor dvs"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    tools_list = []
    language = await get_user_language(chat_id)
    admin_user = await fetch_admin_user_id(chat_id)
    builder_number = user_builder_cache.get(chat_id)

    if admin_user['admin'] == 'admin':
        user_tools = await fetch_builder(builder_number)
    else:
        user_tools = await fetch_user_tools(chat_id)

    geo = user_geo.get(chat_id)
    if geo:
        if user_tools:
            for tool in user_tools:
                ru_tool_name = tool["Инструменты"]
                ro_tool_name = tool["instrumente"]
                quantity = tool["Количество"]
                tool_name = ro_tool_name if language == 'ro' else ru_tool_name

                # Формируем строку с информацией об инструменте
                tools_list.append(f"{tool_name}: {quantity}")

            return_all_button = InlineKeyboardButton(
                text=get_translation(language, 'return_all'),
                callback_data="return_all_tools"
            )

            # Создаем разметку с кнопкой возврата всех инструментов
            lang_keyboard_buttons = [[return_all_button]]
            keyboard = InlineKeyboardMarkup(inline_keyboard=lang_keyboard_buttons)

            list_of_tools = get_translation(language, 'list_of_tools') + "\n" + "\n".join(tools_list)

            # ReplyKeyboardMarkup
            back = ro_back if language == 'ro' else ru_back
            reply = await bot.send_message(chat_id, '📜', reply_markup=back)
            reply_0 = await bot.send_message(chat_id, list_of_tools, reply_markup=keyboard)
            # Отправляем сообщение пользователю
            await handle_user_message(message)
            await handle_bot_message(message, reply)
            await handle_bot_message(message, reply_0)
        else:
            # Сообщение, если нет инструментов
            no_tools_message = get_translation(language,
                                               'registered_instruments') 
            reply_no_tools = await bot.send_message(chat_id, no_tools_message)
            await handle_bot_message(message, reply_no_tools)
    else:
        await error_user_geo(message, language)


@router.message(F.text.in_(["Список инструментов", "Lista de instrumente"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    language = await get_user_language(chat_id)
    admin_user = await fetch_admin_user_id(chat_id)
    sections_menu_markup = us_ro_markup if language == 'ro' else us_ru_markup
    if admin_user['admin'] == 'admin':
        user_tools = await fetch_builder_all(chat_id)
        user_toolss = await fetch_user_tool_all(chat_id)
        print("fetch_builder_all", user_tools)
        print("fetch_user_tool_all", user_toolss)
    else:
        user_tools = await fetch_user_tools(chat_id)
        user_toolss = []  # Если не админ, не получаем user_toolss

    # Объединяем списки
    all_tools = user_tools + user_toolss

    grouped_tools = {}
    for tool in all_tools:
        full_name = f"{tool['Имя'].strip()} {tool['Фамилия'].strip()}"
        tool_name = tool['Инструменты'] if language == 'ru' else tool['instrumente']
        if full_name not in grouped_tools:
            grouped_tools[full_name] = []
        grouped_tools[full_name].append(f"{tool_name} {tool['Количество']}")

    # Формируем сообщение для отправки
    tool_list_message = ""
    for full_name, tools in grouped_tools.items():
        tool_list_message += f"\n<b>{full_name}</b>\n"  # Имя и фамилия
        tool_list_message += "\n".join(tools) + "\n"  # Инструменты и их количество

    # Отправляем сообщение пользователю через Telegram
    if tool_list_message:
        reply = await message.answer(tool_list_message, parse_mode=ParseMode.HTML, reply_markup=sections_menu_markup)
        await handle_bot_message(message, reply)

    # Если нет инструментов
    if not all_tools:
        no_tools_message = get_translation(language,
                                           'registered_instruments')
        reply_no_tools = await bot.send_message(chat_id, no_tools_message, reply_markup=sections_menu_markup)

        await handle_bot_message(message, reply_no_tools)
    await handle_user_message(message)


# Обработка кнопки "Список пользователей"
@router.message(F.text.in_(["Список пользователей", "Lista de utilizatori"]))
async def handle_take_tools(message: Message):
    chat_id = message.chat.id
    keyboard = await fetch_chat_id_user(chat_id)  # Получаем клавиатуру
    language = await get_user_language(chat_id)
    choose_a_publisher = get_translation('ro', 'choose_a_publisher') if language == 'ro' else get_translation(
        'ru',
        'choose_a_publisher'
    )

    reply = await message.answer(choose_a_publisher, reply_markup=keyboard)
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

    await display_tools(message, 1, 22)
    await handle_bot_message(message, reply)


# Обработка кнопки "Аксессуар для инструментов"
@router.message(F.text.in_(["Аксессуар для инструментов", "Accesoriu pentru scule"]))
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "accessories"

    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu
    reply = await message.answer("️🛠️", reply_markup=sections_menu_markup)

    await display_tools(message, 34, 62)
    await handle_bot_message(message, reply)


# Обработка кнопки "Ручной инструмент"
@router.message(F.text.in_(["Ручной инструмент", "Unelte de mână"]))
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "hand_tools"

    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu

    reply = await message.answer("🪛", reply_markup=sections_menu_markup)
    await display_tools(message, 75, 113)
    await handle_bot_message(message, reply)


# Обработка кнопки "Инструмент для внутренней отделки"
@router.message(F.text.in_(["Инструмент для внутренней отделки", "Instrument pentru finisare interioare"]))
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "interior_tools"

    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    sections_menu_markup = rom_sections_menu if language == 'ro' else sections_menu

    reply = await message.answer("🔨", reply_markup=sections_menu_markup)
    await display_tools(message, 123, 148)
    await handle_bot_message(message, reply)


@router.message(F.text.in_(
    ["Весь день", "До обеда", "Указать время работы", "Toată ziua", "Înainte de prânz", "Specify opening hours"]))
async def handle_working_time_selection(message: Message):
    chat_id = message.chat.id
    pool = await connect_to_db()
    language = user_language_cache.get(chat_id)
    message_text = message.text

    try:
        # Время окончания работы в зависимости от выбора пользователя
        if message.text == "Весь день" or message_text == "Toată ziua":
            end_time = datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
            await handle_user_message(message)
        elif message.text == "До обеда" or message_text == "Înainte de prânz":
            end_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
            await handle_user_message(message)
        else:
            print("3")
            # Просим пользователя ввести время в формате HH:MM
            end_time_input = get_translation(language, 'end_time_input')
            reply = await message.answer(end_time_input, reply_markup=time)
            await handle_user_message(message)
            await handle_bot_message(message, reply)
            return

        # Настраиваем уведомление за 30 минут до окончания работы
        notification_time = end_time - timedelta(minutes=30)

        # Сохраняем время окончания работы в базу данных
        async with pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO working_time (chat_id, Конец_работы, notification_time)
                VALUES ($1, $2, $3)
                ON CONFLICT (chat_id) 
                DO UPDATE SET Конец_работы = $2, notification_time = $3;
            """, chat_id, end_time, notification_time)

        ftime = end_time.strftime('%H:%M')
        end_time_set = get_translation(language, 'end_time_set', ftime=ftime)
        menu = rom_main_menu if language == 'ro' else main_menu
        # Напоминаем пользователю о возвращении инструментов за 30 минут до конца работы
        reply = await message.answer(end_time_set, reply_markup=menu)
        await handle_bot_message(message, reply)
        await schedule_reminder(message, chat_id, notification_time)
    except Exception as e:
        # Обработка исключений, например, логирование ошибки
        print(f"Error handling working time selection: {e}")
    finally:
        # Закрытие пула соединений в любом случае
        await pool.close()


# Функция для отправки уведомления пользователю
async def schedule_reminder(message: Message, chat_id, notification_time):
    time_until_notification = notification_time - datetime.now()
    language = user_language_cache.get(chat_id)
    working_time = rom_main_menu if language == 'ro' else main_menu

    # Если время для уведомления еще не наступило, ждем до его наступления
    if time_until_notification.total_seconds() > 0:
        await asyncio.sleep(time_until_notification.total_seconds())

    # Получаем список инструментов пользователя
    user_tools = await fetch_user_tools(chat_id)

    if user_tools:
        # Если время для уведомления еще не настало, ждем до его наступления

        # Создаем строку для вывода всех инструментов
        tools_list = []
        for tool in user_tools:
            ru_tool_name = tool["Инструменты"]
            ro_tool_name = tool["instrumente"]
            quantity = tool["Количество"]
            tool_name = ro_tool_name if language == 'ro' else ru_tool_name

            # Формируем строку с информацией об инструменте
            tools_list.append(f"{tool_name}: {quantity}")

        # Соединяем все строки и создаем напоминание
        reminder_message = get_translation(language, 'return_reminder') + "\n" + "\n".join(tools_list)

        # Отправляем сообщение пользователю
        reply = await bot.send_message(chat_id, reminder_message, reply_markup=working_time)
        await handle_bot_message(message, reply)

    else:
        # Если у пользователя нет инструментов, напоминаем о возврате
        reminder_message = get_translation(language, 'registered_instruments')
        reply = await bot.send_message(chat_id, reminder_message, reply_markup=working_time)
        await handle_bot_message(message, reply)


@router.message(F.text.regexp(r"\d{2}:\d{2}"))
async def handle_custom_working_time(message: Message):
    chat_id = message.chat.id
    pool = await connect_to_db()
    language = user_language_cache.get(chat_id)
    # Получаем введённое время от пользователя
    user_time = message.text
    try:
        end_time = datetime.strptime(user_time, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )

        # Настраиваем уведомление за 30 минут до окончания работы
        notification_time = end_time - timedelta(minutes=30)

        # Сохраняем время окончания работы в базу данных
        async with pool.acquire() as connection:
            await connection.execute("""
                       INSERT INTO working_time (chat_id, Конец_работы, notification_time)
                       VALUES ($1, $2, $3)
                       ON CONFLICT (chat_id) 
                       DO UPDATE SET Конец_работы = $2, notification_time = $3;
                   """, chat_id, end_time, notification_time)

        ftime = end_time.strftime('%H:%M')
        menu = rom_main_menu if language == 'ro' else main_menu
        end_time_set = get_translation(language, 'end_time_set', ftime=ftime)
        reply = await message.answer(end_time_set, reply_markup=menu)

        await handle_user_message(message)
        await handle_bot_message(message, reply)
        await schedule_reminder(message, chat_id, notification_time)

        # Напоминаем пользователю о возвращении инструментов за 30 минут до конца работы

    except ValueError:
        error_time_prompt = get_translation(language, 'error_time_prompt')
        reply = await message.answer(error_time_prompt)
        await handle_bot_message(message, reply)
    finally:
        await pool.close()


@router.message(F.text.in_(["Меню", "Meniu"]))
async def handle_back(message: Message):
    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    sections_menu_markup = us_ro_markup if language == 'ro' else us_ru_markup
    reply = await message.answer(get_translation(language, 'choose_section'), reply_markup=sections_menu_markup)
    await handle_user_message(message)
    await handle_bot_message(message, reply)


# Обработка кнопки "Назад"
@router.message(F.text.in_(["Назад", "Înapoi"]))
async def handle_back(message: Message):
    chat_id = message.chat.id
    language = user_language_cache.get(chat_id)
    user = await fetch_admin_user_id(chat_id)
    user_id = user['admin']
    if user_id == 'admin':
        print('1wew')
        start_message_text = get_translation('ro',
                                             'choose_section') if language == 'ro' else get_translation(
            'ru', 'choose_section')
        markup = rom_main_menu_2 if language == 'ro' else main_menu_2
        reply = await message.answer(start_message_text, reply_markup=markup)
        await handle_user_message(message)
        await handle_bot_message(message, reply)
    else:
        geo = user_geo.get(chat_id)
        if geo:
            print('2ere')
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
        else:
            await error_user_geo(message, language)


@router.callback_query(F.data == "back_to_tools")
async def handle_back_to_tools(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    current_section = user_sections.get(chat_id, "tools")  # Используем текущее состояние пользователя

    if current_section == "tools":
        await display_tools(callback_query.message, 1, 22)
    elif current_section == "accessories":
        await display_tools(callback_query.message, 34, 62)
    elif current_section == "hand_tools":
        await display_tools(callback_query.message, 75, 113)
    elif current_section == "interior_tools":
        await display_tools(callback_query.message, 123, 148)
    else:
        await callback_query.message.answer("ERROR", reply_markup=main_menu)

    await callback_query.answer()


@router.callback_query(F.data == "back_to_tools2")
async def handle_back_to_tools(callback_query: types.CallbackQuery):
    await send_user_tools(callback_query.message)


user_builder_cache = {}


@router.callback_query(F.data.startswith('user:'))
async def process_tool_choice(callback_query: types.CallbackQuery):
    logging.info(f"Callback query received: {callback_query.data}")
    message = callback_query.message

    _, builder_number = callback_query.data.split(":")
    chat_id = message.chat.id
    user_builder_cache[chat_id] = builder_number
    print("user_builder_cache", user_builder_cache)
    language = user_language_cache.get(chat_id)
    sections_menu_markup = rom_main_menu_2 if language == 'ro' else main_menu_2
    reply = await message.answer(get_translation(language, 'choose_section'), reply_markup=sections_menu_markup)

    await handle_user_message(message)
    await handle_bot_message(message, reply)


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

    elif text in ['Инструменты', 'Аксессуар для инструментов', 'Ручной инструмент', 'Средство личной защиты',
                  'Инструмент для внутренней отделки', 'Instrumente', 'Accesoriu pentru unelte', 'Unealtă manuală',
                  'Echipament de protecție individuală', 'Instrumente pentru decorațiuni interioare']:
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
    # Check if the new content or markup differs from the current content
    if message.text != info_tool or message.reply_markup != keyboard:
        # Only edit the message if content or markup is different
        await message.edit_text(info_tool, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        logging.info("Message content and markup are identical, skipping edit.")


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
    print('user_builder_cache2', user_builder_cache)
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
            "SELECT Инструменты, instrumente, Осталось FROM tools WHERE id = $1", tool_id)
        user_name = await connection.fetchrow(
            "SELECT Имя, Фамилия, admin FROM id_users WHERE chat_id = $1", chat_id)

        if tool:
            print('user_name', user_name)
            first_name = user_name['Имя']
            last_name = user_name['Фамилия']
            ru_tool_name = tool['Инструменты']
            ro_tool_name = tool['instrumente']
            remaining_quantity = int(tool['Осталось'])
            tool_name = ro_tool_name if language == 'ro' else ru_tool_name

            if user_name['admin'] != 'admin':
                print("32")
                message_to_send = get_translation(language, 'message_to_send', first_name=first_name,
                                                  last_name=last_name, tool_name=tool_name, quantity=quantity)
                target_chat_id = 5184928601  # укажите сюда нужный chat_id
                await bot.send_message(target_chat_id, message_to_send)
            else:
                print('fergegergegergergergergergeegeg')

            if remaining_quantity >= quantity:
                if user_name['admin'] == 'admin':
                    builder_number0 = user_builder_cache.get(chat_id)
                    builder_number = builder_number0
                    # Для администраторов ищем по builder_number
                    users = await connection.fetch(
                        "SELECT Инструменты, Количество, instrumente FROM user_tool WHERE builder_number = $1",
                        builder_number)
                else:
                    # Для обычных пользователей ищем по chat_id
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
                        if user_name['admin'] == 'admin':
                            await connection.execute(
                                "UPDATE user_tool SET Количество = $1 WHERE builder_number = $2 AND Инструменты = $3 AND instrumente = $4",
                                str(new_quantity1), builder_number, ru_tool_name, ro_tool_name
                            )
                        else:
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
                    if user_name['admin'] == 'admin':
                        await connection.execute(
                            "INSERT INTO user_tool (Инструменты, Количество, chat_id, builder_number, instrumente) VALUES ($1, $2, $3, $4, $5)",
                            ru_tool_name, str(quantity), chat_id, builder_number, ro_tool_name
                        )
                    else:
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
                    await display_tools(callback_query.message, 1, 22)
                elif current_section == "accessories":
                    await display_tools(callback_query.message, 34, 62)
                elif current_section == "hand_tools":
                    await display_tools(callback_query.message, 75, 113)
                elif current_section == "interior_tools":
                    await display_tools(callback_query.message, 123, 148)


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

    builder_number = user_builder_cache.get(user_id)
    admin_user = await fetch_admin_user_id(user_id)

    if admin_user['admin'] == 'admin':
        user_tool = await fetch_builder(builder_number)
    else:
        user_tool = await fetch_user_tools(user_id)

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

        # Добавляем кнопку "Вернуть весь инструмент"
    lang_keyboard_buttons.append(
        [InlineKeyboardButton(text=get_translation(language, 'return_all'), callback_data="return_all_tools")])

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
    # Извлекаем uuid инструмента из callback_data
    tool_uuid = callback_data.split(':')[1]

    # Теперь вы можете использовать tool_uuid для выполнения нужных действий.
    # Например, получить данные инструмента из базы данных по uuid.
    user_tool = await fetch_tool_by_uuid(tool_uuid)

    if user_tool:
        tool_quantity = user_tool['Количество']
        await show_return_quantity_selection(callback_query.message, tool_uuid, tool_quantity, tool_quantity)

    # Оповещаем пользователя, что запрос обработан
    await callback_query.answer()


@router.callback_query(F.data == 'return_all_tools')
async def handle_return_all_tools(callback_query: types.CallbackQuery):
    print('________handle_return_all_tools________')
    chat_id = callback_query.message.chat.id
    builder_number = user_builder_cache.get(chat_id)
    language = user_language_cache.get(chat_id)

    # Вызов функции возврата всех инструментов
    user_tools = await return_all_tools(chat_id, builder_number)
    admin_user = await fetch_admin_user_id(chat_id)

    tool_return = get_translation('ro', 'tool_return') if language == 'ro' else get_translation('ru', 'tool_return')
    no_tools_message = get_translation('ro', 'tool_not_found1') if language == 'ro' else get_translation('ru',
                                                                                                         'tool_not_found1')
    main_menu_0 = us_ro_markup if language == 'ro' else us_ru_markup
    main_menu_1 = rom_main_menu if language == 'ro' else main_menu

    if user_tools:
        print('user_tools', user_tools)
        if admin_user['admin'] == 'admin':
            reply = await callback_query.message.answer(tool_return, reply_markup=main_menu_0)
        else:
            print('else1')
            reply = await callback_query.message.answer(tool_return, reply_markup=main_menu_1)
        # Сообщаем пользователю об успешном возврате всех инструментов
    else:
        print('else2')
        # Сообщаем, что у пользователя нет инструментов для возврата
        reply = await callback_query.message.answer(no_tools_message)

    await handle_bot_message(callback_query.message, reply)
    await callback_query.answer()


# Функция для отображения количества инструмента и кнопок увеличения/уменьшения для возврата
async def show_return_quantity_selection(message: types.Message, tool_uuid: str, tool_quantity,
                                         current_quantity: int = 1):
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

    ru_user_tool = user_tool['Инструменты'].upper()
    ro_user_tool = user_tool['instrumente'].upper()
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
    print("callback_query.data.split", callback_query.data.split(':'))
    _, tool_uuid, current_quantity = callback_query.data.split(':')
    chat_id = callback_query.message.chat.id
    language = user_language_cache.get(chat_id)
    error0 = get_translation('ro', 'error0') if language == 'ro' else get_translation('ru', 'error0')
    error2 = get_translation('ro', 'error2') if language == 'ro' else get_translation('ru', 'error2')

    user_tool = await fetch_tool_by_uuid(tool_uuid)

    tool_quantity = int(user_tool['Количество'])
    current_quantity = int(current_quantity)

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
    builder_number = user_builder_cache.get(chat_id)

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
        is_admin = await connection.fetchrow(
            "SELECT Имя, Фамилия, admin FROM id_users WHERE chat_id = $1", chat_id)

        if tool:
            if is_admin['admin'] == 'admin':
                user_tool = await connection.fetchrow(
                    "SELECT uuid, Количество FROM user_tool WHERE builder_number = $1 AND (Инструменты = $2 OR instrumente = $2)",
                    builder_number, tool_name
                )
            else:
                user_tool = await connection.fetchrow(
                    "SELECT uuid, Количество FROM user_tool WHERE chat_id = $1 AND (Инструменты = $2 OR instrumente = $2)",
                    chat_id, tool_name
                )

            if user_tool:
                user_tool_quantity = int(user_tool['Количество'])
                remaining_quantity = int(tool['Осталось'])

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
                if is_admin['admin'] == 'admin':
                    print("43")
                    tools = await fetch_builder(builder_number)
                else:
                    print("32")
                    tools = await fetch_user_tools(chat_id)

                if tools:
                    # Если у пользователя еще остались инструменты, отправляем обновленный список
                    print("callback_query.message", callback_query.message)
                    await send_user_tools(callback_query.message)
                else:
                    # Если у пользователя не осталось инструментов, удаляем сообщение с выбором количества
                    await callback_query.message.delete()
                    if is_admin['admin'] == 'admin':
                        main_menu_markup = rom_main_menu_2 if language == 'ro' else main_menu_2
                    else:
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
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())

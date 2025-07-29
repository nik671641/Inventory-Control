import logging
import asyncpg
import asyncio
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import timedelta

from geoloc import projects, haversine

from config import DATABASE_URL, DB_CONFIG
from aiogram import types

from datetime import datetime

from keyboard import *
from translations import get_translation

# Список для хранения сообщений пользователей
user_messages = {}
# Список для хранения сообщений бота
bot_messages = {}
MAX_MESSAGES = 2

logging.basicConfig(level=logging.INFO)


# Обработчик для всех входящих сообщений от пользователей
async def handle_user_message(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in user_messages:
        user_messages[chat_id] = []

    # Сохраняем сообщение пользователя
    user_messages[chat_id].append({
        "message_id": message.message_id,
        "text": message.text
    })
    logging.info(f"User message saved: {message.text}")

    # Удаляем старые сообщения пользователя, если их количество превышает лимит
    await delete_old_messages(chat_id, user_messages[chat_id])


# Функция для обработки сообщений бота
async def handle_bot_message(message: types.Message, reply):
    chat_id = message.chat.id
    # Сохраняем сообщение бота
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    bot_messages[chat_id].append({
        "message_id": reply.message_id,
        "text": reply.text
    })

    # Удаляем старые сообщения бота, если их количество превышает лимит
    await delete_old_messages(chat_id, bot_messages[chat_id])


async def delete_old_messages(chat_id, messages):
    """Удаляет старые сообщения из чата, если их количество превышает лимит."""
    from bot import bot
    while len(messages) > MAX_MESSAGES:
        old_message = messages.pop(0)
        try:
            await bot.delete_message(chat_id, old_message['message_id'])
            logging.info(f"Deleted message {old_message['message_id']}")
        except Exception as e:
            logging.error(f"Failed to delete message {old_message['message_id']}: {e}")


async def delete_remaining_user_messages():
    """Функция для удаления всех оставшихся сообщений в словаре user_messages в конце дня."""
    from bot import bot  # Импортируем объект бота
    logging.info("Запуск удаления оставшихся сообщений...")
    for chat_id, messages in user_messages.items():
        for message in messages:
            try:
                await bot.delete_message(chat_id, message['message_id'])
                logging.info(f"Deleted message {message['message_id']} for chat_id {chat_id} from user_messages")
            except Exception as e:
                logging.error(
                    f"Failed to delete message {message['message_id']} for chat_id {chat_id} from user_messages: {e}")

        # Удаление сообщений из bot_messages
    for chat_id, messages in bot_messages.items():
        for message in messages:
            try:
                await bot.delete_message(chat_id, message['message_id'])
                logging.info(f"Deleted message {message['message_id']} for chat_id {chat_id} from bot_messages")
            except Exception as e:
                logging.error(
                    f"Failed to delete message {message['message_id']} for chat_id {chat_id} from bot_messages: {e}")
    # Очищаем словарь после удаления всех сообщений
    user_messages.clear()
    bot_messages.clear()


async def schedule_end_of_day_cleanup():
    """Функция планирует удаление сообщений в конце рабочего дня"""
    logging.info("Задача по очистке сообщений запущена.")

    now = datetime.now()
    end_of_day = now.replace(hour=23, minute=0, second=0, microsecond=0)

    # Если время до конца дня уже прошло, запланируем на следующий день
    if now > end_of_day:
        end_of_day += timedelta(days=1)

    # Рассчитываем, сколько осталось до конца дня
    time_until_cleanup = (end_of_day - now).total_seconds()
    logging.info(f"Ожидание до конца рабочего дня ({time_until_cleanup} секунд)...")
    # Ждем до конца рабочего дня
    await asyncio.sleep(time_until_cleanup)
    print('user_messages', user_messages)
    # Удаляем сообщения
    await delete_remaining_user_messages()




async def connect_to_db():
    return await asyncpg.create_pool(DATABASE_URL)


async def fetch_tool_by_uuid(tool_uuid):
    # Пример запроса к базе данных для получения данных инструмента по uuid
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        query = "SELECT * FROM user_tool WHERE uuid = $1"
        return await conn.fetchrow(query, tool_uuid)
    finally:
        # Закрытие соединения с базой данных в любом случае
        await conn.close()


async def fetch_admin_user_id(chat_id):
    # Пример запроса к базе данных для получения данных инструмента по uuid
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        if chat_id:
            query = "SELECT * FROM id_users WHERE chat_id = $1"
            rows = await conn.fetchrow(query, chat_id)
            return rows
    finally:
        await conn.close()


async def fetch_chat_id_user(chat_id):
    # Пример запроса к базе данных для получения данных инструмента по uuid
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        if chat_id:
            query = "SELECT * FROM chat_id_user WHERE chat_id = $1"
            users = await conn.fetch(query, chat_id)
            print("chat_users", users)

            keyboard_buttons = [
                [InlineKeyboardButton(text=f"{user['Имя']} {user['Фамилия']}",
                                      callback_data=f"user:{user['builder_number']}")
                 for user in users[i:i + 2]]
                for i in range(0, len(users), 2)
            ]

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            return keyboard

    finally:
        await conn.close()


async def return_all_tools(chat_id: int, builder_number: str = None):
    """Функция для возврата всех инструментов пользователя."""
    print('________return_all_tools________')

    pool = await connect_to_db()
    async with pool.acquire() as connection:
        # Определение, является ли пользователь администратором
        is_admin = builder_number is not None
        # Запрос для извлечения всех инструментов, взятых пользователем
        print('chat_id',chat_id)
        print('builder_number',builder_number)
        if is_admin:
            print('is_admin')

            user_tools = await connection.fetch(
                "SELECT uuid, Инструменты, instrumente, Количество FROM user_tool WHERE builder_number = $1",
                builder_number
            )
        else:
            print('else_')
            user_tools = await connection.fetch(
                "SELECT uuid, Инструменты, instrumente, Количество FROM user_tool WHERE chat_id = $1",
                chat_id
            )

        if user_tools:
            print('user_tools1', user_tools)
            # Обновляем количество инструментов в таблице `tools` и удаляем записи пользователя
            for tool in user_tools:
                tool_name_ru = tool['Инструменты']
                tool_name_ro = tool['instrumente']
                tool_quantity = int(tool['Количество'])

                # Обновляем количество в основной таблице
                await connection.execute(
                    """
                    UPDATE tools 
                    SET Осталось = (CAST(Осталось AS INTEGER) + $1)::varchar
                    WHERE Инструменты = $2 OR instrumente = $3
                    """,
                    tool_quantity, tool_name_ru, tool_name_ro
                )

                # Удаляем записи из таблицы user_tool
                await connection.execute(
                    "DELETE FROM user_tool WHERE uuid = $1",
                    tool['uuid']
                )
        else:
            return None
    await pool.close()
    return user_tools


# Функция для подключения к базе данных и получения списка инструментов
async def fetch_tools(start: int, end: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        rows = await conn.fetch(
            "SELECT id, Инструменты, instrumente, Осталось FROM tools WHERE id BETWEEN $1 AND $2 ORDER BY id;",
            start, end)
        return rows
    finally:
        await conn.close()


async def tools_quantity():
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        query = """
            SELECT id, Инструменты, Осталось
            FROM tools;
            """
        rows = await conn.fetchrow(query)
        return rows
    finally:
        await conn.close()


async def fetch_tools_quantity(tool_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        # Подключение к базе данных
        query = "SELECT id, Инструменты, instrumente, Осталось FROM tools WHERE id = $1;"
        # Возвращаем список инструментов с их количеством
        tool_quantity = await conn.fetchrow(query, tool_id)
        return tool_quantity
    finally:
        # Закрытие соединения с базой данных в любом случае
        await conn.close()


async def fetch_builder_all(chat_id):
    """Функция для извлечения инструментов и их количества для определенного пользователя."""
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
        SELECT chat_id_user.Имя, chat_id_user.Фамилия, user_tool.Инструменты, user_tool.instrumente, user_tool.Количество
        FROM user_tool
        JOIN chat_id_user ON user_tool.builder_number = chat_id_user.builder_number
        WHERE user_tool.chat_id = $1;
        """
    try:
        rows = await conn.fetch(query, chat_id)
        return rows
    finally:
        await conn.close()


async def fetch_user_tool_all(chat_id):
    """Функция для извлечения инструментов и их количества для определенного пользователя."""
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
        SELECT id_users.Имя, id_users.Фамилия, user_tool.Инструменты, user_tool.instrumente, user_tool.Количество
        FROM user_tool
        JOIN id_users ON user_tool.chat_id = id_users.chat_id
        WHERE user_tool.chat_id != $1
        ORDER BY user_tool.chat_id;
        """
    try:
        rows = await conn.fetch(query,chat_id)
        return rows
    finally:
        await conn.close()


async def fetch_builder(builder):
    """Функция для извлечения инструментов и их количества для определенного пользователя."""
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
        SELECT uuid, Инструменты, Количество, chat_id, instrumente
        FROM user_tool 
        WHERE builder_number = $1;
    """
    try:
        rows = await conn.fetch(query, builder)
        return rows
    finally:
        await conn.close()


async def fetch_user_tools(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
        SELECT uuid, Инструменты, Количество, chat_id, instrumente
        FROM user_tool 
        WHERE chat_id = $1;
    """
    try:
        rows = await conn.fetch(query, user_id)
        return rows
    finally:
        await conn.close()


async def delete_working_time(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = "DELETE FROM working_time WHERE chat_id = $1",
    try:
        rows = await conn.fetch(query, user_id)
        return rows
    finally:
        await conn.close()


async def add_geo(user_id, name_project):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
        INSERT INTO warehouse (chat_id, name_project)
        VALUES ($1, $2)
        ON CONFLICT (chat_id)
        DO UPDATE SET name_project = EXCLUDED.name_project;
    """
    try:
        rows = await conn.execute(query, user_id, name_project)
        return rows
    finally:
        await conn.close()


async def fetch_geo_user(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
        SELECT name_project
        FROM warehouse 
        WHERE chat_id = $1;
    """
    try:
        rows = await conn.fetch(query, user_id)
        return rows
    finally:
        await conn.close()


async def check_user_location(user_latitude, user_longitude, selected_project):
    """Проверяет, находится ли пользователь в пределах допустимого радиуса для выбранного проекта."""
    project_coords = projects[selected_project]
    distance = haversine(user_latitude, user_longitude, project_coords["latitude"], project_coords["longitude"])

    logging.info(f"Distance to project: {distance} meters, allowed radius: {project_coords['radius']} meters")

    return distance <= project_coords["radius"]


async def handle_admin_user(message, language):
    """Обрабатывает действия для администраторов."""
    register = get_translation('ro', 'register') if language == 'ro' else get_translation('ru', 'register')
    admin_menu = us_ro_markup if language == 'ro' else us_ru_markup

    reply = await message.answer(register, reply_markup=admin_menu)
    await handle_bot_message(message, reply)
    await schedule_end_of_day_cleanup()


async def handle_non_admin_user(message, language, selected_project):
    """Обрабатывает действия для обычных пользователей."""
    if language is None:
        reply = await message.answer(get_translation('ru', 'language_prompt'), reply_markup=language_menu)
    else:
        work_time_prompt = get_translation('ro', 'work_time_prompt') if language == 'ro' else get_translation('ru',
                                                                                                              'work_time_prompt')
        stroi_project = get_translation('ro', 'stroi_project', selected_project=selected_project) if language == 'ro' else get_translation('ru',
                                                                                                              'stroi_project', selected_project=selected_project)

        time_menu = ro_working_time if language == 'ro' else ru_working_time
        reply = await message.answer(stroi_project + "\n" +  "\n" + work_time_prompt, reply_markup=time_menu)

    await handle_bot_message(message, reply)


async def error_user_geo(message, language):

    stroi_project_error = get_translation('ro', 'stroi_project_error2') if language == 'ro' else get_translation(
        'ru', 'stroi_project_error2')
    reply = await message.answer(stroi_project_error, reply_markup=language_menu)
    await handle_bot_message(message, reply)
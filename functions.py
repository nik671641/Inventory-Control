import logging
import asyncpg


from bot import bot, types
from config import DATABASE_URL, DB_CONFIG



# Список для хранения сообщений пользователей
user_messages = {}
# Список для хранения сообщений бота
bot_messages = {}
MAX_MESSAGES = 2


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
    #
    print('--------------------handle_user_message--------------------')
    print('message_id', message.message_id)
    print('text', message.text)
    print('user_messages', user_messages, '\n')


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

    print('--------------------handle_bot_message--------------------')
    print('message_id_bot', reply.message_id)
    print('text_bot', reply.text)
    print('bot_messages', bot_messages, '\n')


async def delete_old_messages(chat_id, messages):
    """Удаляет старые сообщения из чата, если их количество превышает лимит."""
    while len(messages) > MAX_MESSAGES:
        old_message = messages.pop(0)
        try:
            await bot.delete_message(chat_id, old_message['message_id'])
            logging.info(f"Deleted message {old_message['message_id']}")
        except Exception as e:
            logging.error(f"Failed to delete message {old_message['message_id']}: {e}")


async def connect_to_db():
    return await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=10)


# Функция для подключения к базе данных и получения списка инструментов
async def fetch_tools(start: int, end: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        rows = await conn.fetch("SELECT id, Инструменты, Осталось FROM tools WHERE id BETWEEN $1 AND $2 ORDER BY id;",
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


async def fetch_tools_quantity():
    # Подключение к базе данных
    pool = await connect_to_db()

    async with pool.acquire() as connection:
        # Выполняем SQL-запрос для получения данных из таблицы tools
        query = "SELECT id, Инструменты, Осталось FROM tools WHERE id BETWEEN 1 AND 182 ORDER BY id;"
        rows = await connection.fetch(query)

        # Обрабатываем результаты запроса и формируем список
        tools = [{"tool_id": row["id"], "tool_name": row["Инструменты"], "quantity": row["Осталось"]} for row in rows]

    # Освобождаем ресурсы
    await pool.close()

    # Возвращаем список инструментов с их количеством
    return tools


# Функция для показа выбора количества


async def fetch_user_tools(user_id):
    """Функция для извлечения инструментов и их количества для определенного пользователя."""
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        query = """
        SELECT uuid, Инструменты, Количество, chat_id
        FROM user_tool 
        WHERE chat_id = $1;
        """
        rows = await conn.fetch(query, user_id)
        return rows
    finally:
        await conn.close()

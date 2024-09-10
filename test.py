import psycopg2

# Устанавливаем параметры подключения
conn = psycopg2.connect(
    dbname="postgres",  # Название вашей базы данных
    user="postgres",  # Имя пользователя
    password="Narzullo2045",  # Пароль
    host="localhost",  # Хост, например, "localhost"
    port="5432"  # Порт, стандартный порт для PostgreSQL — 5432
)

# Создаем курсор
cursor = conn.cursor()
select_query = "SELECT id_users.Имя, Фамилия, user_tool.Инструменты, Количество FROM id_users, user_tool WHERE id_users.chat_id=user_tool.chat_id"
cursor.execute(select_query)

# Получаем и выводим результаты
rows = cursor.fetchall()
for row in rows:
    print(row)

# Закрываем курсор и соединение
cursor.close()
conn.close()
# TIME_FORMAT = re.compile(r'^\d{2}:\d{2}$')

# Регистрируем роутер в диспетчере

# working_time = ReplyKeyboardMarkup(
#     keyboard=[
#         [KeyboardButton(text="Конец работы")],
#         [KeyboardButton(text="Изменить время работы")]
#     ],
#     resize_keyboard=True
#
# )

# # Обработка кнопки "Указать время работы"
# @router.message(F.text == "Указать время работы")
# async def handle_take_tools(message: Message):
#     logging.info("Handling 'Указать время работы'")
#     reply = await message.answer("Укажите время до скольки будете работать", reply_markup=working_time)
#     await handle_user_message(message)
#     await handle_bot_message(message, reply)


# # Обработчик кнопки "Конец работы"
# @router.message(F.text == "Конец работы")
# async def ask_end_time(message: Message):
#     reply = await message.answer("Пожалуйста, введите время конца работы (например, 17:00)")
#     await handle_user_message(message)
#     await handle_bot_message(message, reply)


# # Обработчик ввода времени конца работы
# @router.message(lambda message: TIME_FORMAT.match(message.text))  # Проверяем формат HH:MM
# async def save_start_time(message: Message):
#     chat_id = message.chat.id
#     start_time_str = message.text
#
#     # Преобразование строки в объект времени
#     try:
#         start_time = datetime.strptime(start_time_str, '%H:%M').time()
#     except ValueError:
#         reply = await message.answer("Неверный формат времени. Пожалуйста, введите время в формате HH:MM.")
#         await handle_user_message(message)
#         await handle_bot_message(message, reply)
#         return
#
#     # Подключение к базе данных
#     pool = await connect_to_db()
#     async with pool.acquire() as connection:
#         # Сохранение времени начала работы в БД
#         await connection.execute(
#             "INSERT INTO working_time (chat_id, Конец_работы) VALUES ($1, $2) "
#             "ON CONFLICT (chat_id) DO UPDATE SET Конец_работы = EXCLUDED.Конец_работы",
#             chat_id, start_time
#         )
#
#     # Ответ пользователю
#     reply = await message.answer(f"Конец работы установлено: {start_time_str}", reply_markup=working_time)
#     await handle_user_message(message)
#     await handle_bot_message(message, reply)
#
#     await pool.close()
#
# async def check_work_end_times():
#     while True:
#         # Подключение к базе данных
#         pool = await connect_to_db()
#         async with pool.acquire() as connection:
#             # Получение текущего времени
#             now = datetime.now()
#             current_time = now.time()
#
#             # Получение всех пользователей с указанным временем окончания работы
#             users = await connection.fetch("SELECT chat_id, Конец_работы FROM working_time")
#
#             for user in users:
#                 chat_id = user['chat_id']
#                 end_time = user['Конец_работы']
#
#                 # Вычисление разницы во времени
#                 end_datetime = datetime.combine(now.date(), end_time)
#                 reminder_time = end_datetime - timedelta(minutes=30)
#
#                 # Если текущее время больше или равно времени уведомления
#                 if current_time >= reminder_time.time() and current_time < end_time:
#                     await bot.send_message(
#                         chat_id,
#                         "Через 30 минут вам нужно вернуть все инструменты. Пожалуйста, подготовьтесь к завершению работы."
#                     )
#
#         await pool.close()
#         await asyncio.sleep(120)  # Проверять каждую минуту
#


#
#
# async def fetch_working_time():
#     pool = await connect_to_db()
#
#     async with pool.acquire() as connection:
#         # Выполняем SQL-запрос для получения данных из таблицы tools
#         query = "SELECT Начало_работы, Конец_работы, chat_id FROM working_time;"
#         rows = await connection.fetch(query)
#
#         # Обрабатываем результаты запроса и формируем список
#         tools = [{"opening_hours": row["Начало_работы"], "end_of_work": row["Конец_работы"], "chat_id": row["chat_id"]} for row in rows]
#
#     # Освобождаем ресурсы
#     await pool.close()
#
#     # Возвращаем список инструментов с их количеством
#     return tools
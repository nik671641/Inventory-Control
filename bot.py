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

# Включаем логирование
logging.basicConfig(level=logging.WARNING)

# Инициализируем бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

dp.include_router(router)
user_sections = {}

markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Зарегистрироваться", web_app=WebAppInfo(
    url="https://my-idea1.ru/"))]], resize_keyboard=True)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Взять инструмент"), KeyboardButton(text="Вернуть инструмент")],
        [KeyboardButton(text="Указать время работы"), KeyboardButton(text="Выбрать язык")]
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


# Обработка команды /start
@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    pool = await connect_to_db()

    async with pool.acquire() as connection:
        # Проверка наличия пользователя в базе данных
        user = await connection.fetchrow(
            "SELECT * FROM id_users WHERE chat_id = $1",
            chat_id
        )

        if user and chat_id:
            # Если пользователь уже существует, отправляем сообщение
            reply = await message.answer("Вы уже зарегистрированы в системе.\nВыберете раздел", reply_markup=main_menu)
            await handle_user_message(message)
            await handle_bot_message(message,reply)
        else:
            reply = await message.answer(f"Привет, {user_name}! Добро пожаловать на склад. Пожалуйста, Зарегистрируетесь!",
                                 reply_markup=markup)
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
                await connection.execute(
                    "INSERT INTO id_users (chat_id, builder_number, Имя, Фамилия) VALUES ($1, $2, $3, $4)",
                    chat_id, res['builder'], res['name'], res['surname']
                )
                reply = await message.answer(f"Выберите раздел",
                                     reply_markup=main_menu)
                await handle_bot_message(message,reply)
    else:
        reply = await message.answer(f"Пожалуйста введите все данные при регистрации",
                             reply_markup=markup, show_alert=True)
        await handle_bot_message(message, reply)

    # Освобождение ресурсов пула подключения
    await pool.close()


# Обработка кнопки "Взять инструмент"
@router.message(F.text == "Взять инструмент")
async def handle_take_tools(message: Message):
    logging.info("Handling 'Взять инструмент'")
    reply = await message.answer("Выберите раздел", reply_markup=sections_menu)
    await handle_user_message(message)
    await handle_bot_message(message, reply)

"fatal: Updating an unborn branch with changes added to the index."
# Обработка кнопки "Вернуть инструмент"
@router.message(F.text == "Вернуть инструмент")
async def handle_take_tools(message: Message):
    await send_user_tools(message)


# Обработка кнопки "Инструменты"
@router.message(F.text == "Инструменты")
async def table_tool(message: Message):
    user_sections[message.chat.id] = "tools"
    reply = await message.answer("🔨", reply_markup=sections_menu)
    await display_tools(message, 1, 21)
    await handle_bot_message(message, reply)


# Обработка кнопки "Аксессуар для инструментов"
@router.message(F.text == "Аксессуар для инструментов")
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "accessories"
    reply = await message.answer("️🛠️", reply_markup=sections_menu)
    await display_tools(message, 26, 103)
    await handle_bot_message(message, reply)


# Обработка кнопки "Ручной инструмент"
@router.message(F.text == "Ручной инструмент")
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "hand_tools"
    reply = await message.answer("🪛", reply_markup=sections_menu)
    await display_tools(message, 107, 140)
    await handle_bot_message(message, reply)


# Обработка кнопки "Средство личной защиты"
@router.message(F.text == "Средство личной защиты")
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "personal_protection"
    reply = await message.answer("⛑️", reply_markup=sections_menu)
    await display_tools(message, 142, 153)
    await handle_bot_message(message, reply)


# Обработка кнопки "Инструмент для внутренней отделки"
@router.message(F.text == "Инструмент для внутренней отделки")
async def tool_accessory(message: Message):
    user_sections[message.chat.id] = "interior_tools"
    reply = await message.answer("🔨", reply_markup=sections_menu)
    await display_tools(message, 155, 182)
    await handle_bot_message(message, reply)


# Обработка кнопки "Назад"
@router.message(F.text == "Назад")
async def handle_back(message: Message):
    reply = await message.answer("Выберите раздел", reply_markup=main_menu)
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
        await callback_query.message.answer("Выберите действие", reply_markup=main_menu)

    await callback_query.answer()


@router.callback_query(F.data == "back_to_tools2")
async def handle_back_to_tools(callback_query: types.CallbackQuery):
    await send_user_tools(callback_query.message)


async def display_tools(message: Message, start: int, end: int):
    logging.info("Fetching tools from database")
    text = message.text

    # Получаем список инструментов из базы данных
    tools = await fetch_tools(start, end)

    # Создаем список кнопок для клавиатуры, разделяя их на строки по 2 кнопки
    keyboard_buttons = [
        [InlineKeyboardButton(text=tool['Инструменты'], callback_data=f"tool:{tool['id']}:{tool['Осталось']}")
         for tool in tools[i:i + 2]]
        for i in range(0, len(tools), 2)
    ]

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    keyboard1 = message.reply_markup
    if keyboard1 and isinstance(keyboard1, InlineKeyboardMarkup):
        # Поиск кнопки с callback_data
        for row in keyboard1.inline_keyboard:
            for button in row:
                if button.callback_data == 'back_to_tools':
                    await message.edit_text("Выберите инструмент", reply_markup=keyboard)

    elif text == 'Инструменты' or 'Аксессуар для инструментов' or 'Ручной инструмент' or 'Средство личной защиты' or 'Инструмент для внутренней отделки':
        reply = await message.answer("Выберите инструмент", reply_markup=keyboard)
        await handle_user_message(message)
        await handle_bot_message(message, reply)
    return keyboard


# Обработчик для выбора инструмента (callback handler)
@router.callback_query(F.data.startswith('tool:'))
async def process_tool_choice(callback_query: types.CallbackQuery):
    logging.info(f"Callback query received: {callback_query.data}")
    # Разделяем callback_data и извлекаем ID инструмента и количество
    try:
        # Split the callback data by colon and extract tool_id and tool_quantity
        _, tool_id, tools_quantity = callback_query.data.split(":")
        tool_id = int(tool_id)
        tools_quantity = int(tools_quantity)
        # Показ количества и кнопок увеличения/уменьшения
        await show_quantity_selection(callback_query.message, tool_id, tools_quantity)
    except Exception as e:
        logging.error(f"Error processing callback query: {e}")


async def show_quantity_selection(message: Message, tool_id: int, tools_quantity: int, current_quantity: int = 1):
    # Создаем inline-кнопки для изменения количества

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"decrease:{tool_id}:{tools_quantity}:{current_quantity}"),
            InlineKeyboardButton(text=str(current_quantity), callback_data="ignore"),
            InlineKeyboardButton(text="➕", callback_data=f"increase:{tool_id}:{tools_quantity}:{current_quantity}")
        ],
        [InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm:{tool_id}:{current_quantity}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"back_to_tools")],

    ])
    tools = await fetch_tools_quantity()
    for tool in tools:
        if tool['tool_id'] == tool_id:
            await message.edit_text(
                f"Инструмент: {tool['tool_name'].upper()}\nОсталось на складе: {tool['quantity']}"
                f"\nВыберите количество инструмента",
                reply_markup=keyboard, parse_mode=ParseMode.HTML)


# Обработчики для увеличения/уменьшения количества
@router.callback_query(lambda c: c.data and (c.data.startswith('increase:') or c.data.startswith('decrease:')))
async def change_quantity(callback_query: types.CallbackQuery):
    _, tool_id, tools_quantity,  current_quantity = callback_query.data.split(':')
    current_quantity = int(current_quantity)
    tools_quantity = int(tools_quantity)

    if 'increase' in callback_query.data and current_quantity < tools_quantity:
        current_quantity += 1
        await show_quantity_selection(callback_query.message, int(tool_id), tools_quantity, current_quantity)
    elif 'decrease' in callback_query.data and current_quantity > 1:
        current_quantity -= 1
        await show_quantity_selection(callback_query.message, int(tool_id), tools_quantity, current_quantity)

    else:
        if current_quantity < tools_quantity:
            await callback_query.answer(f"ОШИБКА: Вы не можете выбрать 0 инструментов",
                                        show_alert=True)
        elif current_quantity >= 1:
            await callback_query.answer(
                f"ОШИБКА: Вы не можете выбрать инструментов больше чем имеется на складе",
                show_alert=True)


@router.callback_query(F.data.startswith('confirm:'))
async def confirm_choice(callback_query: types.CallbackQuery):
    _, tool_id, quantity = callback_query.data.split(':')
    tool_id = int(tool_id)
    quantity = int(quantity)
    chat_id = callback_query.message.chat.id

    # Подключение к базе данных
    pool = await connect_to_db()
    async with pool.acquire() as connection:
        # Проверка наличия инструмента в базе данных и получение текущего количества
        tool = await connection.fetchrow(
            "SELECT Инструменты, Осталось FROM tools WHERE id = $1", tool_id
        )
        if tool:
            tool_name = tool['Инструменты']
            remaining_quantity = int(tool['Осталось'])

            if remaining_quantity >= quantity:
                # Fetch all rows where chat_id matches the user's chat_id
                users = await connection.fetch(
                    "SELECT Инструменты, Количество FROM user_tool WHERE chat_id = $1",
                    chat_id
                )

                # Flag to check if tool is found for this user
                tool_found = False

                for user in users:
                    if user['Инструменты'] == tool_name:
                        new_quantity1 = quantity + int(user['Количество'])
                        await connection.execute(
                            "UPDATE user_tool SET Количество = $1 WHERE chat_id = $2 AND Инструменты = $3",
                            str(new_quantity1), chat_id, tool_name
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
                        "INSERT INTO user_tool (Инструменты, Количество, chat_id) VALUES ($1, $2, $3)",
                        tool_name, str(quantity), chat_id
                    )
                    new_quantity = remaining_quantity - quantity
                    await connection.execute(
                        "UPDATE tools SET Осталось = $1 WHERE id = $2",
                        str(new_quantity), tool_id
                    )

                # Отправка подтверждения пользователю
                await callback_query.answer(f"Вы выбрали инструмент {tool_name} в количестве {quantity}.")

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
                await callback_query.answer("Недостаточно инструмента на складе для выбранного количества.",
                                            show_alert=True)
        else:
            await callback_query.answer("Инструмент не найден.", show_alert=True)

    await pool.close()















async def send_user_tools(message: types.Message):
    """Функция для отправки пользователю списка его инструментов в виде инлайн-кнопок."""
    user_id = message.chat.id  # Получение ID пользователя

    # print('---------send_user_tools---------')
    # print('user_id-------->',user_id)
    # print('message-------->',message)
    # Получение данных из базы данных
    user_tool = await fetch_user_tools(user_id)

    # print('tools-------->',tools)

    # Если нет инструментов для пользователя
    if not user_tool:
        reply = await message.answer("У вас нет зарегистрированных инструментов.")
        await handle_user_message(message)
        await handle_bot_message(message, reply)
        return

    # Создание инлайн-кнопок
    keyboard_buttons = []
    for tool in user_tool:
        # print('tool---------', tool)
        print('tool[uuid]------------------------------------------------------------------------------------',tool['uuid'])
        if user_id == tool['chat_id']:
            keyboard_buttons.append(
                [InlineKeyboardButton(text=tool['Инструменты'],
                                      callback_data=f"ret_tool:{tool['uuid']}")])

    # Проверяем, если список кнопок пуст
    if not keyboard_buttons:
        reply = await message.answer("У вас нет зарегистрированных инструментов.")
        await handle_user_message(message)
        await handle_bot_message(message, reply)
        return

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    keyboard1 = message.reply_markup
    if keyboard1 and isinstance(keyboard1, InlineKeyboardMarkup):
        # Поиск кнопки с callback_data
        for row in keyboard1.inline_keyboard:
            for button in row:
                if button.callback_data == 'back_to_tools2':
                    await message.edit_text("Выберите инструмент", reply_markup=keyboard)
    elif user_id:
        reply = await message.answer("Выберите инструмент", reply_markup=keyboard)
        await handle_user_message(message)
        await handle_bot_message(message, reply)
    return keyboard


# Обработчик для выбора инструмента, который хочет вернуть
@router.callback_query(F.data.startswith('ret_tool:'))
async def process_tool_return(callback_query: types.CallbackQuery):
    # Получаем callback_data
    callback_data = callback_query.data
    print('callback_data--------->', callback_data)

    # Извлекаем uuid инструмента из callback_data
    tool_uuid = callback_data.split(':')[1]
    print('tool_uuid--------->', tool_uuid)

    # Теперь вы можете использовать tool_uuid для выполнения нужных действий.
    # Например, получить данные инструмента из базы данных по uuid.
    user_tool = await fetch_tool_by_uuid(tool_uuid)
    print(user_tool)

    if user_tool:
        tool_name = user_tool['Инструменты']
        tool_quantity = user_tool['Количество']

        print("---------process_tool_return---------")
        print("tool_name---------", tool_name)
        await show_return_quantity_selection(callback_query.message, tool_uuid, tool_quantity)

    # Оповещаем пользователя, что запрос обработан
    await callback_query.answer()


# Функция для отображения количества инструмента и кнопок увеличения/уменьшения для возврата
async def show_return_quantity_selection(message: types.Message, tool_uuid: str, tool_quantity, current_quantity: int = 1):
    # print("---------show_return_quantity_selection---------")
    # print("tool_name---------", tool_name)
    # print("tool_quantity---------", tool_quantity)
    # print("current_quantity---------\n", current_quantity)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"decrease_return:{tool_uuid}:{current_quantity}"),
            InlineKeyboardButton(text=f"{current_quantity}", callback_data="ignore"),
            InlineKeyboardButton(text="➕", callback_data=f"increase_return:{tool_uuid}:{current_quantity}")
        ],
        [InlineKeyboardButton(text="Продолжить", callback_data=f"confirm_return:{tool_uuid}:{current_quantity}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"back_to_tools2")],

    ])
    await message.edit_text(f"Выберите количество для возврата {tool_quantity}:", reply_markup=keyboard)


# Обработчики для увеличения/уменьшения количества возвращаемого инструмента
@router.callback_query(
    lambda c: c.data and (c.data.startswith('increase_return:') or c.data.startswith('decrease_return:')))
async def change_return_quantity(callback_query: types.CallbackQuery):
    print(callback_query.data.split(':'))
    _, tool_uuid, current_quantity = callback_query.data.split(':')

    user_tool = await fetch_tool_by_uuid(tool_uuid)

    tool_name = user_tool['Инструменты']
    tool_quantity = int(user_tool['Количество'])
    current_quantity = int(current_quantity)

    print("---------change_return_quantity---------")
    print("tool_name---------", tool_name)
    print("tool_quantity---------", tool_quantity)
    print("current_quantity---------", current_quantity)

    # Логика изменения количества
    if 'increase_return' in callback_query.data and current_quantity < tool_quantity:
        current_quantity += 1
        await show_return_quantity_selection(callback_query.message, tool_uuid, tool_quantity,current_quantity)
    elif 'decrease_return' in callback_query.data and current_quantity > 1:
        current_quantity -= 1
        await show_return_quantity_selection(callback_query.message, tool_uuid, tool_quantity,current_quantity)
    else:
        if current_quantity < tool_quantity:
            await callback_query.answer(f"ОШИБКА: Вы не можете выбрать 0 инструментов",
                                        show_alert=True)
        elif current_quantity >= 1:
            await callback_query.answer(
                f"ОШИБКА: Вы не можете выбрать инструментов больше чем имеется у вас",
                show_alert=True)
    await callback_query.answer()


# Обработчик для подтверждения возврата
@router.callback_query(F.data.startswith('confirm_return:'))
async def confirm_tool_return(callback_query: types.CallbackQuery):
    _, tool_uuid, quantity = callback_query.data.split(':')
    quantity = int(quantity)
    chat_id = callback_query.message.chat.id
    user_tool = await fetch_tool_by_uuid(tool_uuid)

    if user_tool:
        tool_name = user_tool['Инструменты']
        # Подключение к базе данных
        pool = await connect_to_db()
        async with pool.acquire() as connection:
            # Check if the tool exists in the database
            tool = await connection.fetchrow(
                "SELECT Инструменты, Осталось FROM tools WHERE Инструменты = $1", tool_name
            )

            if tool:
                user_tool = await connection.fetchrow(
                    "SELECT uuid, Количество FROM user_tool WHERE chat_id = $1 AND Инструменты = $2",
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
                        "UPDATE tools SET Осталось = $1 WHERE Инструменты = $2",
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

                    # Confirm to the user
                    await callback_query.answer(f"Вы успешно вернули {quantity} {tool_name} на склад.")
                    # Проверяем, есть ли еще зарегистрированные инструменты у пользователя
                    tools = await fetch_user_tools(chat_id)

                    if tools:
                        # Если у пользователя еще остались инструменты, отправляем обновленный список
                        await send_user_tools(callback_query.message)
                    else:
                        # Если у пользователя не осталось инструментов, удаляем сообщение с выбором количества
                        await callback_query.message.delete()
                        # Отправляем сообщение о том, что у него больше нет инструментов
                        reply = await callback_query.message.answer("Все инструменты были возвращены.\nВыберите раздел", reply_markup=main_menu)
                        await handle_bot_message(callback_query.message, reply)
                else:
                    await callback_query.answer("Инструмент не найден для возврата.", show_alert=True)
            else:
                await callback_query.answer("Инструмент не найден.", show_alert=True)

        await pool.close()


async def main():


    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


# import asyncio
# import math
# from aiogram import Bot, Dispatcher, types, Router, F
# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# from aiogram.filters import Command
# from geoloc import haversine
#
# from config import TOKEN
# import logging
#
# # Установите базовое конфигурирование для логирования
# logging.basicConfig(level=logging.INFO)
# # Данные для строительных проектов
# projects = {
#     "Straseni": {"latitude": 47.037518, "longitude": 28.774526, "radius": 300},
#     "Albisoara": {"latitude": 47.03617770637934, "longitude": 28.841908730215263, "radius": 300}
# }
#
#
# bot = Bot(token=TOKEN)
# dp = Dispatcher()
# router = Router()
#
# dp.include_router(router)
#
#
# @router.message(Command(commands=["start"]))
# async def send_welcome(message: types.Message):
#     # Запрашиваем выбор проекта
#     project_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=project) for project in projects.keys()]], resize_keyboard=True)
#     reply = await message.answer("Выберите проект:", reply_markup=project_keyboard)
#
#
# @router.message(lambda message: message.text in projects.keys())
# async def handle_project_selection(message: types.Message):
#     selected_project = message.text
#     location_keyboard = ReplyKeyboardMarkup(
#         keyboard=[[KeyboardButton(text="Отправить геолокацию", request_location=True)]], resize_keyboard=True)
#
#     await message.answer(
#         f"Вы выбрали {selected_project}",
#         reply_markup=location_keyboard)
#
#
# @router.message(F.content_type == types.ContentType.LOCATION)
# async def handle_location(message: types.Message):
#     user_latitude = message.location.latitude
#     user_longitude = message.location.longitude
#     print("user_latitude",user_latitude)
#     print("user_longitude",user_longitude)
#
#     # Извлекаем выбранный проект из текста предыдущего сообщения
#     selected_project_text = message.reply_to_message.text
#     selected_project = selected_project_text.split(" ")[-1]
#     print("selected_project_text",selected_project_text)
#     print("selected_project",selected_project)
#     if selected_project not in projects:
#         print("projects",projects)
#         await message.answer("Ошибка: выбранный проект не найден. Пожалуйста, выберите проект еще раз.")
#         return
#
#     logging.info(f"Полученный проект: '{selected_project}'")
#     project_coords = projects[selected_project]
#     print("project_coords",project_coords)
#
#     # Рассчитываем расстояние от пользователя до стройки
#     distance = haversine(user_latitude, user_longitude, project_coords["latitude"], project_coords["longitude"])
#     print("distance",distance)
#     print("project_coords[radius]",project_coords["radius"])
#     if distance <= project_coords["radius"]:
#         await message.answer(
#             f"Ваш доступ подтвержден к проекту {selected_project}. Вы находитесь на стройке (расстояние: {distance:.2f} метров)."
#         )
#         # Здесь можно предоставить доступ к функциональности бота
#     else:
#         await message.answer(
#             f"Извините, доступ запрещен. Вы находитесь слишком далеко от стройки {selected_project}"
#         )
#
# async def main():
#     await dp.start_polling(bot, skip_updates=True)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

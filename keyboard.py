from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo

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

us_ru_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Зарегистрировать пользователя", web_app=WebAppInfo(url="https://my-idea1.ru/admin/"))],
        [KeyboardButton(text="Список пользователей"), KeyboardButton(text="Список инструментов")],
        [KeyboardButton(text="Selectați o limbă")]
    ],
    resize_keyboard=True)

us_ro_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Înregistrați un utilizator", web_app=WebAppInfo(url="https://my-idea1.ru/admin/"))],
        [KeyboardButton(text="Lista de utilizatori"), KeyboardButton(text="Lista de instrumente")],
        [KeyboardButton(text="Выбрать язык")]
    ],
    resize_keyboard=True)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Взять инструмент"), KeyboardButton(text="Вернуть инструмент")],
        [KeyboardButton(text="График работы"), KeyboardButton(text="Выбрать язык")],
        [KeyboardButton(text="Список ваших инструментов")]
    ],
    resize_keyboard=True
)
main_menu_2 = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Взять инструмент"), KeyboardButton(text="Вернуть инструмент")],
        [KeyboardButton(text="Список ваших инструментов"), KeyboardButton(text="Меню")]
    ],
    resize_keyboard=True
)
rom_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Obține instrumentul"), KeyboardButton(text="Returnează instrumentul")],
        [KeyboardButton(text="Programul de lucru"), KeyboardButton(text="Selectați o limbă")],
        [KeyboardButton(text="O listă a uneltelor dvs")]
    ],
    resize_keyboard=True
)
rom_main_menu_2 = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Obține instrumentul"), KeyboardButton(text="Returnează instrumentul")],
        [KeyboardButton(text="O listă a uneltelor dvs"), KeyboardButton(text="Meniu")]
    ],
    resize_keyboard=True
)

sections_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Инструменты"), KeyboardButton(text="Аксессуар для инструментов")],
        [KeyboardButton(text="Ручной инструмент"), KeyboardButton(text="Инструмент для внутренней отделки")],
        [KeyboardButton(text="Назад")],

    ],
    resize_keyboard=True
)
rom_sections_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Instrumente"), KeyboardButton(text="Accesoriu pentru scule")],
        [KeyboardButton(text="Unelte de mână"), KeyboardButton(text="Instrument pentru finisare interioare")],
        [KeyboardButton(text="Înapoi")]
    ],
    resize_keyboard=True
)

ru_working_time = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Весь день"), KeyboardButton(text="До обеда")],
        [KeyboardButton(text="Указать время работы")]
    ],
    resize_keyboard=True

)
ro_working_time = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Toată ziua"), KeyboardButton(text="Înainte de prânz")],
        [KeyboardButton(text="Specify opening hours")]
    ],
    resize_keyboard=True
)
ru_back = ReplyKeyboardMarkup(
    keyboard=[

        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)
ro_back = ReplyKeyboardMarkup(
    keyboard=[

        [KeyboardButton(text="Înapoi")]
    ],
    resize_keyboard=True
)

time = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="09:00"), KeyboardButton(text="09:30"), KeyboardButton(text="10:00"),
         KeyboardButton(text="10:30")],
        [KeyboardButton(text="11:00"), KeyboardButton(text="11:30"), KeyboardButton(text="12:00"),
         KeyboardButton(text="13:00")],
        [KeyboardButton(text="13:30"), KeyboardButton(text="14:00"), KeyboardButton(text="14:30"),
         KeyboardButton(text="15:00")],
        [KeyboardButton(text="15:30"), KeyboardButton(text="16:00"), KeyboardButton(text="16:30"),
         KeyboardButton(text="17:00")],
    ],
    resize_keyboard=True
)

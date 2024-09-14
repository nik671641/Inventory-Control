


translations = {
    'ru': {
        'start_message': "Привет, {name}! Добро пожаловать на склад. Пожалуйста, Зарегистрируетесь!",
        'language_prompt': "Select a language:",
        'already_registered': "Вы уже зарегистрированы в системе.\nВыберете раздел",
        'registration_prompt': "Пожалуйста, Зарегистрируетесь!",
        'choose_section': "Выберите раздел",
        'choose_tool': "Выберите инструмент",
        'insufficient_stock': "Недостаточно инструмента на складе для выбранного количества.",
        'tool_return': "Все инструменты были возвращены.\nВыберите раздел",
        'tool_not_found1': "Инструмент не найден для возврата",
        'tool_not_found': "Инструмент не найден.",
        'confirm': "Подтвердить",
        'back': "Назад",
        'registered_instruments': "У вас нет зарегистрированных инструментов.",
        'chose_an_instrument': "Вы выбрали инструмент {tool_name} в количестве {quantity}.",
        'error0': "ОШИБКА: Вы не можете выбрать 0 инструментов",
        'error1': "ОШИБКА: Вы не можете выбрать инструментов больше чем имеется на складе",
        'error2': "ОШИБКА:  Вы не можете выбрать больше инструментов",
        'info_tool': "Инструмент: {tool_name}\nОсталось на складе: {tool_quantity}"
                f"\nВыберите количество инструмента",
        'info_tool1': "Инструмент: {tool_name}\nВыберите количество для возврата: {tool_quantity}",
        # Добавьте остальные переводы
    },
    'ro': {
        'start_message': "Bună ziua, {name}! Bine ați venit la depozit. Vă rugăm să vă înregistrați!",
        'language_prompt': "Alegeți limba în care doriți să utilizați bot:",
        'already_registered': "Sunteți deja înregistrat în sistem.\nAlegeți o secțiune",
        'registration_prompt': "Vă rugăm să vă înregistrați!",
        'choose_section': "Alegeți o secțiune",
        'choose_tool': "Alegeți un instrument",
        'insufficient_stock': "Stoc insuficient pentru cantitatea selectată",
        'tool_return': "Toate instrumentele au fost returnate.\nSelectați o secțiune",
        'tool_not_found1': "Instrumentul nu a fost găsit pentru returnare",
        'tool_not_found': "Instrumentul nu a fost găsit",
        'confirm': "Confirmați",
        'back': "Înapoi",
        'registered_instruments': "Nu aveți niciun instrument înregistrat.",
        'chose_an_instrument': "Ați selectat un instrument {tool_name} în cantitate {quantity}.",
        'error0': "ERROR: Nu puteți selecta 0 instrumente",
        'error1': "ERROR: Nu puteți selecta mai multe instrumente decât aveți în stoc",
        'error2': "ERROR: Nu puteți selecta mai multe instrumente ",
        'info_tool': "Instrument: {tool_name}\nRămase în stoc: {tool_quantity}"
                f"\nSelectați numărul de instrumente",
        'info_tool1': "Instrument: {tool_name}\nSelectați cantitatea care urmează să fie returnată: {tool_quantity}",

    }

}


def get_translation(language: str, key: str, **kwargs) -> str:
    return translations.get(language, {}).get(key, key).format(**kwargs)

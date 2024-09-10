# import psycopg2
# import pandas as pd
# from config import DB_CONFIG
#
# # Путь к файлу Excel
# excel_file = 'Список_всех_инструментов.xlsx'
#
# # Имя таблицы, в которую нужно загрузить данные
# table_name = 'tools'
#
# try:
#     # Чтение данных из Excel файла с помощью pandas
#     df = pd.read_excel(excel_file)
#
#     # Подключение к базе данных PostgreSQL
#     conn = psycopg2.connect(**DB_CONFIG)
#     cursor = conn.cursor()
#
#     # Получаем список колонок за исключением 'id'
#     columns = ', '.join([col for col in df.columns if col != 'id'])
#     values = ', '.join(['%s' for _ in range(len(df.columns) - 1)])  # Количество %s должно быть равно количеству колонок за исключением 'id'
#     insert_query = f'INSERT INTO {table_name} ({columns}) VALUES ({values})'
#
#     # Итерация по строкам DataFrame и вставка каждой строки в таблицу
#     for row in df.itertuples(index=False):
#         # Исключаем значение поля 'id' из вставляемых данных
#         cursor.execute(insert_query, tuple(row[1:]))  # Пропускаем первый элемент 'id'
#
#     # Подтверждение транзакции
#     conn.commit()
#
#     print("Данные успешно загружены в таблицу PostgreSQL")
#
# except Exception as e:
#     print(f"Ошибка: {e}")
#
# finally:
#     # Закрытие курсора и соединения с базой данных
#     if cursor:
#         cursor.close()
#     if conn:
#         conn.close()


import psycopg2
import pandas as pd
from config import DB_CONFIG

# Путь к файлу Excel
excel_file = 'Список_всех_инструментов.xlsx'

# Имя таблицы, в которую нужно загрузить данные
table_name = 'tools'

try:
    # Чтение данных из Excel файла с помощью pandas
    df = pd.read_excel(excel_file)

    # Удаляем столбец 'id' из DataFrame, если он существует
    if 'id' in df.columns:
        df.drop(columns=['id'], inplace=True)

    # Подключение к базе данных PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Получаем список колонок и количество значений для вставки
    columns = ', '.join(df.columns)
    values = ', '.join(['%s' for _ in df.columns])  # Количество %s должно соответствовать количеству колонок
    insert_query = f'INSERT INTO {table_name} ({columns}) VALUES ({values})'

    # Итерация по строкам DataFrame и вставка каждой строки в таблицу
    for row in df.itertuples(index=False):
        cursor.execute(insert_query, tuple(row))

    # Подтверждение транзакции
    conn.commit()

    print("Данные успешно загружены в таблицу PostgreSQL")

except Exception as e:
    print(f"Ошибка: {e}")

finally:
    # Закрытие курсора и соединения с базой данных
    if cursor:
        cursor.close()
    if conn:
        conn.close()

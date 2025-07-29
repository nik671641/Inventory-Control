import psycopg2
import pandas as pd
from config import DB_CONFIG

# Путь к файлу Excel
excel_file = 'Список_всех_инструментов.xlsx'

# Имя таблицы, в которую нужно загрузить данные
table_name = 'tools'

# Подключение к базе данных PostgreSQL
try:
    # Чтение данных из Excel файла с помощью pandas
    df = pd.read_excel(excel_file)

    # Подключение к базе данных PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Подготовка строки запроса для вставки данных
    columns = ', '.join(df.columns)
    values = ', '.join(['%s' for _ in df.columns])
    insert_query = f'INSERT INTO {table_name} ({columns}) VALUES ({values})'

    # Итерация по строкам DataFrame и вставка каждой строки в таблицу
    for index, row in df.iterrows():
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


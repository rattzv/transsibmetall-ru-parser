import json
import os
import sqlite3

from utils.utils import print_template

FILENAME = "transsibmetallru"


def remove_old_data(reports_folder):
    report_file_sqlite = os.path.join(reports_folder, 'sqlite', f'{FILENAME}.sqlite')
    report_file_json = os.path.join(reports_folder, 'json', 'products.json')
    try:
        if os.path.exists(report_file_sqlite):
            print_template(f"Remove old data {report_file_sqlite}...")
            os.remove(report_file_sqlite)

        if os.path.exists(report_file_json):
            print_template(f"Remove old data {report_file_json}...")
            os.remove(report_file_json)

    except:
        print_template(f"Error when deleting old file")


def save_to_sqlite(products, reports_folder):
    try:
        report_file = os.path.join(reports_folder, 'sqlite', FILENAME)

        conn = sqlite3.connect(report_file + ".sqlite")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS json_data (id INTEGER PRIMARY KEY, data TEXT)''')

        for product in products:
            try:
                data = json.dumps(product, ensure_ascii=False, indent=4)
                cursor.execute("INSERT INTO json_data (data) VALUES (?)", (data,))
            except:
                continue
        conn.commit()
    except:
        return False


def convert_to_json(reports_folder):
    """
    Конвертирует данные из файлов базы данных SQLite в файлы JSON.
    Args:
        reports_folder (str): Путь к папке, где хранятся файлы отчетов.
    Returns:
        None
    """

    try:
        total = 0
        sqlite_report_file = os.path.join(reports_folder, 'sqlite', f'{FILENAME}.sqlite')

        if not os.path.exists(sqlite_report_file):
            print_template(f"Error: sqlite database file does not exist ({sqlite_report_file})")
            return False

        json_report_file = os.path.join(reports_folder, 'json', 'products.json')

        conn = sqlite3.connect(sqlite_report_file)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM json_data")
        rows = cursor.fetchall()
        conn.close()

        data_list = []

        for row in rows:
            try:
                data_list.append(json.loads(row[0]))
            except:
                continue

        total += len(data_list)

        print_template(f"Convert to json {sqlite_report_file}...")
        with open(json_report_file, 'w', encoding="utf-8") as file:
            json.dump(data_list, file, ensure_ascii=False, indent=4)
    except:
        print_template(f"Error converting sqlite database to json :(")
        return False
    return total

import mysql.connector

# Подключение к базе данных
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",  # Замените на свой пароль
    database="botanical_db"
)

cursor = db.cursor()

# Создание таблиц
def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS taxonomy (
            id INT AUTO_INCREMENT PRIMARY KEY,
            family VARCHAR(100),
            genus VARCHAR(100),
            species VARCHAR(100)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name_ru VARCHAR(255),
            name_lat VARCHAR(255),
            description TEXT,
            taxonomy_id INT,
            FOREIGN KEY (taxonomy_id) REFERENCES taxonomy(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            table_name VARCHAR(50),
            action_type VARCHAR(10),
            record_id INT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()

# Логирование действий
def log_audit(table_name, action_type, record_id, content):
    cursor.execute(
        "INSERT INTO audit_log (table_name, action_type, record_id, content) VALUES (%s, %s, %s, %s)",
        (table_name, action_type, record_id, content)
    )
    db.commit()

# Добавление растения
def add_plant():
    family = input("Семейство: ")
    genus = input("Род: ")
    species = input("Вид: ")
    name_ru = input("Русское название: ")
    name_lat = input("Латинское название: ")
    description = input("Описание: ")

    cursor.execute("INSERT INTO taxonomy (family, genus, species) VALUES (%s, %s, %s)", (family, genus, species))
    taxonomy_id = cursor.lastrowid
    log_audit("taxonomy", "INSERT", taxonomy_id, f"{family} / {genus} / {species}")

    cursor.execute("INSERT INTO plants (name_ru, name_lat, description, taxonomy_id) VALUES (%s, %s, %s, %s)",
                   (name_ru, name_lat, description, taxonomy_id))
    plant_id = cursor.lastrowid
    log_audit("plants", "INSERT", plant_id, f"{name_ru} / {name_lat} / {description}")

    db.commit()
    print("✅ Растение добавлено.")

# Просмотр всех растений
def list_plants():
    cursor.execute("""
        SELECT p.id, p.name_ru, p.name_lat, t.family, t.genus, t.species
        FROM plants p
        JOIN taxonomy t ON p.taxonomy_id = t.id
    """)
    plants = cursor.fetchall()
    if not plants:
        print("🔍 Записей нет.")
    for row in plants:
        print(f"[{row[0]}] {row[1]} ({row[2]}) — {row[3]} / {row[4]} / {row[5]}")

# Поиск растения
def search_plant():
    keyword = input("Введите название (русское или латинское): ")
    cursor.execute("""
        SELECT p.id, p.name_ru, p.name_lat, p.description
        FROM plants p
        WHERE p.name_ru LIKE %s OR p.name_lat LIKE %s
    """, (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    if not results:
        print("🔍 Ничего не найдено.")
    for row in results:
        print(f"[{row[0]}] {row[1]} ({row[2]})\nОписание: {row[3]}\n")

# Обновление описания
def update_plant():
    plant_id = input("ID растения для обновления: ")
    new_desc = input("Новое описание: ")
    cursor.execute("UPDATE plants SET description = %s WHERE id = %s", (new_desc, plant_id))
    log_audit("plants", "UPDATE", plant_id, f"Новое описание: {new_desc}")
    db.commit()
    print("✏️ Описание обновлено.")

# Удаление растения
def delete_plant():
    plant_id = input("ID растения для удаления: ")
    cursor.execute("SELECT name_ru, name_lat FROM plants WHERE id = %s", (plant_id,))
    result = cursor.fetchone()
    if result:
        name_ru, name_lat = result
        log_audit("plants", "DELETE", plant_id, f"{name_ru} / {name_lat}")
    cursor.execute("DELETE FROM plants WHERE id = %s", (plant_id,))
    db.commit()
    print("🗑️ Растение удалено.")

# Добавление пробных данных
def insert_sample_data():
    samples = [
        {
            "family": "Betulaceae",
            "genus": "Betula",
            "species": "pendula",
            "name_ru": "Берёза повислая",
            "name_lat": "Betula pendula",
            "description": "Лиственное дерево, распространённое в Европе и Азии."
        },
        {
            "family": "Pinaceae",
            "genus": "Pinus",
            "species": "sylvestris",
            "name_ru": "Сосна обыкновенная",
            "name_lat": "Pinus sylvestris",
            "description": "Хвойное дерево, характерное для хвойных лесов Европы и Азии."
        },
        {
            "family": "Asteraceae",
            "genus": "Taraxacum",
            "species": "officinale",
            "name_ru": "Одуванчик лекарственный",
            "name_lat": "Taraxacum officinale",
            "description": "Многолетнее растение с жёлтыми цветками и глубоким корнем."
        }
    ]

    for plant in samples:
        cursor.execute(
            "INSERT INTO taxonomy (family, genus, species) VALUES (%s, %s, %s)",
            (plant["family"], plant["genus"], plant["species"])
        )
        taxonomy_id = cursor.lastrowid
        log_audit("taxonomy", "INSERT", taxonomy_id, f"{plant['family']} / {plant['genus']} / {plant['species']}")

        cursor.execute(
            "INSERT INTO plants (name_ru, name_lat, description, taxonomy_id) VALUES (%s, %s, %s, %s)",
            (plant["name_ru"], plant["name_lat"], plant["description"], taxonomy_id)
        )
        plant_id = cursor.lastrowid
        log_audit("plants", "INSERT", plant_id, f"{plant['name_ru']} / {plant['name_lat']} / {plant['description']}")

    db.commit()
    print("✅ Пробные растения добавлены.")

def view_audit_log():
    cursor.execute("""
        SELECT id, table_name, action_type, record_id, content, timestamp
        FROM audit_log
        ORDER BY timestamp DESC
        LIMIT 100
    """)
    logs = cursor.fetchall()
    if not logs:
        print("🕵️ Журнал аудита пуст.")
    else:
        print("\n📑 Журнал аудита (последние изменения):")
        for log in logs:
            print(f"[{log[0]}] [{log[5]}] {log[1]} - {log[2]} (ID: {log[3]})")
            print(f"     → {log[4]}")

# Основное меню
def main():
    init_db()
    while True:
        print("\n📚 Ботанический справочник")
        print("1. Добавить растение")
        print("2. Показать все растения")
        print("3. Поиск по названию")
        print("4. Обновить описание")
        print("5. Удалить растение")
        print("6. Добавить пробные данные")
        print("7. Выход")
        print("8. Просмотреть журнал аудита")
        choice = input("Выбор: ")
        if choice == "1":
            add_plant()
        elif choice == "2":
            list_plants()
        elif choice == "3":
            search_plant()
        elif choice == "4":
            update_plant()
        elif choice == "5":
            delete_plant()
        elif choice == "6":
            insert_sample_data()
        elif choice == "7":
            print("👋 Завершение работы.")
            break
        elif choice == "8":
            view_audit_log()
        else:
            print("⚠️ Неверный ввод.")


if __name__ == "__main__":
    main()

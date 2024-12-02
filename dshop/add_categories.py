import psycopg2

def add_categories(connection_string, categories):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()

        for category in categories:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s)",
                (category,)
            )

        connection.commit()
        print("Categories added successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    connection_string = 'dbname=catalog_db user=postgres password=1234 host=localhost'
    categories = ["Гаджеты", "Часы", "Смартфоны", "Ноутбуки", "ПК", "Телевизоры", "Техника"]
    add_categories(connection_string, categories)

import psycopg2

def drop_all_tables(connection_string):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()

        # Получение списка всех таблиц в базе данных
        cursor.execute(
            """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
            """
        )
        tables = cursor.fetchall()

        # Удаление всех таблиц
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DROP TABLE {table_name} CASCADE;")

        connection.commit()
        print("All tables dropped successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    connection_string = 'dbname=catalog_db user=postgres password=1234 host=localhost'
    drop_all_tables(connection_string)

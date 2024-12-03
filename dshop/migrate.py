import os
from controller import ApplicationController

# Используйте переменную окружения для строки подключения к базе данных
connection_string = os.getenv('DATABASE_URL', 'dbname=catalog_db user=postgres password=1234 host=db port=5432')
app_controller = ApplicationController(connection_string)

# Выполните миграции
app_controller.run_migrations()

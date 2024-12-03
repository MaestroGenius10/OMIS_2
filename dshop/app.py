from controller import ApplicationController
from flask import *
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Используйте переменную окружения для строки подключения к базе данных
connection_string = os.getenv('DATABASE_URL', 'dbname=catalog_db user=postgres password=1234 host=db port=5432')
app_controller = ApplicationController(connection_string)

app_controller.setup_routes(app)

# Запускаем приложение
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

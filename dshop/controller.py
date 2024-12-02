from model import *
from flask import *
from view import *
from datetime import datetime
import os
from werkzeug.utils import secure_filename
class ApplicationController:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.user_service = UserService(self.connection_string)
        self.authentication_service = AuthenticationService(self.connection_string)
        self.goods_service = GoodsService(self.connection_string)
        self.payment_card_service = PaymentCardService(self.connection_string)
        self.cart_service = CartService(self.connection_string)
        self.order_service = OrderService(self.connection_string)

        self.user_controller = UserController(self.user_service)
        self.authentication_controller = AuthenticationController(self.authentication_service, self.user_service, self.cart_service)
        self.goods_controller = GoodsController(self.goods_service, self.order_service, self.user_controller)
        self.payment_card_controller = PaymentCardController(self.payment_card_service, self.user_service)
        self.personal_data_controller = PersonalDataController(self.user_service)
        self.cart_controller = CartController(self.cart_service)
        self.order_controller = OrderController(self.order_service, self.cart_service, self.payment_card_service)

    def setup_routes(self, app):
        self.authentication_controller.setup_routes(app)
        self.goods_controller.setup_routes(app)
        self.payment_card_controller.setup_routes(app)
        self.personal_data_controller.setup_routes(app)
        self.cart_controller.setup_routes(app)
        self.order_controller.setup_routes(app)
class UserController:
    def __init__(self, user_service):
        self.user_service = user_service

    def get_user_by_email(self, email):
        return self.user_service.get_user_by_email(email)

    def get_user_by_id(self, user_id):
        return self.user_service.get_user_by_id(user_id)

    def delete_user_by_email(self, email):
        self.user_service.delete_user_by_email(email)

    def delete_user_by_id(self, user_id):
        self.user_service.delete_user_by_id(user_id)

    def save_user(self, name, email, password_hash, profile_picture=None, birth_date=None):
        self.user_service.save_user(name, email, password_hash, profile_picture, birth_date)

    def find_all_users(self):
        return self.user_service.find_all_users()
class AuthenticationController:
    def __init__(self, authentication_service, user_service, cart_service):
        self.authentication_service = authentication_service
        self.user_service = user_service
        self.cart_service = cart_service
        self.user_interface = UserInterface()

    def register_user(self, name, email, password):
        self.authentication_service.register_user(name, email, password)

    def login_user(self, email, password):
        return self.authentication_service.login_user(email, password)

    def get_register_page(self):
        return self.user_interface.get_register_page()

    def get_login_page(self):
        return self.user_interface.get_login_page()

    def profile(self):
        user_id = session.get('user_id')
        user = self.user_service.get_user_by_id(user_id)
        if user:
            user_info = {
                'name': user[1],
                'profile_picture': user[4]
            }
            return self.user_interface.get_profile_page(user_info)

    def change_password(self):
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user_id = session.get('user_id')

        if not self.authentication_service.validate_password(user_id, old_password):
            flash('Неверный старый пароль.', 'error')
            return redirect(url_for('profile'))

        if new_password != confirm_password:
            flash('Новый пароль и его подтверждение не совпадают.', 'error')
            return redirect(url_for('profile'))

        self.authentication_service.change_password(user_id, new_password)
        flash('Пароль успешно изменён.', 'success')
        return redirect(url_for('profile'))

    def setup_routes(self, app):
        @app.route('/', methods=['GET'])
        def start_page():
            return render_template('start_page.html')

        @app.route('/register', methods=['GET', 'POST'])
        def register():
            if request.method == 'POST':
                name = request.form['name']
                email = request.form['email']
                password = request.form['password']
                try:
                    self.register_user(name, email, password)
                    flash('Регистрация прошла успешно. Пожалуйста, авторизуйтесь', 'success')
                    return redirect(url_for('login'))
                except psycopg2.errors.UniqueViolation:
                    flash('Данный адрес электронной почты уже занят, выберите другой.', 'error')
                    return self.get_register_page()
                except ValueError as e:
                    flash(str(e), 'error')
                    return self.get_register_page()
            return self.get_register_page()

        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                email = request.form['email']
                password = request.form['password']
                user = self.login_user(email, password)
                if user:
                    session['user_id'] = user[0]
                    session['user_email'] = email
                    self.cart_service.create_user_cart(session['user_id'])
                    return redirect(url_for('catalog'))
                else:
                    flash('Неверный логин или пароль.', 'error')
                    return self.get_login_page()
            return self.get_login_page()

        @app.route('/profile', methods=['GET'])
        def profile():
            return self.profile()

        @app.route('/change_password', methods=['POST'])
        def change_password():
            return self.change_password()

        @app.route('/logout', methods=['GET'])
        def logout():
            session.clear()
            return redirect(url_for('start_page'))
class GoodsController:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    UPLOAD_FOLDER = 'static/images'

    def __init__(self, goods_service, order_service, user_controller):
        self.goods_service = goods_service
        self.order_service = order_service
        self.user_controller = user_controller
        self.goods_interface = GoodsInterface()
        self.order_interface = OrderInterface()
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

    def save_file(self, file):
        upload_folder = 'static/images'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return filename

    def delete_goods(self, goods_id):
        return self.goods_service.delete_goods(goods_id)

    def add_goods(self, user_id, name, description, price, category_id, product_picture):
        return self.goods_service.add_goods(user_id, name, description, price, category_id, product_picture)

    def view_purchases(self):
        user_id = session['user_id']
        purchases = self.order_service.get_user_purchases(user_id)
        user = self.user_controller.get_user_by_id(user_id)
        user_info = {
            'name': user[1],
            'profile_picture': user[4]
        }
        return self.order_interface.get_purchases_page(purchases, user_info)

    def unhide_goods(self, goods_id):
        return self.goods_service.unhide_goods(goods_id)

    def update_goods(self, goods_id, name, description, price, category_id, product_picture):
        return self.goods_service.update_goods(goods_id, name, description, price, category_id, product_picture)

    def find_user_goods(self, user_id):
        return self.goods_service.find_user_goods(user_id)

    def get_all_categories(self):
        return self.goods_service.get_all_categories()

    def find_all_goods(self, user_id):
        return self.goods_service.find_all_goods(user_id)

    def good_detail(self, goods_id):
        good = self.goods_service.get_goods_by_id(goods_id)
        return self.goods_interface.get_good_detail_page(good)

    def setup_routes(self, app):
        @app.route('/my_goods', methods=['GET'])
        def my_goods():
            user_id = session['user_id']
            goods = self.find_user_goods(user_id)
            return self.goods_interface.get_my_goods_page(goods)

        @app.route('/goods/add', methods=['GET', 'POST'])
        def add_good():
            if request.method == 'POST':
                user_id = session['user_id']
                name = request.form['name']
                description = request.form['description']
                price = request.form['price']
                category_id = request.form['category_id']
                product_picture = request.files['product_picture']
                filename = self.save_file(product_picture)

                self.goods_service.add_goods(user_id, name, description, price, category_id, filename)
                flash("Товар успешно добавлен!", "success")
                return redirect(url_for('catalog'))

            categories = self.get_all_categories()
            return self.goods_interface.get_add_good_form(categories)

        @app.route('/goods/delete/<int:goods_id>', methods=['POST'])
        def delete_good(goods_id):
            self.delete_goods(goods_id)
            flash('Товары успешно удалены!', 'success')
            return redirect(url_for('my_goods'))

        @app.route('/goods/update/<int:goods_id>', methods=['GET', 'POST'])
        def update_good(goods_id):
            if request.method == 'POST':
                name = request.form.get('name')
                description = request.form.get('description')
                price = request.form.get('price')
                category_id = request.form.get('category_id')
                product_picture = request.files['product_picture']
                filename = self.save_file(product_picture)
                self.update_goods(goods_id, name, description, price, category_id, filename)
                flash('Товары успешно обновлены!', 'success')
                return redirect(url_for('my_goods'))

            good = self.goods_service.find_good_by_id(goods_id)
            categories = self.goods_service.get_all_categories()
            return self.goods_interface.get_update_good_form(good, categories)

        @app.route('/goods/hide/<int:goods_id>', methods=['POST'])
        def hide_goods(goods_id):
            self.goods_service.hide_goods(goods_id)
            return redirect(url_for('my_goods'))

        @app.route('/goods/unhide/<int:goods_id>', methods=['POST'])
        def unhide_goods(goods_id):
            self.unhide_goods(goods_id)
            return redirect(url_for('my_goods'))

        @app.route('/catalog', methods=['GET', 'POST'])
        def catalog():
            if request.method == 'POST':
                product_name = request.form.get('product_name')
                category_name = request.form.get('category_name')
                price_range = request.form.get('price_range')
                user_id = session['user_id']

                price_min, price_max = None, None
                if price_range:
                    price_min, price_max = map(float, price_range.split('-'))

                goods = self.goods_service.search_goods(product_name, category_name, price_min, price_max, user_id)
                return self.goods_interface.get_catalog_page(goods, self.get_all_categories())

            categories = self.get_all_categories()
            goods = self.goods_service.find_all_goods(session['user_id'])
            return self.goods_interface.get_catalog_page(goods, categories)

        @app.route('/product/<int:good_id>', methods=['GET'])
        def good_detail(good_id):
            return self.good_detail(good_id)

        @app.route('/purchases', methods=['GET'])
        def purchases():
            return self.view_purchases()
class PaymentCardController:
    def __init__(self, payment_card_service, user_service):
        self.payment_card_service = payment_card_service
        self.user_service = user_service
        self.payment_card_interface = PaymentCardInterface()

    def add_payment_card(self):
        user_id = session.get('user_id')
        card_number = request.form['card_number']
        cardholder_name = request.form['card_holder_name']
        expiration_date = request.form['expiration_date']
        cvv = request.form['cvv']

        self.payment_card_service.add_payment_card(user_id, card_number, cardholder_name, expiration_date, cvv)
        flash('Платёжная карта успешно добавлена.', 'success')
        return redirect(url_for('view_user_cards'))

    def delete_payment_card(self):
        user_id = session.get('user_id')
        card_number = request.form['card_number']

        self.payment_card_service.delete_payment_card(user_id, card_number)
        flash('Платёжная карта успешно удалена.', 'success')
        return redirect(url_for('view_user_cards'))

    def view_user_cards(self):
        user_id = session.get('user_id')

        user = self.user_service.get_user_by_id(user_id)
        user_info = {
            'name': user[1],
            'profile_picture': user[4]
        }

        cards = self.payment_card_service.get_user_cards(user_id)
        return self.payment_card_interface.get_payment_cards_page(user_info, cards)

    def setup_routes(self, app):
        @app.route('/add_payment_card', methods=['POST'])
        def add_payment_card():
            return self.add_payment_card()

        @app.route('/delete_payment_card', methods=['POST'])
        def delete_payment_card():
            return self.delete_payment_card()

        @app.route('/view_user_cards', methods=['GET'])
        def view_user_cards():
            return self.view_user_cards()
class PersonalDataController:
    UPLOAD_FOLDER = 'static/images'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def __init__(self, user_service):
        self.user_service = user_service
        self.personal_data_interface = PersonalDataInterface()
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

    def save_file(self, file):
        if not file or file.filename == '':
            return None
        if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS:
            filename = secure_filename(file.filename)
            file_path = os.path.join(self.UPLOAD_FOLDER, filename)
            file.save(file_path)
            return filename
        return None

    def view_personal_data(self):
        user_id = session.get('user_id')
        user = self.user_service.get_user_by_id(user_id)
        user_info = {
            'name': user[1],
            'email': user[2],
            'profile_picture': user[4],
            'birth_date': user[5]
        }
        return self.personal_data_interface.get_personal_data_page(user_info)

    def update_personal_data(self):
        user_id = session.get('user_id')
        name = request.form['name']
        email = request.form['email']
        birth_date = request.form['birth_date']

        profile_picture = request.files.get('profile_picture')
        filename = None

        if profile_picture:
            filename = self.save_file(profile_picture)

        self.user_service.update_user(user_id, name, email, filename, birth_date)

        return redirect(url_for('view_personal_data'))

    def setup_routes(self, app):
        @app.route('/view_personal_data', methods=['GET'])
        def view_personal_data():
            return self.view_personal_data()

        @app.route('/update_personal_data', methods=['POST'])
        def update_personal_data():
            return self.update_personal_data()
class CartController:
    def __init__(self, cart_service):
        self.cart_service = cart_service
        self.cart_interface = CartInterface()

    def create_user_cart(self):
        user_id = session.get('user_id')
        self.cart_service.create_user_cart(user_id)
        return redirect(url_for('view_cart'))

    def add_to_cart(self):
        user_id = session.get('user_id')
        good_id = request.form['good_id']
        quantity = 1

        self.cart_service.add_to_cart(user_id, good_id, quantity)
        return redirect(url_for('view_cart'))

    def remove_from_cart(self):
        user_id = session.get('user_id')
        good_id = request.form['good_id']

        self.cart_service.remove_from_cart(user_id, good_id)
        return redirect(url_for('view_cart'))

    def view_cart(self):
        user_id = session.get('user_id')

        items = self.cart_service.get_items_from_cart(user_id)
        total_price = self.cart_service.get_total_price(user_id)
        return self.cart_interface.get_cart_page(items, total_price)

    def increase_quantity(self):
        user_id = session.get('user_id')
        good_id = request.form['good_id']

        self.cart_service.increase_quantity(user_id, good_id)
        return redirect(url_for('view_cart'))

    def decrease_quantity(self):
        user_id = session.get('user_id')
        good_id = request.form['good_id']

        self.cart_service.decrease_quantity(user_id, good_id)
        return redirect(url_for('view_cart'))

    def setup_routes(self, app):
        @app.route('/create_user_cart', methods=['POST'])
        def create_user_cart():
            return self.create_user_cart()

        @app.route('/add_to_cart', methods=['POST'])
        def add_to_cart():
            return self.add_to_cart()

        @app.route('/remove_from_cart', methods=['POST'])
        def remove_from_cart():
            return self.remove_from_cart()

        @app.route('/view_cart', methods=['GET'])
        def view_cart():
            return self.view_cart()

        @app.route('/increase_quantity', methods=['POST'])
        def increase_quantity():
            return self.increase_quantity()

        @app.route('/decrease_quantity', methods=['POST'])
        def decrease_quantity():
            return self.decrease_quantity()
class OrderController:
    def __init__(self, order_service, cart_service, payment_card_service):
        self.order_service = order_service
        self.cart_service = cart_service
        self.payment_card_service = payment_card_service
        self.order_interface = OrderInterface()

    def create_order(self):
        user_id = session.get('user_id')
        items = self.cart_service.get_items_from_cart(user_id)
        if not items:
            return redirect(url_for('view_cart'))

        total_price = self.cart_service.get_total_price(user_id)
        order_id = self.order_service.create_order(user_id, total_price)
        order_items = [(item[0], item[3], item[2]) for item in items]
        self.order_service.add_order_items(order_id, order_items)

        return redirect(url_for('view_order', order_id=order_id))

    def view_order(self, order_id):
        user_id = session.get('user_id')

        order_details = self.order_service.get_order_details(order_id)
        if order_details is None:
            return redirect(url_for('view_cart'))

        user_cards = self.payment_card_service.get_user_cards(user_id)
        return self.order_interface.get_order_details_page(order_details, user_cards)

    def pay_order(self):
        user_id = session.get('user_id')

        order_id = request.form.get('order_id')
        card_number = request.form.get('payment_method')

        card_details = self.payment_card_service.get_card_details(user_id, card_number)
        if not card_details:
            return redirect(url_for('view_order', order_id=order_id))

        expiration_date = card_details['expiration_date']
        current_date = datetime.now().date()

        if current_date > expiration_date:
            flash('Срок действия данной карты истёк. Пожалуйста, выберите другую карту.', 'error')
            return redirect(url_for('view_order', order_id=order_id))

        amount = self.order_service.get_order_total_price(order_id)
        if amount <= 0:
            flash('Невозможно оплатить пустой заказ. Пожалуйста, вернитесь в каталог и выберите какие-либо товары.', 'error')
            return redirect(url_for('view_order', order_id=order_id))

        self.order_service.pay_order(order_id, card_number, amount)
        self.order_service.update_order_status(order_id, 'successful')

        flash('Заказ оплачен успешно.', 'success')
        return redirect(url_for('view_order', order_id=order_id))

    def setup_routes(self, app):
        @app.route('/create_order', methods=['POST'])
        def create_order():
            return self.create_order()

        @app.route('/view_order/<int:order_id>', methods=['GET'])
        def view_order(order_id):
            return self.view_order(order_id)

        @app.route('/pay_order', methods=['POST'])
        def pay_order():
            return self.pay_order()

        @app.route('/checkout', methods=['POST'])
        def checkout():
            return self.create_order()

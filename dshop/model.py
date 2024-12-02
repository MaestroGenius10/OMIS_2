import psycopg2
from psycopg2 import sql
import re
from werkzeug.security import generate_password_hash, check_password_hash
from collections import namedtuple

class UserService:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def get_user_by_email(self, email):
        query = sql.SQL("SELECT * FROM users WHERE email = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (email,))
                user = cursor.fetchone()
                return user

    def get_user_by_id(self, user_id):
        query = sql.SQL("SELECT * FROM users WHERE id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                user = cursor.fetchone()
                return user

    def delete_user_by_email(self, email):
        query = sql.SQL("DELETE FROM users WHERE email = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (email,))
                conn.commit()

    def delete_user_by_id(self, user_id):
        query = sql.SQL("DELETE FROM users WHERE id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                conn.commit()

    def save_user(self, name, email, password_hash, profile_picture=None, birth_date=None):
        if self.get_user_by_email(email):
            raise ValueError('Email is already in use.')
        query = sql.SQL("""
            INSERT INTO users (name, email, password_hash, profile_picture, birth_date)
            VALUES (%s, %s, %s, %s, %s)
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name, email, password_hash, profile_picture, birth_date))
                conn.commit()

    def find_all_users(self):
        query = sql.SQL("SELECT * FROM users")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                users = cursor.fetchall()
                return users

    def update_user(self, user_id, name, email, profile_picture, birth_date):
        query = sql.SQL("""
            UPDATE users
            SET name = %s, email = %s, profile_picture = %s, birth_date = %s
            WHERE id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name, email, profile_picture, birth_date, user_id))
                conn.commit()
class AuthenticationService:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def _validate_email(self, email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email) is not None

    def register_user(self, name, email, password):
        if not self._validate_email(email):
            raise ValueError("Invalid email format")

        password_hash = generate_password_hash(password)
        query = sql.SQL("""
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name, email, password_hash))
                conn.commit()

    def login_user(self, email, password):
        query = sql.SQL("SELECT * FROM users WHERE email = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (email,))
                user = cursor.fetchone()
                if user and check_password_hash(user[3], password):
                    return user
                else:
                    return None

    def validate_password(self, user_id, password):
        query = sql.SQL("SELECT password_hash FROM users WHERE id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                user = cursor.fetchone()
                if user and check_password_hash(user[0], password):
                    return True
                else:
                    return False

    def change_password(self, user_id, new_password):
        password_hash = generate_password_hash(new_password)
        query = sql.SQL("""
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (password_hash, user_id))
                conn.commit()

class GoodsService:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def delete_goods(self, goods_id):
        query = sql.SQL("DELETE FROM goods WHERE id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (goods_id,))
                conn.commit()

    def hide_goods(self, goods_id):
        query = sql.SQL("UPDATE goods SET status = 'hidden' WHERE id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (goods_id,))
                conn.commit()

    def unhide_goods(self, goods_id):
        query = sql.SQL("UPDATE goods SET status = 'active' WHERE id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (goods_id,))
                conn.commit()

    def add_goods(self, user_id, name, description, price, category_id, product_picture):
        query = sql.SQL("""
            INSERT INTO goods (user_id, name, description, price, category_id, product_picture)
            VALUES (%s, %s, %s, %s, %s, %s)
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id, name, description, price, category_id, product_picture))
                conn.commit()

    def search_goods(self, product_name, category_name, price_min, price_max, user_id):
        if price_min is None:
            price_min = 0
        if price_max is None:
            price_max = float('inf')

        query = sql.SQL("""
            SELECT * FROM goods
            WHERE status != 'hidden'
              AND user_id != %s
              AND (name ILIKE %s OR %s IS NULL)
              AND (category_id IN (SELECT id FROM categories WHERE name ILIKE %s) OR %s IS NULL)
              AND (price BETWEEN %s AND %s OR %s IS NULL OR %s IS NULL)
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (
                    user_id, f"%{product_name}%", product_name, f"%{category_name}%", category_name, price_min,
                    price_max,
                    price_min, price_max))
                goods = cursor.fetchall()
                Good = namedtuple('Good',
                                  'id user_id name description price category_id product_picture status created_at updated_at ')
                return [Good(*row) for row in goods]

    def update_goods(self, goods_id, name, description, price, category_id, product_picture):
        query = sql.SQL("""
            UPDATE goods
            SET name = %s, description = %s, price = %s, category_id = %s, product_picture = %s
            WHERE id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name, description, price, category_id, product_picture,goods_id))
                conn.commit()

    def find_user_goods(self, user_id):
        query = sql.SQL("SELECT * FROM goods WHERE user_id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                goods = cursor.fetchall()
                Good = namedtuple('Good',
                                  'id user_id name description price category_id status product_picture created_at updated_at')
                return [Good(*row) for row in goods]

    def find_good_by_id(self, goods_id):
        query = sql.SQL("SELECT * FROM goods WHERE id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (goods_id,))
                good = cursor.fetchone()
                if good:
                    Good = namedtuple('Good',
                                      'id user_id name description price category_id product_picture status created_at updated_at')
                    return Good(*good)
                return None

    def get_all_categories(self):
        query = sql.SQL("SELECT id, name FROM categories")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                categories = cursor.fetchall()
                return {row[0]: row[1] for row in categories}

    def find_all_goods(self, user_id):
        query = sql.SQL("SELECT * FROM goods WHERE status != 'hidden' AND user_id != %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                goods = cursor.fetchall()
                Good = namedtuple('Good',
                                  'id user_id name description price category_id status product_picture created_at updated_at')
                return [Good(*row) for row in goods]

    def get_goods_by_id(self, goods_id):
        query = sql.SQL("""
            SELECT g.*, c.name AS category_name
            FROM goods g
            JOIN categories c ON g.category_id = c.id
            WHERE g.id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (goods_id,))
                good = cursor.fetchone()
                if good:
                    Good = namedtuple('Good',
                                      'id user_id name description price category_id status product_picture created_at updated_at category_name')
                    return Good(*good)
                return None

class PaymentCardService:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def add_payment_card(self, user_id, card_number, card_holder_name, expiration_date, cvv):
        query = sql.SQL("""
            INSERT INTO payment_cards (user_id, card_number, card_holder_name, expiration_date, cvv)
            VALUES (%s, %s, %s, %s, %s)
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id, card_number, card_holder_name, expiration_date, cvv))
                conn.commit()

    def delete_payment_card(self, user_id, card_number):
        query = sql.SQL("""
            DELETE FROM payment_cards
            WHERE user_id = %s AND card_number = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id, card_number))
                conn.commit()

    def get_user_cards(self, user_id):
        query = sql.SQL("""
            SELECT card_number
            FROM payment_cards
            WHERE user_id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                cards = cursor.fetchall()
                return [card[0] for card in cards]

    def get_card_details(self, user_id, card_number):
        query = sql.SQL("""
            SELECT card_number, card_holder_name, expiration_date, cvv
            FROM payment_cards
            WHERE user_id = %s AND card_number = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id, card_number))
                card_details = cursor.fetchone()
                if card_details:
                    return {
                        'card_number': card_details[0],
                        'card_holder_name': card_details[1],
                        'expiration_date': card_details[2],
                        'cvv': card_details[3]
                    }
                return None

class CartService:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def create_user_cart(self, user_id):
        query = sql.SQL("""
            INSERT INTO carts (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                conn.commit()

    def add_to_cart(self, user_id, good_id, quantity):
        # Получаем cart_id для данного user_id
        cart_id_query = sql.SQL("SELECT id FROM carts WHERE user_id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(cart_id_query, (user_id,))
                cart_id_result = cursor.fetchone()
                if cart_id_result is None:
                    raise ValueError("Cart not found for user_id: {}".format(user_id))
                cart_id = cart_id_result[0]

        # Проверяем, есть ли уже товар в корзине
        check_query = sql.SQL("""
            SELECT quantity FROM cart_items
            WHERE cart_id = %s AND good_id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(check_query, (cart_id, good_id))
                result = cursor.fetchone()
                if result:
                    # Если товар уже есть в корзине, обновляем количество
                    new_quantity = result[0] + quantity
                    update_query = sql.SQL("""
                        UPDATE cart_items 
                        SET quantity = %s
                        WHERE cart_id = %s AND good_id = %s
                    """)
                    cursor.execute(update_query, (new_quantity, cart_id, good_id))
                    conn.commit()
                else:
                    # Если товара нет в корзине, добавляем новый
                    insert_query = sql.SQL("""
                        INSERT INTO cart_items (cart_id, good_id, quantity)
                        VALUES (%s, %s, %s)
                    """)
                    cursor.execute(insert_query, (cart_id, good_id, quantity))
                    conn.commit()
    def remove_from_cart(self, user_id, good_id):
        # Получаем cart_id для данного user_id
        cart_id_query = sql.SQL("SELECT id FROM carts WHERE user_id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(cart_id_query, (user_id,))
                cart_id_result = cursor.fetchone()
                if cart_id_result is None:
                    raise ValueError("Cart not found for user_id: {}".format(user_id))
                cart_id = cart_id_result[0]

        query = sql.SQL("""
            DELETE FROM cart_items
            WHERE cart_id = %s AND good_id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cart_id, good_id))
                conn.commit()

    def get_items_from_cart(self, user_id):
        # Получаем cart_id для данного user_id
        cart_id_query = sql.SQL("SELECT id FROM carts WHERE user_id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(cart_id_query, (user_id,))
                cart_id_result = cursor.fetchone()
                if cart_id_result is None:
                    return []
                cart_id = cart_id_result[0]

        query = sql.SQL("""
            SELECT c.good_id, g.name, g.price, c.quantity, g.product_picture
            FROM cart_items c
            JOIN goods g ON c.good_id = g.id
            WHERE c.cart_id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cart_id,))
                items = cursor.fetchall()
                return items

    def increase_quantity(self, user_id, good_id):
        # Получаем cart_id для данного user_id
        cart_id_query = sql.SQL("SELECT id FROM carts WHERE user_id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(cart_id_query, (user_id,))
                cart_id_result = cursor.fetchone()
                if cart_id_result is None:
                    raise ValueError("Cart not found for user_id: {}".format(user_id))
                cart_id = cart_id_result[0]

        query = sql.SQL("""
            UPDATE cart_items
            SET quantity = quantity + 1
            WHERE cart_id = %s AND good_id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cart_id, good_id))
                conn.commit()

    def decrease_quantity(self, user_id, good_id):
        # Получаем cart_id для данного user_id
        cart_id_query = sql.SQL("SELECT id FROM carts WHERE user_id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(cart_id_query, (user_id,))
                cart_id_result = cursor.fetchone()
                if cart_id_result is None:
                    raise ValueError("Cart not found for user_id: {}".format(user_id))
                cart_id = cart_id_result[0]

        query = sql.SQL("""
            UPDATE cart_items
            SET quantity = quantity - 1
            WHERE cart_id = %s AND good_id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cart_id, good_id))
                conn.commit()

    def get_total_price(self, user_id):
        # Получаем cart_id для данного user_id
        cart_id_query = sql.SQL("SELECT id FROM carts WHERE user_id = %s")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(cart_id_query, (user_id,))
                cart_id_result = cursor.fetchone()
                if cart_id_result is None:
                    return 0
                cart_id = cart_id_result[0]

        query = sql.SQL("""
            SELECT SUM(g.price * c.quantity) AS total_price
            FROM cart_items c
            JOIN goods g ON c.good_id = g.id
            WHERE c.cart_id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cart_id,))
                total_price = cursor.fetchone()[0]
                return total_price if total_price else 0
class OrderService:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def create_order(self, user_id, total_price):
        query = sql.SQL("""
            INSERT INTO orders (user_id, total_price, status)
            VALUES (%s, %s, 'processing')
            RETURNING id
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id, total_price))
                order_id = cursor.fetchone()[0]
                conn.commit()
                return order_id

    def add_order_items(self, order_id, items):
        query = """
            INSERT INTO order_items (order_id, good_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for item in items:
                    cursor.execute(query, (order_id, item[0], item[1], item[2]))
                conn.commit()

    def get_order_details(self, order_id):
        query_order = """
            SELECT id, user_id, total_price, status, created_at
            FROM orders
            WHERE id = %s
        """
        query_items = """
            SELECT g.name, oi.quantity, oi.price
            FROM order_items oi
            JOIN goods g ON oi.good_id = g.id
            WHERE oi.order_id = %s
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_order, (order_id,))
                order = cursor.fetchone()
                if not order:
                    return None

                order_data = {
                    'id': order[0],
                    'user_id': order[1],
                    'total_price': float(order[2]),
                    'status': order[3],
                    'created_at': order[4],
                    'items': []
                }

                cursor.execute(query_items, (order_id,))
                items = cursor.fetchall()
                for item in items:
                    order_data['items'].append({
                        'name': item[0],
                        'quantity': item[1],
                        'price': float(item[2])
                    })

                return order_data

    def pay_order(self, order_id, payment_method, amount):
        query = sql.SQL("""
            INSERT INTO transactions (order_id, payment_method, amount, status)
            VALUES (%s, %s, %s, 'success')
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (order_id, payment_method, amount))
                conn.commit()

    def update_order_status(self, order_id, status):
        query = sql.SQL("""
            UPDATE orders
            SET status = %s
            WHERE id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (status, order_id))
                conn.commit()

    def get_order_total_price(self, order_id):
        query = sql.SQL("""
            SELECT total_price
            FROM orders
            WHERE id = %s
        """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (order_id,))
                total_price = cursor.fetchone()[0]
                return total_price if total_price else 0

    def get_user_purchases(self, user_id):
        query = sql.SQL("""
               SELECT g.id, g.name, g.description, g.price, g.product_picture
               FROM order_items oi
               JOIN goods g ON oi.good_id = g.id
               JOIN orders o ON oi.order_id = o.id
               WHERE o.user_id = %s AND o.status = 'successful'
           """)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                purchases = cursor.fetchall()
                Purchase = namedtuple('Purchase', 'id name description price product_picture')
                return [Purchase(*row) for row in purchases]







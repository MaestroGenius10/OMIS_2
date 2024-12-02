from flask import render_template

class UserInterface:
    def get_register_page(self):
        return render_template('register.html')

    def get_login_page(self):
        return render_template('login.html')

    def get_profile_page(self, user_info):
        return render_template('profile.html', user=user_info)

    def get_change_password_form(self):
        return render_template('change_password.html')

class GoodsInterface:
    def get_catalog_page(self, goods, categories):
        return render_template('catalog.html', goods=goods, categories=categories)

    def get_add_good_form(self, categories):
        return render_template('add_goods.html', categories=categories)

    def get_update_good_form(self, good, categories):
        return render_template('update_goods.html', good=good, categories=categories)

    def get_good_detail_page(self, good):
        return render_template('good_detail.html', good=good)

    def get_my_goods_page(self, goods):
        return render_template('my_goods.html', goods=goods)

class OrderInterface:
    def get_order_details_page(self, order, user_cards):
        return render_template('order_details.html', order=order, user_cards=user_cards)

    def get_purchases_page(self, purchases, user_info):
        return render_template('purchases.html', purchases=purchases, user=user_info)

class CartInterface:
    def get_cart_page(self, items, total_price):
        return render_template('cart.html', items=items, total_price=total_price)

class PaymentCardInterface:
    def get_payment_cards_page(self, user, cards):
        return render_template('payment_cards.html', user=user, cards=cards)

class PersonalDataInterface:
    def get_personal_data_page(self, user_info):
        return render_template('personal_data.html', user=user_info)


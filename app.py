from flask import Flask, render_template, session, request, jsonify, redirect, url_for
from flask_session import Session
import os
import json
from datetime import datetime
import uuid

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"  # вместо "null"
app.config["SESSION_FILE_DIR"] = "./flask_session"  # папка для сессий
Session(app)

ORDERS_DIR = "orders"
USERS_FILE = "users.json"

if not os.path.exists(ORDERS_DIR):
    os.makedirs(ORDERS_DIR)

products = [
    {
        "id": 1,
        "title": "Черная футболка",
        "price": 1299,
        "main_image": "tshirt-main.jpg",
        "model_image": "tshirt-model.jpg",  # если нет - будет заглушка
        "description": "Классическая черная футболка из 100% хлопка. Идеально подходит для повседневной носки. Доступны размеры от XS до XXL.",
        "features": [
            "Материал: Хлопок 100%",
            "Сезон: Всесезонная",
            "Уход: Машинная стирка"
        ]
    },
    {
        "id": 2,
        "title": "Белая кружка",
        "price": 799,
        "main_image": "mug-main.jpg",
        "model_image": None,  # Нет фотосессии
        "description": "Белая керамическая кружка объемом 350 мл. Можно мыть в посудомоечной машине. Устойчива к высоким температурам.",
        "features": [
            "Объем: 350 мл",
            "Материал: Керамика",
            "Можно мыть в ПММ"
        ]
    },
    {
        "id": 3,
        "title": "Худи MW STORE",
        "price": 2599,
        "main_image": "hoodie-main.jpg",
        "model_image": "hoodie-model.jpg",
        "description": "Теплое худи с капюшоном и передним карманом. Состав: 80% хлопок, 20% полиэстер. Регулируемый капюшон на шнурке.",
        "features": [
            "Материал: Хлопок 80%, Полиэстер 20%",
            "Капюшон: Есть",
            "Карманы: Кенгуру"
        ]
    },
]


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def calculate_total(cart):
    total = 0
    for pid, qty in cart.items():
        product = next((p for p in products if p["id"] == int(pid)), None)
        if product:
            total += qty * product["price"]
    return total


def save_order_to_txt(order_data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 50 + "\n")
        f.write(f"ЗАКАЗ #{order_data['order_id']}\n")
        f.write(f"Дата: {order_data['timestamp']}\n")
        f.write("=" * 50 + "\n\n")

        f.write("👤 ПОКУПАТЕЛЬ:\n")
        f.write(f"  Имя: {order_data['customer']['name']}\n")
        f.write(f"  Телефон: {order_data['customer']['phone']}\n")
        f.write(f"  Email: {order_data['customer']['email']}\n")
        f.write(f"  ID пользователя: {order_data['customer']['user_id']}\n\n")

        f.write("💳 ОПЛАТА:\n")
        payment_names = {
            'card': 'Банковская карта',
            'sbp': 'СБП',
            'cash': 'Наличные'
        }
        f.write(f"  Способ: {payment_names.get(order_data['payment_method'], order_data['payment_method'])}\n\n")

        f.write("📦 ТОВАРЫ:\n")
        for item in order_data['cart_items']:
            f.write(f"  • {item['title']}\n")
            f.write(f"    {item['price']}₽ × {item['qty']} = {item['subtotal']}₽\n")

        f.write("\n" + "-" * 50 + "\n")
        f.write(f"ИТОГО: {order_data['total']}₽\n")
        f.write("=" * 50 + "\n")


# ===== ДЕКОРАТОР ДЛЯ ЗАЩИТЫ МАРШРУТОВ =====
def login_required(f):
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("register"))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# ===== МАРШРУТЫ =====
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("register"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.get_json()
        phone = data.get("phone")
        email = data.get("email")

        if not phone and not email:
            return jsonify({"status": "error", "message": "Введите телефон или email"}), 400

        users = load_users()

        # Проверяем, существует ли пользователь
        user_id = None
        for uid, user in users.items():
            if (phone and user.get("phone") == phone) or (email and user.get("email") == email):
                user_id = uid
                break

        if not user_id:
            # Создаем нового пользователя
            user_id = str(uuid.uuid4())[:8]
            users[user_id] = {
                "phone": phone,
                "email": email,
                "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_users(users)

        # Сохраняем в сессию
        session["user_id"] = user_id
        session["user_phone"] = phone
        session["user_email"] = email

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "message": "Регистрация успешна"
        })

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_phone", None)
    session.pop("user_email", None)
    return redirect(url_for("register"))


@app.route("/products")
@login_required
def products_page():
    return render_template("products.html", products=products)


@app.route("/cart", methods=["GET"])
@login_required
def cart():
    cart_data = session.get("cart", {})
    cart_products = []
    total = 0

    for pid, qty in cart_data.items():
        product = next((p for p in products if p["id"] == int(pid)), None)
        if product:
            cart_item = {
                "id": product["id"],
                "title": product["title"],
                "price": product["price"],
                "qty": qty,
                "subtotal": qty * product["price"]
            }
            cart_products.append(cart_item)
            total += cart_item["subtotal"]

    return render_template("cart.html", cart=cart_products, total=total)


@app.route("/api/cart", methods=["GET"])
@login_required
def cart_api():
    cart_data = session.get("cart", {})
    cart_products = []
    total = 0

    for pid, qty in cart_data.items():
        product = next((p for p in products if p["id"] == int(pid)), None)
        if product:
            cart_products.append({
                "id": pid,
                "title": product["title"],
                "price": product["price"],
                "qty": qty,
                "subtotal": qty * product["price"]
            })
            total += qty * product["price"]

    return jsonify({
        "cart": cart_products,
        "total": total
    })


@app.route("/add_to_cart/<int:pid>", methods=["POST"])
@login_required
def add_to_cart(pid):
    cart = session.get("cart", {})
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"status": "ok", "cart": session["cart"]})

    return redirect(url_for("products_page"))


@app.route("/update_cart/<int:pid>", methods=["POST"])
@login_required
def update_cart(pid):
    data = request.get_json()
    change = data.get('change', 0)

    cart = session.get("cart", {})

    if pid in cart:
        cart[pid] = cart[pid] + change
        if cart[pid] <= 0:
            del cart[pid]

    session["cart"] = cart

    return jsonify({"status": "ok", "cart": session["cart"]})


@app.route("/remove_from_cart/<int:pid>", methods=["POST"])
@login_required
def remove_from_cart(pid):
    cart = session.get("cart", {})

    if pid in cart:
        del cart[pid]

    session["cart"] = cart

    return jsonify({"status": "ok", "cart": session["cart"]})


@app.route("/clear_cart")
@login_required
def clear_cart():
    session["cart"] = {}
    return redirect(url_for("cart"))


@app.route("/checkout")
@login_required
def checkout():
    cart_data = session.get("cart", {})
    cart_products = []
    total = 0

    for pid, qty in cart_data.items():
        product = next((p for p in products if p["id"] == int(pid)), None)
        if product:
            cart_item = {
                "id": product["id"],
                "title": product["title"],
                "price": product["price"],
                "qty": qty,
                "subtotal": qty * product["price"]
            }
            cart_products.append(cart_item)
            total += cart_item["subtotal"]

    return render_template("checkout.html", cart=cart_products, total=total)


@app.route("/place_order", methods=["POST"])
@login_required
def place_order():
    try:
        # Получаем данные из формы
        order_data = {
            "order_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer": {
                "user_id": session.get("user_id", "guest"),
                "name": request.form.get("name"),
                "phone": request.form.get("phone"),
                "email": request.form.get("email")
            },
            "payment_method": request.form.get("payment"),
            "cart": session.get("cart", {}),
            "total": calculate_total(session.get("cart", {}))
        }

        # Получаем детальную информацию о товарах
        cart_items = []
        for pid, qty in order_data["cart"].items():
            product = next((p for p in products if p["id"] == int(pid)), None)
            if product:
                cart_items.append({
                    "id": pid,
                    "title": product["title"],
                    "price": product["price"],
                    "qty": qty,
                    "subtotal": qty * product["price"]
                })

        order_data["cart_items"] = cart_items

        # Сохраняем в JSON
        json_filename = f"{ORDERS_DIR}/order_{order_data['order_id']}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(order_data, f, ensure_ascii=False, indent=2)

        # Сохраняем в TXT
        txt_filename = f"{ORDERS_DIR}/order_{order_data['order_id']}.txt"
        save_order_to_txt(order_data, txt_filename)

        # Очищаем корзину
        session["cart"] = {}

        return jsonify({
            "status": "success",
            "order_id": order_data["order_id"],
            "message": "Заказ успешно оформлен"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/product/<int:pid>")
@login_required
def product_detail(pid):
    product = next((p for p in products if p["id"] == pid), None)
    if not product:
        return redirect(url_for("products_page"))
    return render_template("product.html", product=product)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
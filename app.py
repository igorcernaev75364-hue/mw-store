from flask import Flask, render_template, session, request, jsonify, redirect, url_for
from flask_session import Session
import os
import json
from datetime import datetime
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "/tmp/flask_session"

# Создаем папку для сессий
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)

# Инициализируем Session
Session(app)

# Создаем папки для хранения данных
ORDERS_DIR = "orders"
if not os.path.exists(ORDERS_DIR):
    os.makedirs(ORDERS_DIR)

products = [
    {
        "id": 1, 
        "title": "Черная футболка", 
        "price": 1299,
        "main_image": "tshirt-main.jpg",
        "model_image": None,
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
        "model_image": None,
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
        f.write(f"  Email: {order_data['customer']['email']}\n\n")
        
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

# ===== МАРШРУТЫ =====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/products")
def products_page():
    return render_template("products.html", products=products)

@app.route("/cart")
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

@app.route("/add_to_cart/<int:pid>", methods=["POST"])
def add_to_cart(pid):
    cart = session.get("cart", {})
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart
    return redirect(request.referrer or url_for("products_page"))

@app.route("/update_cart/<int:pid>", methods=["POST"])
def update_cart(pid):
    action = request.form.get("action")
    cart = session.get("cart", {})
    
    if pid in cart:
        if action == "increase":
            cart[pid] = cart[pid] + 1
        elif action == "decrease":
            cart[pid] = cart[pid] - 1
            if cart[pid] <= 0:
                del cart[pid]
        elif action == "remove":
            del cart[pid]
    
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/clear_cart", methods=["POST"])
def clear_cart():
    session["cart"] = {}
    return redirect(url_for("cart"))

@app.route("/checkout")
def checkout():
    cart_data = session.get("cart", {})
    cart_products = []
    total = 0
    
    if not cart_data:
        return redirect(url_for("cart"))
    
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
def place_order():
    try:
        order_data = {
            "order_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer": {
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
        
        return render_template("order_success.html", order_id=order_data["order_id"])
        
    except Exception as e:
        return render_template("checkout.html", error=str(e))

@app.route("/product/<int:pid>")
def product_detail(pid):
    product = next((p for p in products if p["id"] == pid), None)
    if not product:
        return redirect(url_for("products_page"))
    return render_template("product.html", product=product)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

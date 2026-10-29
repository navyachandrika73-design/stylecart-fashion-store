
import os
import re
import math
import sqlite3
from collections import Counter
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "store.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-dev-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


PRODUCTS = [
    ("Everyday Cotton Shirt", "Men", "Shirts", 899, 1299, "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=900&q=85", "Soft cotton shirt for everyday styling.", 4.4, "New"),
    ("Relaxed Linen Shirt", "Men", "Shirts", 1199, 1799, "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=900&q=85", "Breathable linen blend with a relaxed fit.", 4.2, "Trending"),
    ("Classic Denim Jacket", "Men", "Jackets", 1899, 2499, "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=900&q=85", "A versatile layer for casual looks.", 4.5, "Bestseller"),
    ("Minimal Sneakers", "Men", "Footwear", 1599, 2199, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85", "Clean everyday sneakers with a cushioned sole.", 4.3, "Popular"),
    ("Floral Summer Dress", "Women", "Dresses", 1499, 2199, "https://images.unsplash.com/photo-1612336307429-8a898d10e223?auto=format&fit=crop&w=900&q=85", "An easy, airy dress for sunny days.", 4.6, "Trending"),
    ("Tailored Blazer", "Women", "Outerwear", 2499, 3299, "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=900&q=85", "Polished tailoring for work and evenings.", 4.4, "New"),
    ("Everyday Tote Bag", "Women", "Bags", 999, 1499, "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=900&q=85", "Roomy tote for your daily essentials.", 4.1, "Popular"),
    ("Classic White Sneakers", "Women", "Footwear", 1699, 2299, "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=900&q=85", "Minimal sneakers that go with everything.", 4.5, "Bestseller"),
    ("Ribbed Knit Top", "Women", "Tops", 699, 999, "https://images.unsplash.com/photo-1564257577-6a5b3f9f6c11?auto=format&fit=crop&w=900&q=85", "A soft ribbed top for easy layering.", 4.0, "New"),
    ("Everyday Backpack", "Unisex", "Bags", 1299, 1799, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85", "Functional storage with a clean silhouette.", 4.3, "Popular"),
    ("Soft Knit Sweater", "Men", "Knitwear", 1399, 1999, "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?auto=format&fit=crop&w=900&q=85", "A comfortable knit for cooler days.", 4.2, "Trending"),
    ("Statement Sunglasses", "Unisex", "Accessories", 599, 899, "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=900&q=85", "A bold finishing touch for your look.", 4.1, "Popular"),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            price INTEGER NOT NULL,
            original_price INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            description TEXT NOT NULL,
            rating REAL NOT NULL DEFAULT 4.0,
            tag TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
    """)
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        db.executemany("""
            INSERT INTO products
            (name, category, subcategory, price, original_price, image_url, description, rating, tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, PRODUCTS)
    db.commit()
    db.close()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    cart_count = sum(int(qty) for qty in cart.values())
    return {"current_user": current_user(), "cart_count": cart_count}


def product_from_row(row):
    return dict(row)


@app.route("/")
def home():
    db = get_db()
    featured = db.execute("SELECT * FROM products ORDER BY rating DESC LIMIT 8").fetchall()
    return render_template("index.html", products=featured)


@app.route("/products")
def products():
    db = get_db()
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "recommended")
    max_price = request.args.get("max_price", "").strip()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR description LIKE ? OR category LIKE ? OR subcategory LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if max_price.isdigit():
        query += " AND price <= ?"
        params.append(int(max_price))
    sort_options = {
        "price_low": "price ASC",
        "price_high": "price DESC",
        "rating": "rating DESC",
        "newest": "id DESC",
        "recommended": "rating DESC, id DESC",
    }
    query += " ORDER BY " + sort_options.get(sort, sort_options["recommended"])
    rows = db.execute(query, params).fetchall()
    categories = [r["category"] for r in db.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()]
    return render_template("products.html", products=rows, categories=categories,
                           q=search, selected_category=category, sort=sort, max_price=max_price)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    related = db.execute("SELECT * FROM products WHERE category = ? AND id != ? LIMIT 4",
                         (product["category"], product_id)).fetchall()
    return render_template("product_detail.html", product=product, related=related)


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = get_db().execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    cart = session.get("cart", {})
    key = str(product_id)
    cart[key] = min(int(cart.get(key, 0)) + 1, 10)
    session["cart"] = cart
    flash("Added to your bag.", "success")
    return redirect(request.referrer or url_for("products"))


@app.route("/cart")
def cart():
    db = get_db()
    cart_items = []
    total = 0
    cart_data = session.get("cart", {})
    for product_id, quantity in cart_data.items():
        item = db.execute("SELECT * FROM products WHERE id = ?", (int(product_id),)).fetchone()
        if item:
            subtotal = item["price"] * int(quantity)
            total += subtotal
            cart_items.append({"product": item, "quantity": int(quantity), "subtotal": subtotal})
    return render_template("cart.html", items=cart_items, total=total)


@app.post("/cart/update/<int:product_id>")
def update_cart(product_id):
    cart_data = session.get("cart", {})
    key = str(product_id)
    qty = request.form.get("quantity", "1")
    if key in cart_data:
        try:
            qty = int(qty)
        except ValueError:
            qty = 1
        if qty <= 0:
            cart_data.pop(key, None)
        else:
            cart_data[key] = min(qty, 10)
        session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart_data = session.get("cart", {})
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    flash("Item removed from your bag.", "info")
    return redirect(url_for("cart"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "error")
            return render_template("register.html")
        try:
            db = get_db()
            cur = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                             (name, email, generate_password_hash(password)))
            db.commit()
            session.clear()
            session["user_id"] = cur.lastrowid
            session["cart"] = {}
            flash("Account created. Welcome!", "success")
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            flash("An account with that email already exists. Please log in.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["cart"] = {}
            flash("You are now logged in.", "success")
            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("home"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    db = get_db()
    cart_data = session.get("cart", {})
    items = []
    total = 0
    for product_id, quantity in cart_data.items():
        product = db.execute("SELECT * FROM products WHERE id = ?", (int(product_id),)).fetchone()
        if product:
            qty = int(quantity)
            items.append((product, qty))
            total += product["price"] * qty
    if not items:
        flash("Your bag is empty.", "info")
        return redirect(url_for("products"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        if not name or not address or not phone:
            flash("Please fill in all delivery details.", "error")
            return render_template("checkout.html", items=items, total=total)
        cur = db.execute("INSERT INTO orders (user_id, total) VALUES (?, ?)",
                         (session["user_id"], total))
        order_id = cur.lastrowid
        for product, qty in items:
            db.execute("""INSERT INTO order_items
                (order_id, product_id, product_name, quantity, unit_price)
                VALUES (?, ?, ?, ?, ?)""",
                (order_id, product["id"], product["name"], qty, product["price"]))
        db.commit()
        session["cart"] = {}
        return redirect(url_for("order_confirmation", order_id=order_id))
    return render_template("checkout.html", items=items, total=total)


@app.route("/orders")
@login_required
def orders():
    db = get_db()
    rows = db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
                      (session["user_id"],)).fetchall()
    order_items = {}
    for order in rows:
        order_items[order["id"]] = db.execute(
            "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
        ).fetchall()
    return render_template("orders.html", orders=rows, order_items=order_items)


@app.route("/order/<int:order_id>")
@login_required
def order_confirmation(order_id):
    order = get_db().execute("SELECT * FROM orders WHERE id = ? AND user_id = ?",
                             (order_id, session["user_id"])).fetchone()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("orders"))
    items = get_db().execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    return render_template("order_confirmation.html", order=order, items=items)


@app.route("/recommendations")
def recommendations():
    db = get_db()
    all_products = db.execute("SELECT * FROM products").fetchall()
    last_product_id = session.get("last_product_id")
    rows = []
    personalized = False

    if last_product_id and all_products:
        texts = [
            f"{p['name']} {p['category']} {p['subcategory']} {p['description']}"
            for p in all_products
        ]

        token_lists = [
            re.findall(r"[a-z0-9]+", text.lower())
            for text in texts
        ]

        document_count = len(token_lists)
        document_frequency = Counter()

        for tokens in token_lists:
            document_frequency.update(set(tokens))

        idf = {
            word: math.log((document_count + 1) / (frequency + 1)) + 1
            for word, frequency in document_frequency.items()
        }

        vectors = []
        for tokens in token_lists:
            counts = Counter(tokens)
            total_words = max(len(tokens), 1)
            vector = {
                word: (count / total_words) * idf[word]
                for word, count in counts.items()
            }
            vectors.append(vector)

        target_index = next(
            (
                i for i, product in enumerate(all_products)
                if product["id"] == int(last_product_id)
            ),
            None,
        )

        if target_index is not None:
            target_vector = vectors[target_index]
            target_norm = math.sqrt(
                sum(value * value for value in target_vector.values())
            )
            ranked = []

            for i, product in enumerate(all_products):
                if i == target_index:
                    continue

                other_vector = vectors[i]
                dot_product = sum(
                    value * other_vector.get(word, 0)
                    for word, value in target_vector.items()
                )
                other_norm = math.sqrt(
                    sum(value * value for value in other_vector.values())
                )

                similarity = (
                    dot_product / (target_norm * other_norm)
                    if target_norm and other_norm
                    else 0
                )

                ranked.append((similarity, product["rating"], product))

            ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
            rows = [product for _, _, product in ranked[:8]]
            personalized = True

    if not rows:
        rows = db.execute(
            "SELECT * FROM products ORDER BY rating DESC LIMIT 8"
        ).fetchall()

    return render_template(
        "recommendations.html",
        products=rows,
        personalized=personalized,
    )


@app.before_request
def remember_last_category():
    if request.endpoint == "product_detail":
        try:
            product_id = int(request.view_args.get("product_id"))
            session["last_product_id"] = product_id
        except (ValueError, TypeError, AttributeError):
            pass


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)

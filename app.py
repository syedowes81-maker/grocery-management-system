import io
import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, session, send_file, g

# ── ReportLab (bill generation) ──────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

app = Flask(__name__)
app.secret_key = "freshcart_super_secret_2025_xyz"   # strong secret key

DATABASE = "freshcart.db"

# ─────────────────────────────────────────────────────────────────────────────
#  ALL PRODUCTS (source of truth — also seeded into SQLite)
# ─────────────────────────────────────────────────────────────────────────────
ALL_PRODUCTS = {
    "Fruits": [
        {"name": "Apple",        "price": 40,  "emoji": "🍎", "desc": "Crisp Himalayan apples, perfect for snacking and baking."},
        {"name": "Banana",       "price": 20,  "emoji": "🍌", "desc": "Ripe and sweet bananas, rich in potassium and energy."},
        {"name": "Mango",        "price": 80,  "emoji": "🥭", "desc": "Juicy Alphonso mangoes — the king of all fruits."},
        {"name": "Orange",       "price": 35,  "emoji": "🍊", "desc": "Vitamin C-packed Nagpur oranges, tangy and refreshing."},
        {"name": "Grapes",       "price": 60,  "emoji": "🍇", "desc": "Seedless green grapes, plump and sweet."},
        {"name": "Watermelon",   "price": 45,  "emoji": "🍉", "desc": "Chilled whole watermelon, perfect for summer days."},
        {"name": "Strawberry",   "price": 90,  "emoji": "🍓", "desc": "Fresh farm strawberries, great for desserts and shakes."},
        {"name": "Pineapple",    "price": 55,  "emoji": "🍍", "desc": "Sweet and tangy whole pineapple, freshly harvested."},
        {"name": "Papaya",       "price": 30,  "emoji": "🍈", "desc": "Ripe papaya rich in digestive enzymes and vitamins."},
        {"name": "Kiwi",         "price": 70,  "emoji": "🥝", "desc": "New Zealand kiwis, tangy and loaded with vitamin C."},
        {"name": "Pomegranate",  "price": 85,  "emoji": "🍑", "desc": "Ruby red pomegranates bursting with antioxidants."},
        {"name": "Guava",        "price": 25,  "emoji": "🍐", "desc": "Fresh guavas with a sweet tropical aroma."},
        {"name": "Lychee",       "price": 95,  "emoji": "🍒", "desc": "Seasonal lychees — juicy, fragrant, and delicious."},
        {"name": "Coconut",      "price": 40,  "emoji": "🥥", "desc": "Fresh whole coconut with sweet tender water inside."},
        {"name": "Avocado",      "price": 120, "emoji": "🥑", "desc": "Creamy Hass avocados, great on toast or in salads."},
        {"name": "Lemon",        "price": 15,  "emoji": "🍋", "desc": "Tangy fresh lemons perfect for cooking and drinks."},
        {"name": "Pear",         "price": 50,  "emoji": "🍐", "desc": "Soft and sweet pears, excellent for kids."},
        {"name": "Cherry",       "price": 150, "emoji": "🍒", "desc": "Imported dark cherries, sweet and rich in antioxidants."},
        {"name": "Plum",         "price": 65,  "emoji": "🍑", "desc": "Juicy purple plums, tangy with a sweet finish."},
        {"name": "Dragon Fruit", "price": 110, "emoji": "🐉", "desc": "Exotic dragon fruit, vibrant pink and mildly sweet."},
    ],
    "Vegetables": [
        {"name": "Tomato",       "price": 20, "emoji": "🍅", "desc": "Farm-fresh red tomatoes, essential for every kitchen."},
        {"name": "Potato",       "price": 15, "emoji": "🥔", "desc": "Versatile potatoes perfect for curries and fries."},
        {"name": "Onion",        "price": 18, "emoji": "🧅", "desc": "Premium red onions, the base of every great dish."},
        {"name": "Carrot",       "price": 25, "emoji": "🥕", "desc": "Crunchy orange carrots, great for salads and cooking."},
        {"name": "Spinach",      "price": 20, "emoji": "🥬", "desc": "Tender baby spinach leaves, packed with iron."},
        {"name": "Broccoli",     "price": 45, "emoji": "🥦", "desc": "Fresh broccoli florets, excellent stir-fried or steamed."},
        {"name": "Cauliflower",  "price": 35, "emoji": "🥦", "desc": "White cauliflower, great for gobi dishes and rice bowls."},
        {"name": "Capsicum",     "price": 30, "emoji": "🫑", "desc": "Colorful bell peppers — red, yellow, and green mix."},
        {"name": "Cucumber",     "price": 15, "emoji": "🥒", "desc": "Cool and crunchy cucumbers, perfect in raita and salad."},
        {"name": "Green Peas",   "price": 40, "emoji": "🫛", "desc": "Sweet fresh green peas, great for pulao and curries."},
        {"name": "Garlic",       "price": 30, "emoji": "🧄", "desc": "Aromatic garlic cloves, a staple in Indian cooking."},
        {"name": "Ginger",       "price": 25, "emoji": "🫚", "desc": "Fresh ginger root, perfect for teas and curries."},
        {"name": "Eggplant",     "price": 22, "emoji": "🍆", "desc": "Smooth purple eggplant for baingan bharta and more."},
        {"name": "Cabbage",      "price": 18, "emoji": "🥬", "desc": "Crisp green cabbage, great for stir-fry and salads."},
        {"name": "Corn",         "price": 20, "emoji": "🌽", "desc": "Sweet golden corn, great boiled, roasted, or in soup."},
        {"name": "Lady Finger",  "price": 28, "emoji": "🫛", "desc": "Fresh bhindi (okra), a beloved Indian vegetable."},
        {"name": "Bitter Gourd", "price": 24, "emoji": "🥒", "desc": "Fresh karela, known for its health benefits."},
        {"name": "Mushroom",     "price": 60, "emoji": "🍄", "desc": "Button mushrooms, versatile for soups and sautes."},
        {"name": "Sweet Potato", "price": 30, "emoji": "🍠", "desc": "Naturally sweet and nutritious, great roasted."},
        {"name": "Beetroot",     "price": 25, "emoji": "🟣", "desc": "Earthy and sweet beetroots, great in salads and juices."},
    ],
    "Dairy": [
        {"name": "Full Cream Milk",   "price": 28,  "emoji": "🥛", "desc": "Fresh full cream milk from local dairies, 500ml."},
        {"name": "Toned Milk",        "price": 24,  "emoji": "🥛", "desc": "Low-fat toned milk, ideal for health-conscious families."},
        {"name": "Curd",              "price": 30,  "emoji": "🥣", "desc": "Thick and creamy homestyle curd, 400g pack."},
        {"name": "Paneer",            "price": 80,  "emoji": "🧀", "desc": "Fresh soft paneer, made daily — perfect for curries."},
        {"name": "Butter",            "price": 55,  "emoji": "🧈", "desc": "Creamy salted butter, great for rotis and cooking."},
        {"name": "Ghee",              "price": 150, "emoji": "🫙", "desc": "Pure cow ghee with rich aroma, 500ml jar."},
        {"name": "Cheese Slices",     "price": 90,  "emoji": "🧀", "desc": "Processed cheese slices, ideal for sandwiches."},
        {"name": "Mozzarella",        "price": 120, "emoji": "🧀", "desc": "Stretchy mozzarella, perfect for homemade pizza."},
        {"name": "Cream",             "price": 45,  "emoji": "🥛", "desc": "Fresh cooking cream, 200ml — great for gravies."},
        {"name": "Lassi",             "price": 25,  "emoji": "🥤", "desc": "Sweet chilled lassi, a refreshing Indian classic."},
        {"name": "Spiced Buttermilk", "price": 15,  "emoji": "🥛", "desc": "Chilled chaas with jeera and pudina, light and digestive."},
        {"name": "Greek Yogurt",      "price": 85,  "emoji": "🥣", "desc": "Thick protein-rich Greek yogurt, great with granola."},
        {"name": "Flavored Milk",     "price": 35,  "emoji": "🍫", "desc": "Chocolate and strawberry flavored milk for kids."},
        {"name": "Condensed Milk",    "price": 65,  "emoji": "🥛", "desc": "Sweet condensed milk, great for desserts, 400g tin."},
        {"name": "Ice Cream",         "price": 110, "emoji": "🍨", "desc": "Creamy vanilla ice cream tub, 500ml."},
        {"name": "Whipped Cream",     "price": 95,  "emoji": "🍦", "desc": "Ready-to-use whipped cream spray can."},
        {"name": "Cream Cheese",      "price": 130, "emoji": "🧀", "desc": "Smooth cream cheese, perfect for cheesecakes."},
        {"name": "Skimmed Milk",      "price": 22,  "emoji": "🥛", "desc": "Fat-free skimmed milk, ideal for diet plans."},
        {"name": "Sour Cream",        "price": 75,  "emoji": "🥣", "desc": "Tangy sour cream, great as a dip or topping."},
        {"name": "Milk Powder",       "price": 60,  "emoji": "🫙", "desc": "Full cream milk powder, 200g pouch."},
    ],
    "Meat": [
        {"name": "Chicken Breast", "price": 180, "emoji": "🍗", "desc": "Boneless skinless chicken breast, lean and healthy."},
        {"name": "Chicken Leg",    "price": 140, "emoji": "🍖", "desc": "Juicy chicken drumsticks, great for grills and curries."},
        {"name": "Whole Chicken",  "price": 220, "emoji": "🐔", "desc": "Fresh whole broiler chicken, approx 1kg."},
        {"name": "Mutton",         "price": 550, "emoji": "🐑", "desc": "Tender curry-cut mutton pieces, 500g pack."},
        {"name": "Lamb Chops",     "price": 620, "emoji": "🍖", "desc": "Premium lamb chops for grilling and roasting."},
        {"name": "Eggs",           "price": 75,  "emoji": "🥚", "desc": "Farm-fresh brown eggs, 12 pieces per pack."},
        {"name": "Fish Fillet",    "price": 250, "emoji": "🐟", "desc": "Boneless fish fillets, fresh catch of the day."},
        {"name": "Prawns",         "price": 320, "emoji": "🦐", "desc": "Cleaned and deveined medium prawns, 250g."},
        {"name": "Salmon",         "price": 480, "emoji": "🍣", "desc": "Premium Norwegian salmon, great for sushi and grills."},
        {"name": "Crab",           "price": 350, "emoji": "🦀", "desc": "Fresh whole crab, best for coastal curries."},
        {"name": "Tuna",           "price": 280, "emoji": "🐠", "desc": "Fresh tuna steak, great seared or in salads."},
        {"name": "Chicken Mince",  "price": 160, "emoji": "🍗", "desc": "Minced chicken, perfect for kebabs and cutlets."},
        {"name": "Mutton Mince",   "price": 400, "emoji": "🐑", "desc": "Fresh mutton keema, great for biryani and curries."},
        {"name": "Chicken Wings",  "price": 200, "emoji": "🍗", "desc": "Meaty chicken wings, perfect for BBQ and frying."},
        {"name": "Pork Belly",     "price": 300, "emoji": "🥩", "desc": "Tender pork belly slices for slow cooking."},
        {"name": "Duck",           "price": 380, "emoji": "🦆", "desc": "Farm-raised duck, rich and flavorful for roasting."},
        {"name": "Quail",          "price": 200, "emoji": "🐦", "desc": "Whole quail birds, great for gourmet cooking."},
        {"name": "Lobster",        "price": 800, "emoji": "🦞", "desc": "Whole fresh lobster, premium seafood experience."},
        {"name": "Squid",          "price": 260, "emoji": "🦑", "desc": "Fresh cleaned squid rings, perfect for frying."},
        {"name": "Sardines",       "price": 120, "emoji": "🐟", "desc": "Fresh sardines, omega-3 rich and delicious grilled."},
    ],
    "Snacks": [
        {"name": "Potato Chips",   "price": 30,  "emoji": "🥔", "desc": "Crispy salted potato chips, the ultimate snack."},
        {"name": "Popcorn",        "price": 25,  "emoji": "🍿", "desc": "Buttery microwave popcorn, great for movie nights."},
        {"name": "Biscuits",       "price": 20,  "emoji": "🍪", "desc": "Crispy cream biscuits, perfect with chai."},
        {"name": "Cookies",        "price": 45,  "emoji": "🍪", "desc": "Chocolate chip cookies, freshly baked and soft."},
        {"name": "Namkeen Mix",    "price": 35,  "emoji": "🫘", "desc": "Spicy Indian namkeen mix, great as a tea-time snack."},
        {"name": "Peanuts",        "price": 20,  "emoji": "🥜", "desc": "Roasted salted peanuts, crunchy and protein-rich."},
        {"name": "Cashews",        "price": 120, "emoji": "🪙", "desc": "Premium whole cashews, lightly roasted."},
        {"name": "Almonds",        "price": 140, "emoji": "🌰", "desc": "California almonds, raw and great for snacking."},
        {"name": "Dark Chocolate", "price": 90,  "emoji": "🍫", "desc": "70% dark chocolate bar, rich and bittersweet."},
        {"name": "Milk Chocolate", "price": 60,  "emoji": "🍫", "desc": "Smooth milk chocolate, a classic sweet treat."},
        {"name": "Granola Bar",    "price": 40,  "emoji": "🌾", "desc": "Oats and honey granola bar, a healthy snack option."},
        {"name": "Wafers",         "price": 25,  "emoji": "🍘", "desc": "Light and crispy cream wafers in vanilla and chocolate."},
        {"name": "Nachos",         "price": 50,  "emoji": "🌮", "desc": "Corn tortilla chips, great with salsa and dips."},
        {"name": "Rice Cakes",     "price": 35,  "emoji": "🍙", "desc": "Light rice cakes, low calorie and filling."},
        {"name": "Trail Mix",      "price": 75,  "emoji": "🥜", "desc": "Mixed nuts and dried fruits energy trail mix."},
        {"name": "Dried Mango",    "price": 85,  "emoji": "🥭", "desc": "Sweet and chewy sundried mango strips."},
        {"name": "Protein Bar",    "price": 100, "emoji": "💪", "desc": "20g protein bar in chocolate peanut butter flavor."},
        {"name": "Mukhwas",        "price": 30,  "emoji": "🌿", "desc": "Colorful mukhwas mouth freshener after meals."},
        {"name": "Choco Puffs",    "price": 40,  "emoji": "🍫", "desc": "Chocolate puffed corn cereal, kids love it."},
        {"name": "Sesame Chikki",  "price": 25,  "emoji": "🍬", "desc": "Traditional til-gur chikki, a desi classic."},
    ],
    "Beverages": [
        {"name": "Orange Juice",     "price": 60,  "emoji": "🍊", "desc": "100% fresh-squeezed orange juice, no added sugar."},
        {"name": "Apple Juice",      "price": 55,  "emoji": "🍎", "desc": "Clear apple juice from real apples, 1L pack."},
        {"name": "Mango Juice",      "price": 50,  "emoji": "🥭", "desc": "Thick Alphonso mango pulp juice, a summer favourite."},
        {"name": "Green Tea",        "price": 80,  "emoji": "🍵", "desc": "Premium Darjeeling green tea bags, 25 per box."},
        {"name": "Black Coffee",     "price": 95,  "emoji": "☕", "desc": "Dark roast ground coffee, bold and aromatic."},
        {"name": "Coconut Water",    "price": 40,  "emoji": "🥥", "desc": "Natural tender coconut water, packed and chilled."},
        {"name": "Lemonade",         "price": 30,  "emoji": "🍋", "desc": "Tangy and sweet ready-to-drink lemonade, 500ml."},
        {"name": "Cold Brew Coffee", "price": 120, "emoji": "🧋", "desc": "Smooth cold brew coffee concentrate, 250ml bottle."},
        {"name": "Sparkling Water",  "price": 45,  "emoji": "💧", "desc": "Italian sparkling mineral water with light bubbles."},
        {"name": "Energy Drink",     "price": 85,  "emoji": "⚡", "desc": "Citrus blast energy drink with caffeine and B vitamins."},
        {"name": "Protein Shake",    "price": 150, "emoji": "💪", "desc": "Whey protein chocolate shake, ready to drink."},
        {"name": "Masala Chaas",     "price": 15,  "emoji": "🥛", "desc": "Spiced chaas with jeera and pudina, 200ml."},
        {"name": "Rose Sherbet",     "price": 35,  "emoji": "🌹", "desc": "Sweet rose syrup sherbet, great chilled in summer."},
        {"name": "Iced Tea",         "price": 40,  "emoji": "🍵", "desc": "Peach-flavored iced tea, refreshing and light."},
        {"name": "Sugarcane Juice",  "price": 20,  "emoji": "🎋", "desc": "Fresh pressed sugarcane juice with ginger and lemon."},
        {"name": "Turmeric Latte",   "price": 70,  "emoji": "🌿", "desc": "Golden milk turmeric latte mix, 200g jar."},
        {"name": "Masala Chai",      "price": 25,  "emoji": "☕", "desc": "Premixed masala chai powder with authentic spices."},
        {"name": "Grape Juice",      "price": 55,  "emoji": "🍇", "desc": "Dark grape juice, rich in resveratrol, 1L pack."},
        {"name": "Aloe Vera Drink",  "price": 65,  "emoji": "🌵", "desc": "Soothing aloe vera juice with bits, 500ml."},
        {"name": "Watermelon Juice", "price": 35,  "emoji": "🍉", "desc": "Freshly pressed watermelon juice, naturally sweet."},
    ],
}

EMOJI_MAP    = {p["name"]: p.get("emoji", "📦") for cat in ALL_PRODUCTS.values() for p in cat}
CATEGORY_MAP = {p["name"]: cat for cat, items in ALL_PRODUCTS.items() for p in items}


# ─────────────────────────────────────────────────────────────────────────────
#  DATABASE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_db():
    """Open a per-request SQLite connection stored on Flask's g object."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    """Create tables and seed data on first run."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    # ── users ──────────────────────────────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            created  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── products ───────────────────────────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    UNIQUE NOT NULL,
            category TEXT    NOT NULL,
            price    REAL    NOT NULL,
            emoji    TEXT    NOT NULL DEFAULT '📦',
            desc     TEXT    NOT NULL DEFAULT ''
        )
    """)

    # ── cart ───────────────────────────────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            product_id INTEGER NOT NULL REFERENCES products(id),
            qty        INTEGER NOT NULL DEFAULT 1,
            UNIQUE(username, product_id)
        )
    """)

    # ── orders ─────────────────────────────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL,
            bill_no     TEXT NOT NULL,
            grand_total REAL NOT NULL,
            ordered_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── order_items ────────────────────────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            qty        INTEGER NOT NULL,
            unit_price REAL    NOT NULL
        )
    """)

    db.commit()

    # ── seed users ──────────────────────────────────────────────────────────
    db.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "admin"))

    # ── seed products ───────────────────────────────────────────────────────
    for category, items in ALL_PRODUCTS.items():
        for p in items:
            db.execute("""
                INSERT OR IGNORE INTO products (name, category, price, emoji, desc)
                VALUES (?, ?, ?, ?, ?)
            """, (p["name"], category, p["price"], p.get("emoji", "📦"), p.get("desc", "")))

    db.commit()
    db.close()
    print("[FreshCart] Database initialised at", DATABASE)


# ─────────────────────────────────────────────────────────────────────────────
#  CART HELPERS  (now DB-backed, keyed by username)
# ─────────────────────────────────────────────────────────────────────────────
def db_get_cart(username):
    """Return list of dicts: {name, price, qty, emoji, category, product_id}"""
    db = get_db()
    rows = db.execute("""
        SELECT p.id AS product_id, p.name, p.price, p.emoji, p.category, c.qty
        FROM   cart c
        JOIN   products p ON p.id = c.product_id
        WHERE  c.username = ?
        ORDER  BY p.name
    """, (username,)).fetchall()
    return [dict(r) for r in rows]

def db_add_to_cart(username, product_name):
    db = get_db()
    row = db.execute("SELECT id FROM products WHERE name = ?", (product_name,)).fetchone()
    if not row:
        return
    pid = row["id"]
    db.execute("""
        INSERT INTO cart (username, product_id, qty)
        VALUES (?, ?, 1)
        ON CONFLICT(username, product_id) DO UPDATE SET qty = qty + 1
    """, (username, pid))
    db.commit()

def db_change_qty(username, product_name, delta):
    db = get_db()
    row = db.execute("SELECT id FROM products WHERE name = ?", (product_name,)).fetchone()
    if not row:
        return
    pid = row["id"]
    cart_row = db.execute("SELECT qty FROM cart WHERE username=? AND product_id=?",
                          (username, pid)).fetchone()
    if not cart_row:
        return
    new_qty = cart_row["qty"] + delta
    if new_qty <= 0:
        db.execute("DELETE FROM cart WHERE username=? AND product_id=?", (username, pid))
    else:
        db.execute("UPDATE cart SET qty=? WHERE username=? AND product_id=?",
                   (new_qty, username, pid))
    db.commit()

def db_remove_item(username, product_name):
    db = get_db()
    row = db.execute("SELECT id FROM products WHERE name = ?", (product_name,)).fetchone()
    if row:
        db.execute("DELETE FROM cart WHERE username=? AND product_id=?", (username, row["id"]))
        db.commit()

def db_clear_cart(username):
    db = get_db()
    db.execute("DELETE FROM cart WHERE username=?", (username,))
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def login():
    # If already logged in, go to dashboard
    #if "user" in session:
       # return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()

        # Validate against SQLite users table
        db   = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (u, p)
        ).fetchone()

        if user:
            session.clear()                # clear any stale data
            session["user"] = u
            session.permanent = False      # session expires when browser closes
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials. Use admin / admin"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    db       = get_db()
    username = session["user"]

    # Stats for the dashboard
    total_products  = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_orders    = db.execute("SELECT COUNT(*) FROM orders WHERE username=?",
                                 (username,)).fetchone()[0]
    total_spent     = db.execute(
        "SELECT COALESCE(SUM(grand_total),0) FROM orders WHERE username=?", (username,)
    ).fetchone()[0]
    recent_orders   = db.execute("""
        SELECT bill_no, grand_total, ordered_at
        FROM   orders WHERE username=?
        ORDER  BY ordered_at DESC LIMIT 5
    """, (username,)).fetchall()

    return render_template("dashboard.html",
                           username=username,
                           total_products=total_products,
                           total_orders=total_orders,
                           total_spent=total_spent,
                           recent_orders=recent_orders)


@app.route("/shop")
def shop():
    if "user" not in session:
        return redirect(url_for("login"))

    selected = request.args.get("category")
    db       = get_db()

    if selected and selected in ALL_PRODUCTS:
        rows = db.execute(
            "SELECT * FROM products WHERE category=? ORDER BY name", (selected,)
        ).fetchall()
        products = {selected: [dict(r) for r in rows]}
    else:
        products  = {}
        selected  = None
        for cat in ALL_PRODUCTS:
            rows = db.execute(
                "SELECT * FROM products WHERE category=? ORDER BY name", (cat,)
            ).fetchall()
            products[cat] = [dict(r) for r in rows]

    username   = session["user"]
    cart       = db_get_cart(username)
    cart_count = sum(i["qty"] for i in cart)

    return render_template("product.html",
                           products=products,
                           all_categories=list(ALL_PRODUCTS.keys()),
                           selected=selected,
                           cart_count=cart_count)


@app.route("/add_to_cart/<string:name>/<int:price>")
def add_to_cart(name, price):
    if "user" not in session:
        return redirect(url_for("login"))
    db_add_to_cart(session["user"], name)
    return redirect(url_for("shop"))


@app.route("/increase/<string:name>")
def increase(name):
    if "user" not in session:
        return redirect(url_for("login"))
    db_change_qty(session["user"], name, +1)
    return redirect(url_for("view_cart"))


@app.route("/decrease/<string:name>")
def decrease(name):
    if "user" not in session:
        return redirect(url_for("login"))
    db_change_qty(session["user"], name, -1)
    return redirect(url_for("view_cart"))


@app.route("/remove/<string:name>")
def remove(name):
    if "user" not in session:
        return redirect(url_for("login"))
    db_remove_item(session["user"], name)
    return redirect(url_for("view_cart"))


@app.route("/cart")
def view_cart():
    if "user" not in session:
        return redirect(url_for("login"))
    username   = session["user"]
    cart       = db_get_cart(username)
    total      = sum(i["price"] * i["qty"] for i in cart)
    cart_count = sum(i["qty"]              for i in cart)
    return render_template("cart.html", cart=cart, total=total, cart_count=cart_count)


@app.route("/clear_cart")
def clear_cart():
    if "user" not in session:
        return redirect(url_for("login"))
    db_clear_cart(session["user"])
    return redirect(url_for("shop"))


# ─────────────────────────────────────────────────────────────────────────────
#  BILL / INVOICE  (saves order to DB then streams PDF)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/bill")
def generate_bill():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    cart     = db_get_cart(username)
    if not cart:
        return redirect(url_for("view_cart"))

    now        = datetime.now()
    bill_no    = f"FC-{now.strftime('%Y%m%d%H%M%S')}"
    grand_total = sum(i["price"] * i["qty"] for i in cart)

    # ── Save order to SQLite ────────────────────────────────────────────────
    db = get_db()
    cur = db.execute(
        "INSERT INTO orders (username, bill_no, grand_total, ordered_at) VALUES (?,?,?,?)",
        (username, bill_no, grand_total, now.strftime("%Y-%m-%d %H:%M:%S"))
    )
    order_id = cur.lastrowid
    for item in cart:
        db.execute(
            "INSERT INTO order_items (order_id, product_id, qty, unit_price) VALUES (?,?,?,?)",
            (order_id, item["product_id"], item["qty"], item["price"])
        )
    db.commit()

    # ── Generate PDF ────────────────────────────────────────────────────────
    if not REPORTLAB_OK:
        # Fallback: plain-text invoice if reportlab not installed
        lines = [f"FreshCart Invoice  {bill_no}", f"Date: {now.strftime('%d %B %Y %I:%M %p')}", ""]
        for i, item in enumerate(cart, 1):
            lines.append(f"{i}. {item['name']}  x{item['qty']}  Rs.{item['price']*item['qty']}")
        lines += ["", f"GRAND TOTAL: Rs.{grand_total}", "", "Thank you for shopping with FreshCart!"]
        text = "\n".join(lines).encode("utf-8")
        buf  = io.BytesIO(text)
        fname = f"FreshCart_Invoice_{now.strftime('%Y%m%d_%H%M%S')}.txt"
        return send_file(buf, mimetype="text/plain", as_attachment=True, download_name=fname)

    # ── Full PDF with ReportLab ─────────────────────────────────────────────
    buf  = io.BytesIO()
    W, H = A4
    LM = RM = 18 * mm
    TM = BM = 16 * mm
    UW = W - LM - RM

    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=LM, rightMargin=RM,
                            topMargin=TM,  bottomMargin=BM)

    C_DARK   = colors.HexColor("#1a3d2b")
    C_FRESH  = colors.HexColor("#52b788")
    C_LIGHT  = colors.HexColor("#e8f5ee")
    C_MUTED  = colors.HexColor("#6b8c78")
    C_WHITE  = colors.white
    C_BORDER = colors.HexColor("#cce8d4")
    C_ROW2   = colors.HexColor("#f4fbf7")

    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    story = []

    # Header
    hdr = Table(
        [[Paragraph("<b>FreshCart</b>",
                    S("logo", fontName="Helvetica-Bold", fontSize=26, textColor=C_DARK, leading=30)),
          Paragraph("<b>TAX INVOICE</b>",
                    S("invt", fontName="Helvetica-Bold", fontSize=16, textColor=C_DARK,
                      alignment=TA_RIGHT, leading=20))],
         [Paragraph("Fresh groceries . Farm to doorstep",
                    S("tag", fontName="Helvetica", fontSize=8.5, textColor=C_MUTED, leading=12)),
          Paragraph(
              f"Invoice No: <b>{bill_no}</b><br/>"
              f"Date: <b>{now.strftime('%d %B %Y')}</b><br/>"
              f"Time: <b>{now.strftime('%I:%M %p')}</b>",
              S("meta", fontName="Helvetica", fontSize=8.5, textColor=C_MUTED,
                alignment=TA_RIGHT, leading=13))]],
        colWidths=[UW * 0.55, UW * 0.45]
    )
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
        ("PADDING",    (0, 0), (-1, -1), 14),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(
        "FreshCart Pvt. Ltd., Bengaluru, Karnataka - 560001  |  "
        "+91-9876543210  |  support@freshcart.in  |  GSTIN: 29AAAFC1234Z1Z5",
        S("info", fontName="Helvetica", fontSize=7.5, textColor=C_MUTED,
          alignment=TA_CENTER, leading=11)
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_FRESH, spaceAfter=5 * mm))

    # Items table
    COL_W = [UW*0.05, UW*0.30, UW*0.18, UW*0.15, UW*0.12, UW*0.20]

    def TH(txt):
        return Paragraph(f"<b>{txt}</b>",
                         S(f"th_{txt}", fontName="Helvetica-Bold", fontSize=8.5,
                           textColor=C_WHITE, alignment=TA_CENTER, leading=12))

    def TD(txt, align=TA_CENTER, bold=False):
        return Paragraph(str(txt),
                         S(f"td_{id(txt)}", fontName="Helvetica-Bold" if bold else "Helvetica",
                           fontSize=9, textColor=C_DARK, alignment=align, leading=12))

    rows = [[TH("#"), TH("Product"), TH("Category"), TH("Unit Price"), TH("Qty"), TH("Amount")]]
    for idx, item in enumerate(cart, 1):
        subtotal = item["price"] * item["qty"]
        rows.append([
            TD(str(idx)),
            Paragraph(f"<b>{item['name']}</b>",
                      S(f"pn{idx}", fontName="Helvetica-Bold", fontSize=9,
                        textColor=C_DARK, alignment=TA_LEFT, leading=12)),
            TD(item.get("category", CATEGORY_MAP.get(item["name"], "—"))),
            TD(f"Rs. {item['price']}"),
            TD(str(item["qty"])),
            TD(f"Rs. {subtotal}", bold=True),
        ])

    tbl = Table(rows, colWidths=COL_W, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0),  (-1, 0),  C_DARK),
        ("PADDING",        (0, 0),  (-1, 0),  10),
        ("VALIGN",         (0, 0),  (-1, -1), "MIDDLE"),
        ("PADDING",        (0, 1),  (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1),  (-1, -1), [C_WHITE, C_ROW2]),
        ("GRID",           (0, 0),  (-1, -1), 0.4, C_BORDER),
        ("LINEBELOW",      (0, 0),  (-1, 0),  1.5, C_FRESH),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))

    # Totals
    def TR(label, value, highlight=False):
        cc = "ffffff" if highlight else "0d1f17"
        vc = C_WHITE  if highlight else C_FRESH
        sz = 11       if highlight else 9
        return [
            Paragraph(f"<b><font color='#{cc}'>{label}</font></b>",
                      S(f"tl_{label}", fontName="Helvetica-Bold", fontSize=sz,
                        alignment=TA_RIGHT, leading=14)),
            Paragraph(f"<b>Rs. {value}</b>",
                      S(f"tv_{label}", fontName="Helvetica-Bold", fontSize=sz,
                        textColor=vc, alignment=TA_RIGHT, leading=14)),
        ]

    totals = Table([
        TR("Subtotal",           grand_total),
        TR("GST (0% Exempted)",  "0.00"),
        TR("Delivery Charges",   "0.00  (FREE)"),
        TR("GRAND TOTAL",        grand_total, highlight=True),
    ], colWidths=[UW * 0.70, UW * 0.30])
    totals.setStyle(TableStyle([
        ("PADDING",    (0, 0),  (-1, -1), 8),
        ("PADDING",    (0, -1), (-1, -1), 11),
        ("BACKGROUND", (0, -1), (-1, -1), C_DARK),
        ("LINEABOVE",  (0, -1), (-1, -1), 1.5, C_FRESH),
    ]))
    story.append(totals)
    story.append(Spacer(1, 7 * mm))

    # Payment info box
    total_units = sum(i["qty"] for i in cart)
    info_box = Table([[
        Paragraph(
            f"<b>Customer:</b> {username}     "
            f"<b>Items Ordered:</b> {total_units} unit(s) across {len(cart)} product(s)     "
            f"<b>Payment Status:</b> PAID     <b>Payment Mode:</b> Online / UPI",
            S("ibox", fontName="Helvetica", fontSize=8.5, textColor=C_DARK, leading=14)
        )
    ]], colWidths=[UW])
    info_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
        ("PADDING",    (0, 0), (-1, -1), 12),
        ("BOX",        (0, 0), (-1, -1), 1, C_FRESH),
    ]))
    story.append(info_box)
    story.append(Spacer(1, 6 * mm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.8, color=C_BORDER, spaceAfter=4 * mm))
    story.append(Paragraph(
        "Thank you for shopping with FreshCart! We hope to serve you again soon.<br/>"
        "This is a system-generated invoice. For queries: support@freshcart.in",
        S("foot", fontName="Helvetica", fontSize=7.5, textColor=C_MUTED,
          alignment=TA_CENTER, leading=12)
    ))

    doc.build(story)
    buf.seek(0)
    fname = f"FreshCart_Invoice_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=fname)


# ─────────────────────────────────────────────────────────────────────────────
#  ORDER HISTORY PAGE
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/orders")
def order_history():
    if "user" not in session:
        return redirect(url_for("login"))

    db       = get_db()
    username = session["user"]
    orders   = db.execute("""
        SELECT id, bill_no, grand_total, ordered_at
        FROM   orders WHERE username=?
        ORDER  BY ordered_at DESC
    """, (username,)).fetchall()

    order_list = []
    for o in orders:
        items = db.execute("""
            SELECT p.name, p.emoji, oi.qty, oi.unit_price
            FROM   order_items oi
            JOIN   products p ON p.id = oi.product_id
            WHERE  oi.order_id = ?
        """, (o["id"],)).fetchall()
        order_list.append({"order": dict(o), "items": [dict(i) for i in items]})

    return render_template("orders.html", order_list=order_list)


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

import sqlite3

# === DATABASE SETUP ===


def init_db() -> None:
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        link TEXT NOT NULL,
        stock INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()


# Insert sample products (run once)


def insert_sample_products() -> None:
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    products = [
        ("المنتج أ", "هذا منتج رائع لتلبية جميع احتياجاتك.",
         19.99, "https://yourstore.com/productA", 15),
        ("المنتج ب", "المنتج ب يقدم جودة وقيمة ممتازة.",
         29.99, "https://yourstore.com/productB", 7),
    ]
    cursor.executemany(
        "INSERT INTO products (name, description, price, link, stock) VALUES (?, ?, ?, ?, ?)", products)
    conn.commit()
    conn.close()

# Fetch all products


def get_all_products() -> list:
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Fetch single product by id


def get_product(prod_id: str):
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, price, link FROM products WHERE id=?", (prod_id,))
    product = cursor.fetchone()
    conn.close()
    return product

# === DATABASE HELPERS ===
# Fetch single product by name (case-insensitive search)


def get_product_by_name(name: str):
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, price, link FROM products WHERE name LIKE ?", ('%' + name + '%',))
    product = cursor.fetchone()
    conn.close()
    return product


def list_products():
    rows = get_all_products()
    if not rows:
        return "لا توجد منتجات متاحة حالياً."
    product_list = "المنتجات المتاحة:\n"
    for row in rows:
        product_list += f"{row[0]}: {row[1]} - {row[2]}$)\n"
    return product_list

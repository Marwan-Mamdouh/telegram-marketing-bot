import sqlite3
import re
from rapidfuzz import fuzz, process

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


# def get_all_products() -> list:
#     conn = sqlite3.connect("store.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, name, price FROM products")
#     rows = cursor.fetchall()
#     conn.close()
#     return rows

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


# === NORMALIZATION FOR ARABIC ===
def normalize_arabic(text: str) -> str:
    text = re.sub(r"[إأٱآا]", "ا", text)   # unify alif forms
    text = re.sub(r"ى", "ي", text)         # unify alif maqsura
    text = re.sub(r"ؤ", "و", text)
    text = re.sub(r"ئ", "ي", text)
    text = re.sub(r"ة", "ه", text)         # unify ta marbuta
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)  # remove diacritics & tatweel
    return text.strip()


# === FETCH PRODUCTS ===
def get_all_products() -> list:
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price, link FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows


# === SEARCH PRODUCT BY NAME (FUZZY) ===
def search_product_by_name(query: str, limit: int = 1):
    products = get_all_products()
    if not products:
        return None

    query_norm = normalize_arabic(query)
    # Make list of normalized product names
    product_names = [(p[0], normalize_arabic(p[1]), p) for p in products]

    # Use RapidFuzz to get best match
    matches = process.extract(query_norm,
                              {pid: name for pid, name, _ in product_names},
                              scorer=fuzz.partial_ratio,
                              limit=limit)

    if not matches:
        return None

    # matches = [(matched_text, score, product_id)]
    best_match = matches[0]
    best_score = best_match[1]
    best_pid = best_match[2]

    if best_score > 60:  # threshold (tweakable)
        for pid, _, product in product_names:
            if pid == best_pid:
                return product
    return None

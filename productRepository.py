import sqlite3
import re
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer, util
# import numpy as np

# === LOAD NLP MODEL ===
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Cache embeddings (to avoid recomputing each search)
product_cache = {}

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
        ("تيشرت بولو اسود", "هذا منتج رائع لتلبية جميع احتياجاتك.",
         19.99, "https://yourstore.com/productA"),
        ("قميص كوم اسود", "المنتج ب يقدم جودة وقيمة ممتازة.",
         29.99, "https://yourstore.com/productB"),
    ]
    cursor.executemany(
        "INSERT INTO products (name, description, price, link) VALUES (?, ?, ?, ?)", products)
    conn.commit()
    conn.close()


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
# Fetch all products
def get_all_products() -> list:
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price, link FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows


# === SEARCH PRODUCTS BY NAME (FUZZY, MULTIPLE) ===
def build_product_cache():
    """
    Precompute embeddings for all products and store in memory
    """
    global product_cache
    products = get_all_products()
    product_cache = {}

    texts = [f"{p[1]} {p[2]}" for p in products]  # name + description
    embeddings = model.encode(texts, convert_to_tensor=True)

    for i, product in enumerate(products):
        product_cache[product[0]] = {
            "product": product,
            "embedding": embeddings[i]
        }


def semantic_search(query: str, top_k: int = 5, threshold: float = 0.45):
    """
    Search products using semantic similarity
    """
    if not product_cache:  # Build cache if empty
        build_product_cache()

    query_emb = model.encode(query, convert_to_tensor=True)
    results = []

    for pid, data in product_cache.items():
        score = util.cos_sim(query_emb, data["embedding"]).item()
        if score >= threshold:
            results.append((score, data["product"]))

    results.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in results[:top_k]]


def search_products_by_name(query: str, limit: int = 5, threshold: int = 60):
    products = get_all_products()
    if not products:
        return []

    query_norm = normalize_arabic(query)
    product_names = [(p[0], normalize_arabic(p[1]), p) for p in products]

    # Create {id: normalized_name}
    lookup = {pid: name for pid, name, _ in product_names}

    # Fuzzy match
    matches = process.extract(
        query_norm,
        lookup,
        scorer=fuzz.partial_ratio,
        limit=limit
    )

    results = []
    for _, score, pid in matches:
        if score >= threshold:  # accept only if score is high enough
            for real_pid, _, product in product_names:
                if real_pid == pid:
                    results.append(product)

    return results

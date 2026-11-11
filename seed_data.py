
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# ==========================================
# GREENLEAF GROCERS - SAMPLE DATA GENERATOR
# ==========================================

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent

# Change this only after confirming your app's database path.
DB_PATH = BASE_DIR / "instance" / "greenleaf.db"

PRODUCT_COUNT = 60
SALES_COUNT = 550

CATEGORIES = {
    "Rice": ["Basmati Rice", "Sona Masoori Rice", "Brown Rice"],
    "Dairy": ["Milk", "Curd", "Butter", "Cheese"],
    "Beverages": ["Orange Juice", "Apple Juice", "Tea", "Coffee"],
    "Snacks": ["Biscuits", "Chips", "Chocolates"],
    "Groceries": ["Sugar", "Salt", "Wheat Flour", "Toor Dal"],
    "Oils": ["Sunflower Oil", "Groundnut Oil", "Coconut Oil"],
    "Personal Care": ["Soap", "Shampoo", "Toothpaste"],
    "Household": ["Detergent", "Dishwash Liquid", "Floor Cleaner"]
}

def create_tables(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        unit_price REAL NOT NULL,
        stock_qty INTEGER NOT NULL,
        reorder_level INTEGER NOT NULL,
        expiry_date TEXT
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT
    );

    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_date TEXT NOT NULL,
        sale_time TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS sale_items (
        sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(sale_id) REFERENCES sales(sale_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    );
    """)
    conn.commit()


def insert_users(conn):
    users = [
        ("admin", "demo_admin_hash", "admin"),
        ("cashier1", "demo_cashier_hash", "cashier"),
        ("cashier2", "demo_cashier_hash", "cashier")
    ]

    for user in users:
        conn.execute("""
            INSERT OR IGNORE INTO users
            (username, password_hash, role)
            VALUES (?, ?, ?)
        """, user)

    conn.commit()

    return [
        row[0] for row in conn.execute(
            "SELECT user_id FROM users WHERE role='cashier'"
        ).fetchall()
    ]


def insert_suppliers(conn):
    suppliers = [
        ("Fresh Foods Suppliers", "9876543210", "fresh@example.com"),
        ("ABC Wholesale Traders", "9876543211", "abc@example.com"),
        ("Green Valley Distributors", "9876543212", "green@example.com"),
        ("Daily Needs Agency", "9876543213", "daily@example.com"),
        ("Sri Lakshmi Traders", "9876543214", "lakshmi@example.com")
    ]

    for supplier in suppliers:
        conn.execute("""
            INSERT INTO suppliers (name, phone, email)
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM suppliers WHERE name=?
            )
        """, (*supplier, supplier[0]))

    conn.commit()


def insert_products(conn):
    products = []

    all_names = []

    for category, names in CATEGORIES.items():
        for name in names:
            all_names.append((name, category))

    while len(all_names) < PRODUCT_COUNT:
        category = random.choice(list(CATEGORIES.keys()))
        base_name = random.choice(CATEGORIES[category])
        name = f"{base_name} {len(all_names) + 1}"
        all_names.append((name, category))

    today = datetime.now().date()

    for name, category in all_names[:PRODUCT_COUNT]:
        price = round(random.uniform(10, 300), 2)
        stock = random.randint(0, 100)
        reorder = random.randint(10, 25)

        expiry = today + timedelta(days=random.randint(-5, 365))

        products.append((
            name,
            category,
            price,
            stock,
            reorder,
            expiry.isoformat()
        ))

    for product in products:
        conn.execute("""
            INSERT INTO products
            (name, category, unit_price, stock_qty,
             reorder_level, expiry_date)
            SELECT ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM products WHERE name=?
            )
        """, (*product, product[0]))

    conn.commit()


def insert_sales(conn, cashier_ids):
    if not cashier_ids:
        raise RuntimeError("No cashier users found.")

    product_rows = conn.execute("""
        SELECT product_id, unit_price, stock_qty
        FROM products
        WHERE stock_qty > 0
    """).fetchall()

    if not product_rows:
        raise RuntimeError("No products with stock available.")

    today = datetime.now().date()
    start_date = today - timedelta(days=180)

    sales_created = 0
    items_created = 0

    for _ in range(SALES_COUNT):
        sale_date = start_date + timedelta(
            days=random.randint(0, 180)
        )

        sale_time = (
            datetime.min + timedelta(
                seconds=random.randint(0, 86399)
            )
        ).time().strftime("%H:%M:%S")

        selected = random.sample(
            product_rows,
            k=min(random.randint(1, 4), len(product_rows))
        )

        sale_items = []
        total = 0

        for product_id, price, stock in selected:
            quantity = random.randint(1, min(stock, 5))

            if quantity <= 0:
                continue

            amount = round(price * quantity, 2)

            sale_items.append(
                (product_id, quantity, price)
            )

            total += amount

        if not sale_items:
            continue

        cursor = conn.execute("""
            INSERT INTO sales
            (sale_date, sale_time, user_id, total_amount)
            VALUES (?, ?, ?, ?)
        """, (
            sale_date.isoformat(),
            sale_time,
            random.choice(cashier_ids),
            round(total, 2)
        ))

        sale_id = cursor.lastrowid

        for product_id, quantity, price in sale_items:
            conn.execute("""
                INSERT INTO sale_items
                (sale_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (
                sale_id,
                product_id,
                quantity,
                price
            ))

            items_created += 1

        sales_created += 1

    conn.commit()

    return sales_created, items_created


def main():
    print("\nGreenLeaf Grocers Sample Data Generator")
    print("----------------------------------------")
    print("Database:", DB_PATH)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        create_tables(conn)
        cashier_ids = insert_users(conn)
        insert_suppliers(conn)
        insert_products(conn)

        sales, items = insert_sales(conn, cashier_ids)

        products = conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        total_sales = conn.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

        print("\nData generation completed!")
        print("----------------------------------------")
        print("Products:", products)
        print("Sales:", total_sales)
        print("New sales generated:", sales)
        print("Sale items generated:", items)

        print("\nDatabase successfully populated.")

    except Exception as error:
        conn.rollback()
        print("\nERROR:", error)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()

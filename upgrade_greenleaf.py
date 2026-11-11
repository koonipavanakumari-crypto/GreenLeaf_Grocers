
from pathlib import Path
from datetime import date, datetime, timedelta
import shutil
import re

# ============================================================
# GREENLEAF GROCERS - COMPLETE PROJECT UPGRADE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
APP_FILE = BASE_DIR / "app.py"

TEMPLATE_DIR.mkdir(exist_ok=True)

print("\nGREENLEAF GROCERS PROJECT UPGRADE")
print("=" * 60)


# ============================================================
# 1. SALES REPORTS TEMPLATE
# ============================================================

reports_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics - GreenLeaf Grocers</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f3;
            margin: 0;
            padding: 25px;
        }

        h1, h2 {
            color: #245c35;
        }

        .nav {
            margin-bottom: 20px;
        }

        .nav a, button {
            display: inline-block;
            background: #245c35;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            margin: 4px;
            cursor: pointer;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .card, .panel {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px #ddd;
        }

        .card h3 {
            color: #666;
            font-size: 15px;
        }

        .card p {
            color: #245c35;
            font-size: 25px;
            font-weight: bold;
        }

        .panel {
            margin-top: 20px;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }

        th {
            background: #245c35;
            color: white;
        }

        input {
            padding: 9px;
            margin: 5px;
        }

        .chart {
            max-width: 850px;
            margin: auto;
        }
    </style>
</head>

<body>

<h1>GreenLeaf Grocers - Sales Analytics</h1>

<div class="nav">
    <a href="/dashboard">Dashboard</a>
    <a href="/alerts">Inventory Alerts</a>
    <a href="/products">Products</a>
    <a href="/products/import">Import CSV</a>
    <a href="/products/export">Export Products</a>
    <a href="/reports/export">Export Sales</a>
</div>

<div class="panel">
    <h2>Filter Sales by Date</h2>

    <form method="GET" action="/reports">
        <label>From:</label>
        <input type="date" name="start" value="{{ start }}">

        <label>To:</label>
        <input type="date" name="end" value="{{ end }}">

        <button type="submit">Apply Filter</button>
    </form>
</div>

<div class="cards">

    <div class="card">
        <h3>Total Revenue</h3>
        <p>₹{{ "%.2f"|format(revenue) }}</p>
    </div>

    <div class="card">
        <h3>Total Bills</h3>
        <p>{{ total_bills }}</p>
    </div>

    <div class="card">
        <h3>Average Bill</h3>
        <p>₹{{ "%.2f"|format(average_bill) }}</p>
    </div>

    <div class="card">
        <h3>Total Products</h3>
        <p>{{ product_count }}</p>
    </div>

</div>

<div class="panel">
    <h2>Daily Revenue Chart</h2>
    <div class="chart">
        <canvas id="salesChart"></canvas>
    </div>
</div>

<div class="panel">
    <h2>Top 10 Selling Products</h2>

    <table>
        <tr>
            <th>Product</th>
            <th>Quantity Sold</th>
            <th>Sales Amount</th>
        </tr>

        {% for product in top_products %}
        <tr>
            <td>{{ product.name }}</td>
            <td>{{ product.quantity }}</td>
            <td>₹{{ "%.2f"|format(product.amount) }}</td>
        </tr>
        {% else %}
        <tr>
            <td colspan="3">No sales available.</td>
        </tr>
        {% endfor %}
    </table>
</div>

<div class="panel">
    <h2>Category Sales Distribution</h2>
    <div class="chart">
        <canvas id="categoryChart"></canvas>
    </div>
</div>

<div class="panel">
    <h2>Slow Moving Products</h2>
    <p>Products with no sales in the last 30 days.</p>

    <table>
        <tr>
            <th>Product</th>
            <th>Category</th>
            <th>Available Stock</th>
        </tr>

        {% for product in slow_products %}
        <tr>
            <td>{{ product.name }}</td>
            <td>{{ product.category }}</td>
            <td>{{ product.stock_qty }}</td>
        </tr>
        {% else %}
        <tr>
            <td colspan="3">No slow-moving products found.</td>
        </tr>
        {% endfor %}
    </table>
</div>

<script>
const dailyLabels = {{ daily_labels | tojson }};
const dailyValues = {{ daily_values | tojson }};

new Chart(document.getElementById("salesChart"), {
    type: "bar",
    data: {
        labels: dailyLabels,
        datasets: [{
            label: "Daily Revenue",
            data: dailyValues,
            backgroundColor: "#4b9b61"
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: { beginAtZero: true }
        }
    }
});

const categoryLabels = {{ category_labels | tojson }};
const categoryValues = {{ category_values | tojson }};

new Chart(document.getElementById("categoryChart"), {
    type: "pie",
    data: {
        labels: categoryLabels,
        datasets: [{
            data: categoryValues
        }]
    },
    options: {
        responsive: true
    }
});
</script>

</body>
</html>
"""

(TEMPLATE_DIR / "reports.html").write_text(
    reports_html, encoding="utf-8"
)


# ============================================================
# 2. INVENTORY ALERTS TEMPLATE
# ============================================================

alerts_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Inventory Alerts - GreenLeaf Grocers</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f3;
            padding: 25px;
        }

        h1, h2 {
            color: #245c35;
        }

        .panel {
            background: white;
            padding: 20px;
            margin-top: 20px;
            border-radius: 10px;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }

        th {
            background: #245c35;
            color: white;
        }

        .warning {
            color: #d97706;
            font-weight: bold;
        }

        .danger {
            color: red;
            font-weight: bold;
        }

        a {
            display: inline-block;
            background: #245c35;
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 5px;
            margin: 4px;
        }
    </style>
</head>

<body>

<h1>Inventory Alerts</h1>

<a href="/dashboard">Dashboard</a>
<a href="/products">Products</a>
<a href="/reports">Sales Reports</a>

<div class="panel">
    <h2>Low Stock Products</h2>

    <table>
        <tr>
            <th>Product</th>
            <th>Category</th>
            <th>Current Stock</th>
            <th>Reorder Level</th>
        </tr>

        {% for p in low_stock %}
        <tr>
            <td>{{ p.name }}</td>
            <td>{{ p.category }}</td>
            <td class="warning">{{ p.stock_qty }}</td>
            <td>{{ p.reorder_level }}</td>
        </tr>
        {% else %}
        <tr><td colspan="4">No low-stock products.</td></tr>
        {% endfor %}
    </table>
</div>

<div class="panel">
    <h2>Products Near Expiry - Within 15 Days</h2>

    <table>
        <tr>
            <th>Product</th>
            <th>Expiry Date</th>
            <th>Stock</th>
        </tr>

        {% for p in near_expiry %}
        <tr>
            <td>{{ p.name }}</td>
            <td class="warning">{{ p.expiry_date }}</td>
            <td>{{ p.stock_qty }}</td>
        </tr>
        {% else %}
        <tr><td colspan="3">No products near expiry.</td></tr>
        {% endfor %}
    </table>
</div>

<div class="panel">
    <h2>Expired Products</h2>

    <table>
        <tr>
            <th>Product</th>
            <th>Expiry Date</th>
            <th>Stock</th>
        </tr>

        {% for p in expired %}
        <tr>
            <td>{{ p.name }}</td>
            <td class="danger">{{ p.expiry_date }}</td>
            <td>{{ p.stock_qty }}</td>
        </tr>
        {% else %}
        <tr><td colspan="3">No expired products.</td></tr>
        {% endfor %}
    </table>
</div>

</body>
</html>
"""

(TEMPLATE_DIR / "alerts.html").write_text(
    alerts_html, encoding="utf-8"
)


# ============================================================
# 3. CSV IMPORT TEMPLATE
# ============================================================

import_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Import Products - GreenLeaf Grocers</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f3;
            padding: 30px;
        }

        .box {
            max-width: 600px;
            margin: 30px auto;
            background: white;
            padding: 25px;
            border-radius: 10px;
        }

        h2 {
            color: #245c35;
        }

        button, a {
            background: #245c35;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
        }

        input {
            margin: 15px 0;
        }

        .message {
            margin: 10px 0;
            padding: 10px;
            background: #edf5ed;
        }
    </style>
</head>

<body>

<div class="box">
    <h2>Import Products from CSV</h2>

    <p>Required CSV columns:</p>

    <p>
        name, category, unit_price, stock_qty, reorder_level
    </p>

    <p>Optional column: expiry_date (YYYY-MM-DD)</p>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            <div class="message">{{ message }}</div>
        {% endfor %}
    {% endwith %}

    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" accept=".csv" required>
        <br>
        <button type="submit">Import Products</button>
    </form>

    <br><br>
    <a href="/products">Back to Products</a>
    <a href="/products/export">Export Products</a>
</div>

</body>
</html>
"""

(TEMPLATE_DIR / "import_products.html").write_text(
    import_html, encoding="utf-8"
)


# ============================================================
# 4. CHECK APP.PY
# ============================================================

if not APP_FILE.exists():
    raise FileNotFoundError(
        "app.py was not found. Keep this script in your project root."
    )

app_code = APP_FILE.read_text(encoding="utf-8")

if "def admin_required" not in app_code:
    raise RuntimeError(
        "admin_required decorator not found in app.py. "
        "Your existing app.py must contain the admin_required decorator."
    )

if "GREENLEAF_UPGRADE_ROUTES_V2" in app_code:
    print("Upgrade routes V2 already exist in app.py.")
    print("No duplicate routes were added.")

else:

    main_pattern = re.compile(
        r'(?m)^if __name__\s*==\s*["\']__main__["\']\s*:'
    )

    match = main_pattern.search(app_code)

    if not match:
        raise RuntimeError(
            "Could not find the main execution block in app.py. "
            "No changes were made to app.py."
        )

    backup_file = BASE_DIR / "app.py.before_upgrade.backup"

    if not backup_file.exists():
        shutil.copy2(APP_FILE, backup_file)

    # ========================================================
    # 5. ROUTES TO ADD TO APP.PY
    # ========================================================

    routes_code = r'''

# ============================================================
# GREENLEAF_UPGRADE_ROUTES_V2
# Reports, Alerts, CSV Import and CSV Export
# ============================================================

@app.route("/reports")
@admin_required
def greenleaf_reports():
    from datetime import date, datetime, timedelta
    from collections import defaultdict
    from flask import render_template, request
    from database.models import Product, Sale, SaleItem

    start_text = request.args.get("start", "")
    end_text = request.args.get("end", "")

    try:
        start_date = (
            datetime.strptime(start_text, "%Y-%m-%d").date()
            if start_text else date.today().replace(day=1)
        )

        end_date = (
            datetime.strptime(end_text, "%Y-%m-%d").date()
            if end_text else date.today()
        )

        if start_date > end_date:
            raise ValueError("Start date cannot be after end date.")

    except ValueError:
        start_date = date.today().replace(day=1)
        end_date = date.today()

    sales = Sale.query.filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).order_by(Sale.sale_date).all()

    revenue = sum(
        float(sale.total_amount or 0)
        for sale in sales
    )

    total_bills = len(sales)

    average_bill = (
        revenue / total_bills
        if total_bills else 0
    )

    product_count = Product.query.count()

    daily_totals = defaultdict(float)

    product_totals = defaultdict(
        lambda: {
            "name": "Unknown",
            "quantity": 0,
            "amount": 0
        }
    )

    category_totals = defaultdict(float)

    for sale in sales:

        day_key = sale.sale_date.strftime("%Y-%m-%d")

        daily_totals[day_key] += float(
            sale.total_amount or 0
        )

        for item in sale.items:

            product = db.session.get(
                Product, item.product_id
            )

            if product is None:
                continue

            key = product.product_id

            line_total = (
                float(item.price or 0) * item.quantity
            )

            product_totals[key]["name"] = product.name

            product_totals[key]["quantity"] += item.quantity

            product_totals[key]["amount"] += line_total

            category_totals[product.category] += line_total

    top_products = sorted(
        product_totals.values(),
        key=lambda item: item["quantity"],
        reverse=True
    )[:10]

    cutoff_date = date.today() - timedelta(days=30)

    sold_product_rows = db.session.query(
        SaleItem.product_id
    ).join(
        Sale,
        Sale.sale_id == SaleItem.sale_id
    ).filter(
        Sale.sale_date >= cutoff_date
    ).distinct().all()

    sold_product_ids = {
        row[0] for row in sold_product_rows
    }

    if sold_product_ids:
        slow_products = Product.query.filter(
            ~Product.product_id.in_(sold_product_ids)
        ).all()
    else:
        slow_products = Product.query.all()

    return render_template(
        "reports.html",
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        revenue=revenue,
        total_bills=total_bills,
        average_bill=average_bill,
        product_count=product_count,
        daily_labels=list(daily_totals.keys()),
        daily_values=list(daily_totals.values()),
        top_products=top_products,
        category_labels=list(category_totals.keys()),
        category_values=list(category_totals.values()),
        slow_products=slow_products
    )


@app.route("/alerts")
@admin_required
def greenleaf_inventory_alerts():
    from datetime import date, timedelta
    from flask import render_template
    from database.models import Product

    today = date.today()
    expiry_limit = today + timedelta(days=15)

    low_stock = Product.query.filter(
        Product.stock_qty <= Product.reorder_level
    ).all()

    near_expiry = Product.query.filter(
        Product.expiry_date >= today,
        Product.expiry_date <= expiry_limit
    ).all()

    expired = Product.query.filter(
        Product.expiry_date < today
    ).all()

    return render_template(
        "alerts.html",
        low_stock=low_stock,
        near_expiry=near_expiry,
        expired=expired
    )


@app.route("/reports/export")
@admin_required
def greenleaf_export_sales():
    import csv
    from io import StringIO
    from flask import Response
    from database.models import Product

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Sale ID",
        "Date",
        "Time",
        "Product",
        "Quantity",
        "Unit Price",
        "Line Total",
        "Bill Total"
    ])

    sales = Sale.query.order_by(
        Sale.sale_date.desc()
    ).all()

    for sale in sales:

        for item in sale.items:

            product = db.session.get(
                Product, item.product_id
            )

            writer.writerow([
                sale.sale_id,
                sale.sale_date,
                sale.sale_time,
                product.name if product else "Unknown",
                item.quantity,
                item.price,
                item.quantity * item.price,
                sale.total_amount
            ])

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=greenleaf_sales.csv"
        }
    )


@app.route("/products/export")
@admin_required
def greenleaf_export_products():
    import csv
    from io import StringIO
    from flask import Response
    from database.models import Product

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "name",
        "category",
        "unit_price",
        "stock_qty",
        "reorder_level",
        "expiry_date"
    ])

    products = Product.query.order_by(
        Product.name
    ).all()

    for product in products:

        writer.writerow([
            product.name,
            product.category,
            product.unit_price,
            product.stock_qty,
            product.reorder_level,
            (
                product.expiry_date.isoformat()
                if product.expiry_date else ""
            )
        ])

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=greenleaf_products.csv"
        }
    )


@app.route("/products/import", methods=["GET", "POST"])
@admin_required
def greenleaf_import_products():
    import csv
    from io import TextIOWrapper
    from datetime import datetime
    from flask import (
        request, flash, redirect,
        url_for, render_template
    )
    from database.models import Product

    if request.method == "POST":

        uploaded_file = request.files.get("file")

        if not uploaded_file or not uploaded_file.filename:

            flash("Please select a CSV file.", "error")

            return redirect(
                url_for("greenleaf_import_products")
            )

        if not uploaded_file.filename.lower().endswith(".csv"):

            flash("Only CSV files are allowed.", "error")

            return redirect(
                url_for("greenleaf_import_products")
            )

        try:

            stream = TextIOWrapper(
                uploaded_file.stream,
                encoding="utf-8-sig",
                newline=""
            )

            reader = csv.DictReader(stream)

            required_columns = {
                "name",
                "category",
                "unit_price",
                "stock_qty",
                "reorder_level"
            }

            if (
                not reader.fieldnames
                or not required_columns.issubset(
                    set(reader.fieldnames)
                )
            ):

                raise ValueError(
                    "Required CSV columns: name, category, "
                    "unit_price, stock_qty, reorder_level. "
                    "expiry_date is optional."
                )

            imported_count = 0

            for row in reader:

                name = (row.get("name") or "").strip()

                category = (
                    row.get("category") or ""
                ).strip()

                if not name or not category:

                    raise ValueError(
                        "Product name and category cannot be empty."
                    )

                price = float(row["unit_price"])

                stock = int(row["stock_qty"])

                reorder = int(row["reorder_level"])

                if price < 0 or stock < 0 or reorder < 0:

                    raise ValueError(
                        "Price, stock and reorder level "
                        "cannot be negative."
                    )

                expiry_text = (
                    row.get("expiry_date") or ""
                ).strip()

                expiry = (
                    datetime.strptime(
                        expiry_text, "%Y-%m-%d"
                    ).date()
                    if expiry_text else None
                )

                product = Product(
                    name=name,
                    category=category,
                    unit_price=price,
                    stock_qty=stock,
                    reorder_level=reorder,
                    expiry_date=expiry
                )

                db.session.add(product)

                imported_count += 1

            db.session.commit()

            flash(
                str(imported_count)
                + " products imported successfully.",
                "success"
            )

        except Exception as error:

            db.session.rollback()

            flash(
                "Import failed: " + str(error),
                "error"
            )

        return redirect(
            url_for("greenleaf_import_products")
        )

    return render_template("import_products.html")


'''

    # Insert the route code before the main block.
    # String slicing avoids regex replacement escape errors.

    insert_position = match.start()

    updated_app = (
        app_code[:insert_position]
        + routes_code
        + "\n\n"
        + app_code[insert_position:]
    )

    APP_FILE.write_text(
        updated_app,
        encoding="utf-8"
    )

    print("New routes successfully added to app.py.")


# ============================================================
# 6. COMPLETION MESSAGE
# ============================================================

print("\n" + "=" * 60)
print("GREENLEAF GROCERS UPGRADE COMPLETED")
print("=" * 60)

print("\nCreated HTML templates:")
print("1. templates/reports.html")
print("2. templates/alerts.html")
print("3. templates/import_products.html")

print("\nAdded Flask routes:")
print("1. /reports")
print("2. /alerts")
print("3. /reports/export")
print("4. /products/export")
print("5. /products/import")

print("\nBackup:")
print("app.py.before_upgrade.backup")

print("\nNEXT STEPS:")
print("1. Run: python app.py")
print("2. Login with your admin account.")
print("3. Open: http://127.0.0.1:5000/reports")
print("4. Open: http://127.0.0.1:5000/alerts")
print("5. Open: http://127.0.0.1:5000/products/import")

print("\nUpgrade script finished.")
git remote add origin https://github.com/YOUR_USERNAME/GreenLeaf-Grocers.git

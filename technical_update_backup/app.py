
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

from werkzeug.security import (
    generate_password_hash, check_password_hash
)

from config import Config
from database.db import db
from database.models import User, Product, Supplier, Sale, SaleItem


# ==========================================
# 1. FLASK APPLICATION INITIALIZATION
# ==========================================

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs("instance", exist_ok=True)

db.init_app(app)


# ==========================================
# 2. DATABASE AND DEMO USERS
# ==========================================

with app.app_context():

    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)

    if not User.query.filter_by(username="cashier").first():
        cashier = User(
            username="cashier",
            password_hash=generate_password_hash("cashier123"),
            role="cashier"
        )
        db.session.add(cashier)

    db.session.commit()


# ==========================================
# 3. LOGIN REQUIRED
# ==========================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# ==========================================
# 4. ADMIN REQUIRED
# ==========================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access only!")
            return redirect(url_for("dashboard"))

        return function(*args, **kwargs)

    return wrapper


# ==========================================
# 5. HOME
# ==========================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ==========================================
# 6. LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):

            session["user_id"] = user.user_id
            session["username"] = user.username
            session["role"] = user.role

            return redirect(url_for("dashboard"))

        flash("Invalid username or password!")

    return render_template("login.html")


# ==========================================
# 7. DASHBOARD WITH BILLING INFORMATION
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():

    total_sales = Sale.query.count()

    total_revenue = db.session.query(
        db.func.sum(Sale.total_amount)
    ).scalar() or 0

    total_products = Product.query.count()

    low_stock = Product.query.filter(
        Product.stock_qty <= Product.reorder_level
    ).count()

    recent_sales = Sale.query.order_by(
        Sale.sale_id.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        total_sales=total_sales,
        total_revenue=total_revenue,
        total_products=total_products,
        low_stock=low_stock,
        recent_sales=recent_sales
    )

@app.route("/billing", methods=["GET", "POST"])
@login_required
def billing():

    if request.method == "GET":

        products = Product.query.order_by(Product.name).all()

        return render_template(
            "billing.html",
            products=products
        )

    try:

        product_ids = request.form.getlist("product_id")
        quantities = request.form.getlist("quantity")

        discount = float(request.form.get("discount", 0))

        if discount < 0:
            flash("Discount cannot be negative!")
            return redirect(url_for("billing"))

        cart = {}

        for pid, qty in zip(product_ids, quantities):

            if not pid or not qty:
                continue

            product_id = int(pid)
            quantity = int(qty)

            if quantity <= 0:
                flash("Quantity must be greater than zero!")
                return redirect(url_for("billing"))

            cart[product_id] = cart.get(product_id, 0) + quantity

        if not cart:
            flash("Please select at least one product!")
            return redirect(url_for("billing"))

        subtotal = 0
        selected_products = {}

        for product_id, quantity in cart.items():

            product = db.session.get(Product, product_id)

            if product is None:
                flash("Product not found!")
                return redirect(url_for("billing"))

            if quantity > product.stock_qty:
                flash(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.stock_qty}"
                )
                return redirect(url_for("billing"))

            selected_products[product_id] = product
            subtotal += product.unit_price * quantity

        if discount > subtotal:
            flash("Discount cannot exceed bill amount!")
            return redirect(url_for("billing"))

        total_amount = subtotal - discount
        now = datetime.now()

        sale = Sale(
            sale_date=now.date(),
            sale_time=now.strftime("%H:%M:%S"),
            user_id=session["user_id"],
            total_amount=round(total_amount, 2),
            discount=round(discount, 2)
        )

        db.session.add(sale)
        db.session.flush()

        for product_id, quantity in cart.items():

            product = selected_products[product_id]

            sale_item = SaleItem(
                sale_id=sale.sale_id,
                product_id=product_id,
                quantity=quantity,
                price=product.unit_price
            )

            db.session.add(sale_item)
            product.stock_qty -= quantity

        db.session.commit()

        flash("Bill generated successfully!")

        return redirect(url_for("view_bill", sale_id=sale.sale_id))

    except (ValueError, TypeError):

        db.session.rollback()
        flash("Enter valid product quantities and discount!")
        return redirect(url_for("billing"))

    except Exception:

        db.session.rollback()
        app.logger.exception("Billing error")
        flash("Unable to generate bill!")
        return redirect(url_for("billing"))


# ==========================================
# 9. VIEW BILL
# ==========================================

@app.route("/bill/<int:sale_id>")
@login_required
def view_bill(sale_id):

    sale = db.session.get(Sale, sale_id)

    if sale is None:
        return "Bill not found!", 404

    items = (
        db.session.query(SaleItem, Product)
        .join(Product, SaleItem.product_id == Product.product_id)
        .filter(SaleItem.sale_id == sale_id)
        .all()
    )

    return render_template(
        "bill.html",
        sale=sale,
        items=items
    )


# ==========================================
# 10. VIEW AND SEARCH PRODUCTS
# ==========================================

@app.route("/products")
@admin_required
def products():

    search = request.args.get("search", "").strip()

    if search:

        product_list = Product.query.filter(
            Product.name.ilike(f"%{search}%")
        ).order_by(Product.name).all()

    else:

        product_list = Product.query.order_by(Product.name).all()

    return render_template(
        "products.html",
        products=product_list,
        search=search
    )


# ==========================================
# 11. ADD PRODUCT
# ==========================================

@app.route("/products/add", methods=["GET", "POST"])
@admin_required
def add_product():

    if request.method == "POST":

        try:

            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()

            unit_price = float(request.form.get("unit_price", 0))
            stock_qty = int(request.form.get("stock_qty", 0))
            reorder_level = int(request.form.get("reorder_level", 10))

            expiry_text = request.form.get("expiry_date", "").strip()

            if not name or not category:
                flash("Product name and category are required!")
                return redirect(url_for("add_product"))

            if unit_price < 0 or stock_qty < 0 or reorder_level < 0:
                flash("Values cannot be negative!")
                return redirect(url_for("add_product"))

            expiry_date = (
                datetime.strptime(expiry_text, "%Y-%m-%d").date()
                if expiry_text else None
            )

            product = Product(
                name=name,
                category=category,
                unit_price=unit_price,
                stock_qty=stock_qty,
                reorder_level=reorder_level,
                expiry_date=expiry_date
            )

            db.session.add(product)
            db.session.commit()

            flash("Product added successfully!")
            return redirect(url_for("products"))

        except ValueError:

            db.session.rollback()
            flash("Please enter valid product details!")

        except Exception:

            db.session.rollback()
            app.logger.exception("Add product failed")
            flash("Unable to add product!")

    return render_template("product_form.html", product=None)


# ==========================================
# 12. EDIT PRODUCT
# ==========================================

@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):

    product = db.session.get(Product, product_id)

    if product is None:
        return "Product not found!", 404

    if request.method == "POST":

        try:

            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()

            unit_price = float(request.form.get("unit_price", 0))
            stock_qty = int(request.form.get("stock_qty", 0))
            reorder_level = int(request.form.get("reorder_level", 10))

            expiry_text = request.form.get("expiry_date", "").strip()

            if not name or not category:
                flash("Product name and category are required!")
                return redirect(url_for("edit_product", product_id=product_id))

            if unit_price < 0 or stock_qty < 0 or reorder_level < 0:
                flash("Values cannot be negative!")
                return redirect(url_for("edit_product", product_id=product_id))

            expiry_date = (
                datetime.strptime(expiry_text, "%Y-%m-%d").date()
                if expiry_text else None
            )

            product.name = name
            product.category = category
            product.unit_price = unit_price
            product.stock_qty = stock_qty
            product.reorder_level = reorder_level
            product.expiry_date = expiry_date

            db.session.commit()

            flash("Product updated successfully!")
            return redirect(url_for("products"))

        except ValueError:

            db.session.rollback()
            flash("Please enter valid product details!")

        except Exception:

            db.session.rollback()
            app.logger.exception("Edit product failed")
            flash("Unable to update product!")

    return render_template("product_form.html", product=product)


# ==========================================
# 13. DELETE PRODUCT
# ==========================================

@app.route("/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def delete_product(product_id):

    product = db.session.get(Product, product_id)

    if product is None:
        return "Product not found!", 404

    previous_sale = SaleItem.query.filter_by(
        product_id=product_id
    ).first()

    if previous_sale:
        flash("Cannot delete product because it has sales history!")
        return redirect(url_for("products"))

    try:

        db.session.delete(product)
        db.session.commit()

        flash("Product deleted successfully!")

    except Exception:

        db.session.rollback()
        app.logger.exception("Delete product failed")
        flash("Unable to delete product!")

    return redirect(url_for("products"))


# ==========================================
# 14. LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==========================================
# 15. RUN APPLICATION
# ==========================================



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





if __name__ == "__main__":
    print("Starting GreenLeaf Grocers...")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )



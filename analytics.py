import pandas as pd
from datetime import date, timedelta

from database.models import Sale, Product
from database.db import db


def get_sales_dataframe():
    sales = Sale.query.all()
    rows = []

    for sale in sales:
        for item in sale.items:
            product = db.session.get(Product, item.product_id)

            rows.append({
                "sale_id": sale.sale_id,
                "date": str(sale.sale_date),
                "product_id": item.product_id,
                "product": product.name if product else "Unknown",
                "category": product.category if product else "Unknown",
                "quantity": item.quantity,
                "price": item.price,
                "revenue": item.quantity * item.price
            })

    return pd.DataFrame(rows)


def daily_sales():
    df = get_sales_dataframe()
    if df.empty:
        return []

    result = df.groupby("date").agg(
        revenue=("revenue", "sum"),
        quantity=("quantity", "sum")
    ).reset_index()

    return result.to_dict("records")


def monthly_sales():
    df = get_sales_dataframe()
    if df.empty:
        return []

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    result = df.groupby("month").agg(
        revenue=("revenue", "sum"),
        quantity=("quantity", "sum")
    ).reset_index()

    return result.to_dict("records")


def top_products():
    df = get_sales_dataframe()
    if df.empty:
        return []

    result = (
        df.groupby("product")["quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    return result.to_dict("records")


def category_sales():
    df = get_sales_dataframe()
    if df.empty:
        return []

    result = df.groupby("category")["revenue"].sum().reset_index()
    total = result["revenue"].sum()

    result["share"] = (
        (result["revenue"] / total * 100).round(2)
        if total > 0 else 0
    )

    return result.to_dict("records")


def slow_moving_products():
    df = get_sales_dataframe()
    products = Product.query.filter(Product.stock_qty > 0).all()
    result = []
    today = pd.Timestamp.today().normalize()

    for product in products:
        matching = (
            df[df["product_id"] == product.product_id]
            if not df.empty else pd.DataFrame()
        )

        if matching.empty:
            result.append({
                "name": product.name,
                "stock": product.stock_qty,
                "last_sale": "No sales"
            })
            continue

        last_sale = pd.to_datetime(matching["date"]).max()

        if (today - last_sale.normalize()).days >= 30:
            result.append({
                "name": product.name,
                "stock": product.stock_qty,
                "last_sale": str(last_sale.date())
            })

    return result


def get_expiry_report():
    today = date.today()
    last_date = today + timedelta(days=15)

    products = Product.query.filter(
        Product.expiry_date.isnot(None),
        Product.stock_qty > 0,
        Product.expiry_date <= last_date
    ).order_by(Product.expiry_date.asc()).all()

    result = []

    for product in products:
        expiry = product.expiry_date

        if isinstance(expiry, str):
            expiry = date.fromisoformat(expiry)

        result.append({
            "product_id": product.product_id,
            "name": product.name,
            "stock": product.stock_qty,
            "expiry_date": expiry.strftime("%Y-%m-%d"),
            "status": "Expired" if expiry < today else "Expiring Soon"
        })

    return result


def get_kpis():
    total_revenue = db.session.query(
        db.func.sum(Sale.total_amount)
    ).scalar() or 0

    total_bills = Sale.query.count()
    average_bill = total_revenue / total_bills if total_bills else 0

    low_stock = Product.query.filter(
        Product.stock_qty <= Product.reorder_level
    ).count()

    categories = category_sales()
    top_category_share = max(
        [item["share"] for item in categories],
        default=0
    )

    return {
        "total_revenue": round(float(total_revenue), 2),
        "average_bill": round(float(average_bill), 2),
        "low_stock": low_stock,
        "top_category_share": round(float(top_category_share), 2)
    }

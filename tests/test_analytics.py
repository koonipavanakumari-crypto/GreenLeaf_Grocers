
from analytics import (
    daily_sales,
    monthly_sales,
    top_products,
    category_sales,
    slow_moving_products,
    get_kpis
)


def test_daily_sales_returns_list():
    result = daily_sales()
    assert isinstance(result, list)


def test_monthly_sales_returns_list():
    result = monthly_sales()
    assert isinstance(result, list)


def test_top_products_returns_list():
    result = top_products()
    assert isinstance(result, list)


def test_category_sales_returns_list():
    result = category_sales()
    assert isinstance(result, list)


def test_slow_products_returns_list():
    result = slow_moving_products()
    assert isinstance(result, list)


def test_kpis_returns_dictionary():
    result = get_kpis()
    assert isinstance(result, dict)


def test_kpi_values_are_non_negative():
    result = get_kpis()

    assert result["total_revenue"] >= 0
    assert result["average_bill"] >= 0
    assert result["low_stock"] >= 0
    assert result["top_category_share"] >= 0

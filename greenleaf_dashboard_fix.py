
from pathlib import Path
import re
import shutil

BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "app.py"
TEMPLATE_DIR = BASE_DIR / "templates"
DASHBOARD_FILE = TEMPLATE_DIR / "dashboard.html"

print("=" * 55)
print("GREENLEAF GROCERS - DASHBOARD FIX")
print("=" * 55)

# 1. Check required files
if not APP_FILE.exists():
    raise FileNotFoundError("app.py not found!")

TEMPLATE_DIR.mkdir(exist_ok=True)

# 2. Read existing app.py
app_code = APP_FILE.read_text(encoding="utf-8")

# 3. Find the existing dashboard route
pattern = re.compile(
    r'@app\.route\(["\']/dashboard["\']\)\s*'
    r'@login_required\s*'
    r'def dashboard\(\):[\s\S]*?(?=\n@app\.route|\nif __name__|$)'
)

match = pattern.search(app_code)

if not match:
    raise RuntimeError(
        "Could not find the existing /dashboard route. "
        "No files were changed."
    )

# 4. Create backups
app_backup = BASE_DIR / "app.py.dashboard_backup"

if not app_backup.exists():
    shutil.copy2(APP_FILE, app_backup)

if DASHBOARD_FILE.exists():
    template_backup = BASE_DIR / "dashboard.html.dashboard_backup"

    if not template_backup.exists():
        shutil.copy2(DASHBOARD_FILE, template_backup)

print("Backups created.")

# 5. Replace only the dashboard route
new_dashboard_route = '''@app.route("/dashboard")
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
'''

updated_app = (
    app_code[:match.start()]
    + new_dashboard_route
    + app_code[match.end():]
)

# 6. Create the new dashboard template
dashboard_html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GreenLeaf Grocers Dashboard</title>

<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: Arial, sans-serif;
    background: #f2f7f3;
    color: #26352a;
}

header {
    background: #176b3a;
    color: white;
    padding: 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
}

header h1 {
    margin-bottom: 7px;
}

.logout {
    background: white;
    color: #176b3a;
    padding: 11px 20px;
    border-radius: 6px;
    text-decoration: none;
    font-weight: bold;
}

.container {
    width: 92%;
    max-width: 1200px;
    margin: 30px auto;
}

.section {
    background: white;
    padding: 25px;
    margin-bottom: 25px;
    border-radius: 10px;
    box-shadow: 0 3px 12px rgba(0,0,0,.07);
}

.section h2 {\Desktop\GreenLeaf_Grocers> git branch -M main
git : The term 'git' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path
was included, verify that the path is correct and try again.
At line:1 char:1
+ git branch -M main
+ ~~~
    + CategoryInfo          : ObjectNotFound: (git:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 \Desktop\GreenLeaf_Grocers> git branch -M main
git : The term 'git' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path
was included, verify that the path is correct and try again.
At line:1 char:1
+ git branch -M main
+ ~~~
    + CategoryInfo          : ObjectNotFound: (git:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 
    color: #176b3a;
    margin-bottom: 20px;
}

.cards {
    display: grid;
    grid-template-columns: repeat(auto-fit,minmax(190px,1fr));
    gap: 18px;
}

.card {
    padding: 22px;
    border-left: 5px solid #176b3a;
    background: #f1f8f2;
    border-radius: 8px;
}

.card h3 {
    font-size: 15px;
    margin-bottom: 12px;
    color: #66756a;
}

.card h2 {
    font-size: 28px;
    margin: 0;
}

.menu {
    display: grid;
    grid-template-columns: repeat(auto-fit,minmax(210px,1fr));
    gap: 15px;
}

.menu a {
    display: block;
    padding: 18px;
    background: #edf7ef;
    color: #176b3a;
    text-decoration: none;
    border: 1px solid #d4e8d8;
    border-radius: 8px;
    font-weight: bold;
    transition: .2s;
}

.menu a:hover {
    background: #176b3a;
    color: white;
}

ul {
    padding-left: 22px;
    line-height: 2;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 13px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background: #176b3a;
    color: white;
}

footer {
    text-align: center;
    padding: 25px;
    color: #777;
}

@media(max-width:600px) {
    .container {
        width: 95%;
    }

    .section {
        padding: 15px;
        overflow-x: auto;
    }
}
</style>
</head>

<body>

<header>
    <div>
        <h1>GreenLeaf Grocers</h1>
        <p>Inventory & Sales Management System</p>
    </div>

    <a class="logout" href="/logout">Logout</a>
</header>

<div class="container">

    <div class="section">
        <h2>Welcome to GreenLeaf Grocers!</h2>
        <p>Logged in as:
            <strong>{{ session.get('username', 'User') }}</strong>
        </p>
        <p>Role:
            <strong>{{ session.get('role', 'User') }}</strong>
        </p>
    </div>

    <div class="section">
        <h2>Dashboard Information</h2>

        <div class="cards">

            <div class="card">
                <h3>Total Sales</h3>
                <h2>{{ total_sales }}</h2>
            </div>

            <div class="card">
                <h3>Total Revenue</h3>
                <h2>₹{{ "%.2f"|format(total_revenue) }}</h2>
            </div>

            <div class="card">
                <h3>Total Products</h3>
                <h2>{{ total_products }}</h2>
            </div>

            <div class="card">
                <h3>Low Stock Products</h3>
                <h2>{{ low_stock }}</h2>
            </div>

        </div>
    </div>

    <div class="section">
        <h2>Management & Navigation</h2>

        <div class="menu">

            <a href="/billing">Billing System</a>
            <a href="/products">Product Management</a>
            <a href="/reports">Reports & Analytics</a>
            <a href="/alerts">Stock & Expiry Alerts</a>

            {% if session.get('role') == 'admin' %}
            <a href="/products/import">Import Products CSV</a>
            <a href="/products/export">Export Products CSV</a>
            <a href="/reports/export">Export Sales Report</a>
            {% endif %}

        </div>
    </div>

    <div class="section">
        <h2>Billing Information</h2>
        <ul>
            <li>Select products from inventory.</li>
            <li>Enter product quantities.</li>
            <li>Calculate subtotal automatically.</li>
            <li>Apply customer discounts.</li>
            <li>Calculate final bill amount.</li>
            <li>Generate customer bills and receipts.</li>
            <li>Automatically update stock after billing.</li>
        </ul>
    </div>

    <div class="section">
        <h2>Recent Sales Information</h2>

        {% if recent_sales %}
        <table>
            <thead>
                <tr>
                    <th>Bill ID</th>
                    <th>Date</th>
                    <th>Total Amount</th>
                    <th>Time</th>
                </tr>
            </thead>

            <tbody>
                {% for sale in recent_sales %}
                <tr>
                    <td>{{ sale.sale_id }}</td>
                    <td>{{ sale.sale_date }}</td>
                    <td>₹{{ "%.2f"|format(sale.total_amount) }}</td>
                    <td>{{ sale.sale_time }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>No sales records available.</p>
        {% endif %}
    </div>

</div>

<footer>
    GreenLeaf Grocers | Inventory & Sales Management System
</footer>

</body>
</html>
'''

# 7. Write the two updated files
DASHBOARD_FILE.write_text(dashboard_html, encoding="utf-8")
APP_FILE.write_text(updated_app, encoding="utf-8")

# 8. Verify Python syntax before running Flask
compile(updated_app, str(APP_FILE), "exec")

print("\nDASHBOARD UPDATE SUCCESSFUL!")
print("Updated: app.py")
print("Updated: templates/dashboard.html")
print("Existing database was not modified.")
print("Existing billing and other routes were preserved.")
print("\nBackup files:")
print("app.py.dashboard_backup")
print("dashboard.html.dashboard_backup")
print("\nNEXT:")
print("1. Run: python app.py")
print("2. Open: http://127.0.0.1:5000/dashboard")
print("3. Press Ctrl + F5")
print("=" * 55)


git remote add origin https://github.com/kooni pavana kumari/GreenLeaf-Grocers.git
git push -u origin main



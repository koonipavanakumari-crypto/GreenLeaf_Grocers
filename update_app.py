
import os
import re
import shutil

APP_FILE = "app.py"

print("=" * 55)
print("GREENLEAF GROCERS - APP.PY UPDATE")
print("=" * 55)

if not os.path.exists(APP_FILE):
    raise FileNotFoundError("app.py not found. Run this script inside GreenLeaf_Grocers.")

with open(APP_FILE, "r", encoding="utf-8-sig") as file:
    original = file.read()

# Create backup
backup = "app.py.analytics_backup"
shutil.copy2(APP_FILE, backup)
print("Backup created:", backup)

updated = original

# 1. Add analytics imports
analytics_import = """
from analytics import (
    daily_sales,
    monthly_sales,
    top_products,
    category_sales,
    slow_moving_products,
    get_kpis
)
"""

if "from analytics import (" not in updated:
    import_lines = list(re.finditer(r"^(?:import .+|from .+ import .+)$", updated, re.MULTILINE))

    if not import_lines:
        raise RuntimeError("Could not locate import section in app.py.")

    last_import = import_lines[-1]
    updated = (
        updated[:last_import.end()]
        + "\n"
        + analytics_import
        + updated[last_import.end():]
    )
    print("Analytics imports added.")
else:
    print("Analytics imports already exist.")

# 2. Add analytics route only if it does not exist
if re.search(r'@app\.route\(["\']/analytics["\']', updated):
    print("/analytics route already exists. No duplicate added.")
else:
    analytics_route = '''

@app.route("/analytics")
@login_required
@admin_required
def analytics_dashboard():
    return render_template(
        "reports.html",
        daily_sales=daily_sales(),
        monthly_sales=monthly_sales(),
        top_products=top_products(),
        category_sales=category_sales(),
        slow_products=slow_moving_products(),
        kpis=get_kpis()
    )

'''

    # Insert before main execution block
    main_pattern = re.search(
        r'\nif __name__\s*==\s*["\']__main__["\']\s*:',
        updated
    )

    if main_pattern:
        updated = updated[:main_pattern.start()] + analytics_route + updated[main_pattern.start():]
    else:
        updated = updated.rstrip() + "\n" + analytics_route

    print("Analytics route added.")

# 3. Compile before writing
try:
    compile(updated, APP_FILE, "exec")
except SyntaxError as error:
    print("Syntax error detected. Original app.py was not changed.")
    print(error)
    raise

# 4. Save updated app.py
with open(APP_FILE, "w", encoding="utf-8") as file:
    file.write(updated)

print("\nAPP.PY UPDATE SUCCESSFUL!")
print("Existing routes preserved.")
print("Existing database untouched.")
print("\nNEXT:")
print("1. Check that analytics.py exists.")
print("2. Run: python app.py")
print("3. Open: http://127.0.0.1:5000/analytics")
print("=" * 55)

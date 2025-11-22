"""Inventory Management & Billing System -- Console App"""

import csv
import os
import sys
from datetime import datetime

DATA_DIR = "data"
BILLS_DIR = "bills"
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.csv")
SALES_FILE = os.path.join(DATA_DIR, "sales.csv")


# ============================================
# Utilities
# ============================================

def ensure_directories():
    """Ensure data and bills folders and base CSV files exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BILLS_DIR, exist_ok=True)

    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "price", "stock"])

    if not os.path.exists(SALES_FILE):
        with open(SALES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["bill_id", "datetime", "subtotal", "discount_percent", "total_amount"])


def format_currency(amount: float) -> str:
    """Format a float as Indian currency style string."""
    return f"₹{amount:,.2f}"


def read_products():
    """Load all products from CSV into a list of dicts."""
    products = []
    with open(PRODUCTS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip blank lines or malformed rows
            if not row.get("id"):
                continue
            try:
                products.append({
                    "id": int(row["id"]),
                    "name": row["name"],
                    "price": float(row["price"]),
                    "stock": int(row["stock"])
                })
            except (TypeError, ValueError):
                # If any row is corrupted, just skip it
                continue
    return products


def write_products(products):
    """Write the list of product dicts back to CSV."""
    with open(PRODUCTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "price", "stock"])
        for p in products:
            writer.writerow([
                p["id"],
                p["name"],
                f"{p['price']:.2f}",
                p["stock"]
            ])


def next_product_id(products):
    """Return the next product ID based on current list."""
    # same functionality, but more compact
    return (max((p["id"] for p in products), default=0) + 1)


def find_product_by_id(products, pid):
    """Return product dict with matching ID, or None."""
    return next((p for p in products if p["id"] == pid), None)


# ============================================
# Product management
# ============================================

def add_product():
    products = read_products()
    pid = next_product_id(products)

    name = input("Product name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    try:
        price = float(input("Price: ").strip())
        stock = int(input("Stock quantity: ").strip())
    except ValueError:
        print("Invalid numeric input.")
        return

    products.append({
        "id": pid,
        "name": name,
        "price": price,
        "stock": stock,
    })
    write_products(products)
    print(f"Product added with ID {pid}.")


def update_product():
    try:
        pid = int(input("Enter product ID to update: ").strip())
    except ValueError:
        print("Invalid ID.")
        return

    products = read_products()
    product = find_product_by_id(products, pid)
    if not product:
        print("Product ID not found.")
        return

    print(
        f"Current: Name='{product['name']}', "
        f"Price={format_currency(product['price'])}, Stock={product['stock']}"
    )

    # Update name
    new_name = input("New name (leave blank to keep): ").strip()
    if new_name:
        product["name"] = new_name

    # Update price and stock with validation
    try:
        new_price = input("New price (leave blank to keep): ").strip()
        if new_price:
            product["price"] = float(new_price)

        new_stock = input("New stock (leave blank to keep): ").strip()
        if new_stock:
            product["stock"] = int(new_stock)
    except ValueError:
        print("Invalid numeric input. Aborting update.")
        return

    write_products(products)
    print("Product updated.")


def delete_product():
    try:
        pid = int(input("Enter product ID to delete: ").strip())
    except ValueError:
        print("Invalid ID.")
        return

    products = read_products()
    original_len = len(products)
    products = [p for p in products if p["id"] != pid]

    if len(products) == original_len:
        print("Product ID not found.")
        return

    write_products(products)
    print("Product deleted.")


def search_products():
    products = read_products()
    query = input("Search by name or ID (enter text): ").strip()
    if not query:
        print("Empty search.")
        return

    # Determine if the query is numeric (ID) or text (name)
    results = []
    if query.isdigit():
        pid = int(query)
        results = [p for p in products if p["id"] == pid]
    else:
        lowered = query.lower()
        results = [p for p in products if lowered in p["name"].lower()]

    if not results:
        print("No products found.")
        return

    print("Found products:")
    for p in results:
        print(
            f"ID: {p['id']} | {p['name']} | "
            f"Price: {format_currency(p['price'])} | Stock: {p['stock']}"
        )


def list_all_products():
    products = read_products()
    if not products:
        print("No products available.")
        return

    print("{:<6} {:<30} {:>10} {:>8}".format("ID", "Name", "Price", "Stock"))
    for p in products:
        print("{:<6} {:<30} {:>10} {:>8}".format(
            p["id"],
            p["name"],
            format_currency(p["price"]),
            p["stock"],
        ))


# ============================================
# Cart & order processing
# ============================================

class CartItem:
    def __init__(self, product_id, name, price, qty):
        self.product_id = int(product_id)
        self.name = name
        self.price = float(price)
        self.qty = int(qty)

    def line_total(self):
        return self.price * self.qty


class Cart:
    def __init__(self):
        self.items = []

    def _find_item(self, product_id):
        return next((it for it in self.items if it.product_id == product_id), None)

    def add_item(self, product_id, qty):
        products = read_products()
        product = find_product_by_id(products, product_id)

        if not product:
            print("Product ID not found.")
            return False

        if qty <= 0:
            print("Quantity must be > 0.")
            return False

        if product["stock"] < qty:
            print(f"Insufficient stock. Available: {product['stock']}")
            return False

        existing = self._find_item(product_id)
        if existing:
            existing.qty += qty
            print(f"Added {qty} more to cart for product {product['name']}.")
        else:
            self.items.append(
                CartItem(product["id"], product["name"], product["price"], qty)
            )
            print(f"Added {qty} x {product['name']} to cart.")
        return True

    def remove_item(self, product_id):
        item = self._find_item(product_id)
        if not item:
            print("Item not found in cart.")
            return False
        self.items.remove(item)
        print("Item removed from cart.")
        return True

    def subtotal(self):
        return sum(item.line_total() for item in self.items)

    def is_empty(self):
        return not self.items

    def list_cart(self):
        if self.is_empty():
            print("Cart is empty.")
            return

        print("{:<6} {:<30} {:>8} {:>6} {:>10}".format(
            "PID", "Name", "UnitPrice", "Qty", "LineTotal"
        ))
        for item in self.items:
            print("{:<6} {:<30} {:>8} {:>6} {:>10}".format(
                item.product_id,
                item.name,
                format_currency(item.price),
                item.qty,
                format_currency(item.line_total())
            ))
        print("Subtotal:", format_currency(self.subtotal()))


def apply_discount_prompt(subtotal):
    """Ask user if they want discount and return discount %."""
    ans = input("Apply discount? (y/n): ").strip().lower()
    if ans != "y":
        return 0.0

    try:
        pct = float(input("Enter discount percent (e.g., 10 for 10%): ").strip())
    except ValueError:
        print("Invalid input. No discount.")
        return 0.0

    if pct < 0 or pct > 100:
        print("Invalid percent. No discount applied.")
        return 0.0

    return pct


def _update_product_stock_after_checkout(cart_items):
    """Reduce stock in products.csv based on cart items."""
    products = read_products()
    # Convert to dict for faster lookup, but keep original list to preserve order
    index_by_id = {p["id"]: idx for idx, p in enumerate(products)}

    for item in cart_items:
        idx = index_by_id.get(item.product_id)
        if idx is None:
            continue
        products[idx]["stock"] = max(0, products[idx]["stock"] - item.qty)

    write_products(products)


def _write_bill_files(bill_id, ts, cart, subtotal, discount_pct, total):
    """Create .txt and .csv bill files."""
    bill_txt_path = os.path.join(BILLS_DIR, f"{bill_id}.txt")
    bill_csv_path = os.path.join(BILLS_DIR, f"{bill_id}.csv")

    # Text bill
    with open(bill_txt_path, "w", encoding="utf-8") as f:
        f.write("=== BILL ===\n")
        f.write(f"Bill ID: {bill_id}\n")
        f.write(f"DateTime: {ts}\n\n")
        f.write("{:<6} {:<30} {:>10} {:>6} {:>12}\n".format(
            "PID", "Name", "UnitPrice", "Qty", "LineTotal"
        ))
        for it in cart.items:
            f.write("{:<6} {:<30} {:>10} {:>6} {:>12}\n".format(
                it.product_id,
                it.name,
                format_currency(it.price),
                it.qty,
                format_currency(it.line_total())
            ))
        f.write("\n")
        discount_amount = subtotal * discount_pct / 100.0
        f.write(f"Subtotal: {format_currency(subtotal)}\n")
        f.write(f"Discount ({discount_pct}%): {format_currency(discount_amount)}\n")
        f.write(f"Total: {format_currency(total)}\n")
        f.write("Thank you!\n")

    # CSV bill (items + summary rows)
    with open(bill_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "bill_id", "datetime", "product_id",
            "name", "unit_price", "qty", "line_total"
        ])
        for it in cart.items:
            writer.writerow([
                bill_id,
                ts,
                it.product_id,
                it.name,
                f"{it.price:.2f}",
                it.qty,
                f"{it.line_total():.2f}"
            ])
        writer.writerow([])
        writer.writerow(["", "", "", "SUBTOTAL", f"{subtotal:.2f}"])
        discount_amount = subtotal * discount_pct / 100.0
        writer.writerow(["", "", "", f"DISCOUNT_{discount_pct}%", f"{discount_amount:.2f}"])
        writer.writerow(["", "", "", "TOTAL", f"{total:.2f}"])

    return bill_txt_path, bill_csv_path


def _append_sales_summary(bill_id, ts, subtotal, discount_pct, total):
    """Append a summary row to sales.csv."""
    with open(SALES_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            bill_id,
            ts,
            f"{subtotal:.2f}",
            f"{discount_pct:.2f}",
            f"{total:.2f}"
        ])


def checkout(cart: Cart):
    if cart.is_empty():
        print("Cart empty. Cannot checkout.")
        return

    subtotal = cart.subtotal()
    print("Subtotal:", format_currency(subtotal))

    discount_pct = apply_discount_prompt(subtotal)
    discount_amount = subtotal * discount_pct / 100.0
    total = subtotal - discount_amount

    confirm = input(
        f"Total after {discount_pct}% discount is {format_currency(total)}. "
        "Confirm purchase? (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("Checkout cancelled.")
        return

    # 1) update stock
    _update_product_stock_after_checkout(cart.items)

    # 2) create bill id and timestamps
    now = datetime.now()
    bill_id = "bill_" + now.strftime("%Y%m%d%H%M%S")
    ts = now.strftime("%Y-%m-%d %H:%M:%S")

    # 3) write bill files
    bill_txt_path, bill_csv_path = _write_bill_files(
        bill_id, ts, cart, subtotal, discount_pct, total
    )

    # 4) append sales summary
    _append_sales_summary(bill_id, ts, subtotal, discount_pct, total)

    print(f"Checkout complete. Bill saved: {bill_txt_path} and {bill_csv_path}")


# ============================================
# Reports
# ============================================

def report_total_sales_by_date():
    date_str = input("Enter date (YYYY-MM-DD) or leave blank for today: ").strip()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    total = 0.0
    count = 0

    with open(SALES_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt_str = row.get("datetime")
            if not dt_str:
                continue
            row_date = dt_str.split(" ")[0]
            if row_date == date_str:
                try:
                    total += float(row["total_amount"])
                    count += 1
                except (TypeError, ValueError):
                    continue

    print(f"Date: {date_str} | Bills: {count} | Total Sales: {format_currency(total)}")


def report_low_stock():
    try:
        threshold = int(input("Enter low-stock threshold (e.g., 5): ").strip())
    except ValueError:
        print("Invalid threshold.")
        return

    products = read_products()
    low_stock_items = [p for p in products if p["stock"] <= threshold]

    if not low_stock_items:
        print("No low-stock products.")
        return

    print("Low-stock products:")
    for p in low_stock_items:
        print(f"ID:{p['id']} | {p['name']} | Stock: {p['stock']}")


# ============================================
# Menus
# ============================================

def product_menu():
    while True:
        print("\n--- Product Management ---")
        print("1. Add product")
        print("2. Update product")
        print("3. Delete product")
        print("4. Search product")
        print("5. List all products")
        print("0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            add_product()
        elif choice == "2":
            update_product()
        elif choice == "3":
            delete_product()
        elif choice == "4":
            search_products()
        elif choice == "5":
            list_all_products()
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def sales_menu():
    while True:
        print("\n--- Reports ---")
        print("1. Total sales for a day")
        print("2. Low-stock products")
        print("0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            report_total_sales_by_date()
        elif choice == "2":
            report_low_stock()
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def order_menu():
    cart = Cart()
    while True:
        print("\n--- Order Processing ---")
        print("1. Add item to cart")
        print("2. Remove item from cart")
        print("3. View cart")
        print("4. Checkout")
        print("0. Back (cart will be lost if not checked out)")
        choice = input("Choice: ").strip()

        if choice == "1":
            try:
                pid = int(input("Product ID: ").strip())
                qty = int(input("Quantity: ").strip())
            except ValueError:
                print("Invalid input.")
                continue
            cart.add_item(pid, qty)

        elif choice == "2":
            try:
                pid = int(input("Product ID to remove: ").strip())
            except ValueError:
                print("Invalid ID.")
                continue
            cart.remove_item(pid)

        elif choice == "3":
            cart.list_cart()

        elif choice == "4":
            checkout(cart)
            return  # after checkout, return to main

        elif choice == "0":
            return

        else:
            print("Invalid choice.")


def main_menu():
    ensure_directories()
    while True:
        print("\n=== Inventory & Billing System ===")
        print("1. Product management")
        print("2. Order processing")
        print("3. Reports")
        print("0. Exit")
        choice = input("Choice: ").strip()

        if choice == "1":
            product_menu()
        elif choice == "2":
            order_menu()
        elif choice == "3":
            sales_menu()
        elif choice == "0":
            print("Goodbye.")
            sys.exit(0)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main_menu()

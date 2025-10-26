"""Inventory Management & Billing System -- Console App"""

import csv
import os
import sys
from datetime import datetime

DATA_DIR = "data"
BILLS_DIR = "bills"
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.csv")
SALES_FILE = os.path.join(DATA_DIR, "sales.csv")



# Utilities

def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BILLS_DIR, exist_ok=True)
    # create files with headers if missing
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "price", "stock"])
    if not os.path.exists(SALES_FILE):
        with open(SALES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["bill_id", "datetime", "subtotal", "discount_percent", "total_amount"])


def read_products():
    products = []
    with open(PRODUCTS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row["id"]:
                continue
            products.append({
                "id": int(row["id"]),
                "name": row["name"],
                "price": float(row["price"]),
                "stock": int(row["stock"])
            })
    return products


def write_products(products):
    with open(PRODUCTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "price", "stock"])
        for p in products:
            writer.writerow([p["id"], p["name"], "{:.2f}".format(p["price"]), p["stock"]])


def format_currency(x):
    return f"₹{x:,.2f}"


def next_product_id(products):
    if not products:
        return 1
    return max(p["id"] for p in products) + 1



# Product management

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
    products.append({"id": pid, "name": name, "price": price, "stock": stock})
    write_products(products)
    print(f"Product added with ID {pid}.")


def update_product():
    try:
        pid = int(input("Enter product ID to update: ").strip())
    except ValueError:
        print("Invalid ID.")
        return
    products = read_products()
    for p in products:
        if p["id"] == pid:
            print(f"Current: Name='{p['name']}', Price={format_currency(p['price'])}, Stock={p['stock']}")
            new_name = input("New name (leave blank to keep): ").strip()
            if new_name:
                p["name"] = new_name
            try:
                new_price = input("New price (leave blank to keep): ").strip()
                if new_price:
                    p["price"] = float(new_price)
                new_stock = input("New stock (leave blank to keep): ").strip()
                if new_stock:
                    p["stock"] = int(new_stock)
            except ValueError:
                print("Invalid numeric input. Aborting update.")
                return
            write_products(products)
            print("Product updated.")
            return
    print("Product ID not found.")


def delete_product():
    try:
        pid = int(input("Enter product ID to delete: ").strip())
    except ValueError:
        print("Invalid ID.")
        return
    products = read_products()
    new_products = [p for p in products if p["id"] != pid]
    if len(new_products) == len(products):
        print("Product ID not found.")
        return
    write_products(new_products)
    print("Product deleted.")


def search_products():
    products = read_products()
    q = input("Search by name or ID (enter text): ").strip()
    if not q:
        print("Empty search.")
        return
    results = []
    if q.isdigit():
        pid = int(q)
        results = [p for p in products if p["id"] == pid]
    else:
        qlow = q.lower()
        results = [p for p in products if qlow in p["name"].lower()]
    if not results:
        print("No products found.")
    else:
        print("Found products:")
        for p in results:
            print(f"ID: {p['id']} | {p['name']} | Price: {format_currency(p['price'])} | Stock: {p['stock']}")


def list_all_products():
    products = read_products()
    if not products:
        print("No products available.")
        return
    print("{:<6} {:<30} {:>10} {:>8}".format("ID", "Name", "Price", "Stock"))
    for p in products:
        print("{:<6} {:<30} {:>10} {:>8}".format(p["id"], p["name"], format_currency(p["price"]), p["stock"]))



# Cart & order processing

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

    def add_item(self, product_id, qty):
        products = read_products()
        prod = next((p for p in products if p["id"] == product_id), None)
        if not prod:
            print("Product ID not found.")
            return False
        if qty <= 0:
            print("Quantity must be > 0.")
            return False
        if prod["stock"] < qty:
            print(f"Insufficient stock. Available: {prod['stock']}")
            return False
        # if product exists in cart, increase qty
        for it in self.items:
            if it.product_id == product_id:
                it.qty += qty
                print(f"Added {qty} more to cart for product {prod['name']}.")
                return True
        # else new cart item
        self.items.append(CartItem(prod["id"], prod["name"], prod["price"], qty))
        print(f"Added {qty} x {prod['name']} to cart.")
        return True

    def remove_item(self, product_id):
        for it in self.items:
            if it.product_id == product_id:
                self.items.remove(it)
                print("Item removed from cart.")
                return True
        print("Item not found in cart.")
        return False

    def subtotal(self):
        return sum(it.line_total() for it in self.items)

    def is_empty(self):
        return len(self.items) == 0

    def list_cart(self):
        if self.is_empty():
            print("Cart is empty.")
            return
        print("{:<6} {:<30} {:>8} {:>6} {:>10}".format("PID", "Name", "UnitPrice", "Qty", "LineTotal"))
        for it in self.items:
            print("{:<6} {:<30} {:>8} {:>6} {:>10}".format(it.product_id, it.name, format_currency(it.price), it.qty, format_currency(it.line_total())))
        print("Subtotal:", format_currency(self.subtotal()))


def apply_discount_prompt(subtotal):
    ans = input("Apply discount? (y/n): ").strip().lower()
    if ans != "y":
        return 0.0
    try:
        pct = float(input("Enter discount percent (e.g., 10 for 10%): ").strip())
        if pct < 0 or pct > 100:
            print("Invalid percent. No discount applied.")
            return 0.0
        return pct
    except ValueError:
        print("Invalid input. No discount.")
        return 0.0


def checkout(cart: Cart):
    if cart.is_empty():
        print("Cart empty. Cannot checkout.")
        return
    subtotal = cart.subtotal()
    print("Subtotal:", format_currency(subtotal))
    discount_pct = apply_discount_prompt(subtotal)
    discount_amount = subtotal * discount_pct / 100.0
    total = subtotal - discount_amount

    confirm = input(f"Total after {discount_pct}% discount is {format_currency(total)}. Confirm purchase? (y/n): ").strip().lower()
    if confirm != "y":
        print("Checkout cancelled.")
        return

    # update stocks
    products = read_products()
    for it in cart.items:
        for p in products:
            if p["id"] == it.product_id:
                p["stock"] -= it.qty
                if p["stock"] < 0:
                    p["stock"] = 0
    write_products(products)

    # create bill id and save bill (txt and csv)
    bill_id = "bill_" + datetime.now().strftime("%Y%m%d%H%M%S")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bill_txt_path = os.path.join(BILLS_DIR, f"{bill_id}.txt")
    bill_csv_path = os.path.join(BILLS_DIR, f"{bill_id}.csv")

    # Write text bill
    with open(bill_txt_path, "w", encoding="utf-8") as f:
        f.write("=== BILL ===\n")
        f.write(f"Bill ID: {bill_id}\n")
        f.write(f"DateTime: {ts}\n\n")
        f.write("{:<6} {:<30} {:>10} {:>6} {:>12}\n".format("PID", "Name", "UnitPrice", "Qty", "LineTotal"))
        for it in cart.items:
            f.write("{:<6} {:<30} {:>10} {:>6} {:>12}\n".format(it.product_id, it.name, format_currency(it.price), it.qty, format_currency(it.line_total())))
        f.write("\n")
        f.write(f"Subtotal: {format_currency(subtotal)}\n")
        f.write(f"Discount ({discount_pct}%): {format_currency(discount_amount)}\n")
        f.write(f"Total: {format_currency(total)}\n")
        f.write("Thank you!\n")

    # Write csv bill (items)
    with open(bill_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bill_id", "datetime", "product_id", "name", "unit_price", "qty", "line_total"])
        for it in cart.items:
            writer.writerow([bill_id, ts, it.product_id, it.name, f"{it.price:.2f}", it.qty, f"{it.line_total():.2f}"])
        # write summary row
        writer.writerow([])
        writer.writerow(["", "", "", "SUBTOTAL", f"{subtotal:.2f}"])
        writer.writerow(["", "", "", f"DISCOUNT_{discount_pct}%", f"{discount_amount:.2f}"])
        writer.writerow(["", "", "", "TOTAL", f"{total:.2f}"])

    # append to sales summary
    with open(SALES_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([bill_id, ts, f"{subtotal:.2f}", f"{discount_pct:.2f}", f"{total:.2f}"])

    print(f"Checkout complete. Bill saved: {bill_txt_path} and {bill_csv_path}")



# Reports

def report_total_sales_by_date():
    date_str = input("Enter date (YYYY-MM-DD) or leave blank for today: ").strip()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    total = 0.0
    count = 0
    with open(SALES_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("datetime"):
                continue
            row_date = row["datetime"].split(" ")[0]
            if row_date == date_str:
                total += float(row["total_amount"])
                count += 1
    print(f"Date: {date_str} | Bills: {count} | Total Sales: {format_currency(total)}")


def report_low_stock():
    try:
        threshold = int(input("Enter low-stock threshold (e.g., 5): ").strip())
    except ValueError:
        print("Invalid threshold.")
        return
    products = read_products()
    low = [p for p in products if p["stock"] <= threshold]
    if not low:
        print("No low-stock products.")
        return
    print("Low-stock products:")
    for p in low:
        print(f"ID:{p['id']} | {p['name']} | Stock: {p['stock']}")



# Console Menu

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

import sqlite3
import bcrypt

# Connect to the supermarket database
conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                 )''')

# Create sections table
cursor.execute('''CREATE TABLE IF NOT EXISTS sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                 )''')

# Create products table (linked to sections)
cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL,
                    section_id INTEGER NOT NULL,
                    FOREIGN KEY (section_id) REFERENCES sections(id)
                 )''')

conn.commit()

# Function to register a new user
def register():
    username = input("Enter a new username: ").strip()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        print("Username already exists. Try again.")
        return

    password = input("Enter a new password: ").strip()
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()  # Store as string

    # Insert new user into the database with a default role
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   (username, hashed_password, "customer"))
    conn.commit()  # Commit changes

    print("Registration successful! You can now log in.")

# Function to display sections and allow user to choose one
def select_section():
    cursor.execute("SELECT * FROM sections")
    sections = cursor.fetchall()

    if not sections:
        print("No sections available.")
        return None

    print("\nAvailable Sections:")
    for section in sections:
        print(f"{section[0]}. {section[1]}")  # Display section ID and Name

    while True:
        try:
            section_id = int(input("\nSelect a section by entering its number: "))
            cursor.execute("SELECT * FROM sections WHERE id = ?", (section_id,))
            if cursor.fetchone():
                return section_id
            else:
                print("Invalid section ID. Try again.")
        except ValueError:
            print("Please enter a valid number.")

# Function to display products in a selected section
def show_products(section_id):
    cursor.execute("SELECT id, name, price, stock FROM products WHERE section_id = ?", (section_id,))
    products = cursor.fetchall()

    if not products:
        print("No products available in this section.")
        return []

    print("\nAvailable Products:")
    print(f"{'ID':<5}{'Name':<20}{'Price':<10}{'Stock':<10}")
    print("-" * 45)

    for product in products:
        print(f"{product[0]:<5}{product[1]:<20}{product[2]:<10.2f}{product[3]:<10}")  # Align text properly

    return products

# Function to add products to cart
def add_to_cart(cart):
    section_id = select_section()
    if section_id:
        products = show_products(section_id)

        if not products:
            return  # No products in the section

        while True:
            product_id = input("Enter the Product ID to add to cart (or 'done' to finish): ").strip()
            if product_id.lower() == "done":
                break

            try:
                product_id = int(product_id)
                quantity = int(input("Enter quantity: "))

                # Get product details
                cursor.execute("SELECT name, price, stock FROM products WHERE id = ?", (product_id,))
                product = cursor.fetchone()

                if not product:
                    print("Invalid Product ID. Try again.")
                    continue

                if quantity > product[2]:
                    print("Not enough stock available.")
                    continue

                # Add to cart
                cart.append((product_id, product[0], product[1], quantity))
                print(f"Added {quantity} x {product[1]} to cart.")

            except ValueError:
                print("Invalid input. Try again.")

# Function to checkout
def checkout(cart):
    if not cart:
        print("Your cart is empty!")
        return

    print("\nYour Cart:")
    total = 0
    for item in cart:
        print(f"{item[1]} (x{item[3]}) - ${item[2] * item[3]:.2f}")
        total += item[2] * item[3]

    print(f"Total: ${total:.2f}")
    confirm = input("Proceed to checkout? (yes/no): ").strip().lower()
    if confirm == "yes":
        # Deduct stock
        for item in cart:
            cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item[3], item[0]))
        conn.commit()
        print("Purchase successful!")

    cart.clear()

# Function to start shopping after login
def shop(username):
    print(f"\nWelcome, {username}! You can now start shopping.")
    cart = []

    while True:
        print("\n1. Select Section\n2. Add to Cart\n3. View Cart & Checkout\n4. Logout")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            section_id = select_section()
            if section_id:
                show_products(section_id)  # Display products in the chosen section
        elif choice == "2":
            add_to_cart(cart)
        elif choice == "3":
            checkout(cart)
        elif choice == "4":
            print("Logging out...\n")
            return  # Return to the main menu
        else:
            print("Invalid choice. Try again.")

# Function to check if user exists (Login)
def login():
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    # Fetch user from database
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode(), user[0].encode()):  # Convert back to bytes
        print("Login successful! Welcome to the supermarket system.")
        shop(username)  # Start shopping after successful login
    else:
        print("Invalid username or password.")

# Main function to choose login or register
def main():
    while True:
        choice = input("\nDo you want to (1) Login or (2) Register? (Enter 1 or 2): ").strip()
        if choice == "1":
            login()
            break  # Exit the loop after logout
        elif choice == "2":
            register()
        else:
            print("Invalid choice. Please enter 1 or 2.")

# Run the program
main()

# Close database connection at the very end
conn.close()

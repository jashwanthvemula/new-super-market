import customtkinter as ctk
import os
import sys
import mysql.connector
import subprocess
from tkinter import messagebox
import shutil

from config import connect_db, DB_CONFIG
from utils import setup_environment

# Set environment variables
setup_environment()

def connect_db_without_database():
    """Connect to MySQL without specifying a database"""
    config = DB_CONFIG.copy()
    if "database" in config:
        del config["database"]
    
    try:
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def setup_database():
    """Create and set up the database with all required tables"""
    # First connect without specifying database
    conn = connect_db_without_database()
    if not conn:
        messagebox.showerror("Database Error", "Failed to connect to MySQL server")
        return False
    
    try:
        cursor = conn.cursor()
        db_name = DB_CONFIG["database"]
        
        # Create database if it doesn't exist
        print(f"Creating database: {db_name}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        print("Creating Users table")
        # Create Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            secret_key VARCHAR(255),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        print("Creating Products table")
        # Create Products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock INT NOT NULL DEFAULT 0,
            image_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        print("Creating Carts table")
        # Create Carts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Carts (
            cart_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
        """)
        
        print("Creating CartItems table")
        # Create CartItems table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CartItems (
            cart_item_id INT AUTO_INCREMENT PRIMARY KEY,
            cart_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            FOREIGN KEY (cart_id) REFERENCES Carts(cart_id),
            FOREIGN KEY (product_id) REFERENCES Products(product_id)
        )
        """)
        
        print("Creating Orders table")
        # Create Orders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            cart_id INT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (cart_id) REFERENCES Carts(cart_id)
        )
        """)
        
        conn.commit()
        print("Database tables created successfully")
        
        # Create default users and products
        create_default_user(cursor, conn)
        create_default_products(cursor, conn)
        
        return True
        
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        messagebox.showerror("Database Setup Error", str(err))
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def create_default_user(cursor, conn):
    """Create a default admin user if no users exist"""
    try:
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM Users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Creating default users")
            # Create an admin user
            from utils import hash_password
            hashed_password = hash_password("admin123")
            cursor.execute("""
            INSERT INTO Users (first_name, last_name, username, email, password, role)
            VALUES ('Admin', 'User', 'admin123', 'admin@supermarket.com', %s, 'admin')
            """, (hashed_password,))
            
            # Create a regular user
            hashed_password = hash_password("user123")
            cursor.execute("""
            INSERT INTO Users (first_name, last_name, username, email, password, role)
            VALUES ('John', 'Doe', 'user1', 'user1@example.com', %s, 'user')
            """, (hashed_password,))
            
            conn.commit()
            print("Default users created successfully")
            return True
        
        print("Users already exist, skipping default user creation")
        return True
    
    except mysql.connector.Error as err:
        print(f"Error creating default users: {err}")
        return False

def create_default_products(cursor, conn):
    """Create default products if no products exist"""
    try:
        # Check if products already exist
        cursor.execute("SELECT COUNT(*) FROM Products")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Creating default products")
            # Insert some default products
            products = [
                ("Fresh Apples", 2.00, 50, "images/apple.png"),
                ("Organic Bananas", 1.50, 30, "images/banana.png"),
                ("Fresh Broccoli", 1.80, 25, "images/broccoli.png"),
                ("Whole Wheat Bread", 2.50, 20, "images/bread.png"),
                ("Almond Milk", 3.00, 15, None),
                ("Eggs", 2.00, 40, None),
                ("Chicken Breast", 8.00, 10, None),
                ("Brown Rice", 2.00, 35, None)
            ]
            
            for product in products:
                cursor.execute("""
                INSERT INTO Products (name, price, stock, image_path)
                VALUES (%s, %s, %s, %s)
                """, product)
            
            conn.commit()
            print("Default products created successfully")
            return True
        
        print("Products already exist, skipping default product creation")
        return True
    
    except mysql.connector.Error as err:
        print(f"Error creating default products: {err}")
        return False

def check_image_files():
    """Check if required image files exist, copy to appropriate folder"""
    required_images = ["apple.png", "banana.png", "broccoli.png", "shopping.png"]
    
    # Check if images folder exists, create if not
    if not os.path.exists("images"):
        os.makedirs("images")
    
    # Copy the images to the images folder if they exist in current directory
    for image in required_images:
        if os.path.exists(image) and not os.path.exists(os.path.join("images", image)):
            shutil.copy(image, os.path.join("images", image))
            print(f"Copied {image} to images folder")

class SuperMarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SuperMarket Management System")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Configure appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="SuperMarket Management System", 
                                 font=("Arial", 24, "bold"))
        title_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(main_frame, text="Choose an option to proceed:", 
                                    font=("Arial", 14))
        subtitle_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        # Login button
        login_btn = ctk.CTkButton(buttons_frame, text="Login", width=200, height=40,
                                fg_color="#2563eb", hover_color="#1d4ed8",
                                command=self.open_login)
        login_btn.pack(pady=10)
        
        # Sign Up button
        signup_btn = ctk.CTkButton(buttons_frame, text="Sign Up", width=200, height=40,
                                 fg_color="#10b981", hover_color="#059669",
                                 command=self.open_signup)
        signup_btn.pack(pady=10)
        
        # Admin button
        admin_btn = ctk.CTkButton(buttons_frame, text="Admin Panel", width=200, height=40,
                                fg_color="#6366f1", hover_color="#4f46e5",
                                command=self.open_admin_login)
        admin_btn.pack(pady=10)
        
        # Exit button
        exit_btn = ctk.CTkButton(buttons_frame, text="Exit", width=200, height=40,
                               fg_color="#ef4444", hover_color="#dc2626",
                               command=self.root.destroy)
        exit_btn.pack(pady=10)
        
        # Version label
        version_label = ctk.CTkLabel(main_frame, text="Version 1.0", 
                                   font=("Arial", 10), text_color="gray")
        version_label.pack(side="bottom", pady=10)
    
    def open_login(self):
        self.root.withdraw()  # Hide main window
        try:
            subprocess.run(["python", "login_signup.py"])
        except Exception as e:
            print(f"Error opening login window: {e}")
        self.root.destroy()
    
    def open_signup(self):
        self.root.withdraw()  # Hide main window
        try:
            subprocess.run(["python", "login_signup.py", "signup"])
        except Exception as e:
            print(f"Error opening signup window: {e}")
        self.root.destroy()
    
    def open_admin_login(self):
        self.root.withdraw()  # Hide main window
        try:
            subprocess.run(["python", "admin/admin_view.py", "login"])
        except Exception as e:
            print(f"Error opening admin login window: {e}")
        self.root.destroy()

def main():
    # Check database connection
    print("Checking database connection...")
    conn = connect_db()
    if conn:
        conn.close()
        print("Connected to MySQL successfully")
    else:
        print("Failed to connect to MySQL, exiting")
        sys.exit(1)
    
    # Setup database and tables
    print("Setting up database...")
    if not setup_database():
        print("Failed to setup database, exiting")
        messagebox.showerror("Database Error", "Failed to setup database tables")
        sys.exit(1)
    
    # Check required image files
    print("Checking image files...")
    check_image_files()
    
    # Start the main application
    print("Starting SuperMarket Management System...")
    root = ctk.CTk()
    app = SuperMarketApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
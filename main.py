import customtkinter as ctk
import os
import sys
import mysql.connector
import subprocess
from tkinter import messagebox
import shutil
from PIL import Image, ImageTk

from config_db import connect_db, DB_CONFIG

# Set environment variables
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
    conn = connect_db_without_database()
    if not conn:
        messagebox.showerror("Database Error", "Failed to connect to MySQL server")
        return False
    
    try:
        cursor = conn.cursor()
        db_name = DB_CONFIG["database"]
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        print("Creating Users table")
        cursor.execute("ALTER TABLE Users DROP COLUMN image_path;")
        cursor.execute("ALTER TABLE Users ADD COLUMN image BLOB;")


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
    try:
        cursor.execute("SELECT COUNT(*) FROM Users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Creating default users")
            from utils_file import hash_password
            hashed_password = hash_password("admin123")
            cursor.execute("""
            INSERT INTO Users (first_name, last_name, username, email, password, role)
            VALUES ('Admin', 'User', 'admin123', 'admin@supermarket.com', %s, 'admin')
            """, (hashed_password,))
            
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
    try:
        cursor.execute("SELECT COUNT(*) FROM Products")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Creating default products")
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
    required_images = ["apple.png", "banana.png", "broccoli.png", "shopping.png"]
    
    if not os.path.exists("images"):
        os.makedirs("images")
    
    for image in required_images:
        if os.path.exists(image) and not os.path.exists(os.path.join("images", image)):
            shutil.copy(image, os.path.join("images", image))
            print(f"Copied {image} to images folder")

class SuperMarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SuperMarket Management System")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.background_image = self.load_background_image()
        self.setup_background()
        
        self.create_widgets()

    def load_background_image(self):
        """Load and prepare the background image"""
        try:
            image_path = "images/supermarket_background.png"
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Background image {image_path} not found")
            
            pil_image = Image.open(image_path)
            pil_image = pil_image.resize((800, 600), Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(800, 600))
        except Exception as e:
            print(f"Error loading background image: {e}")
            return None

    def setup_background(self):
        """Set up the background image"""
        if self.background_image:
            self.background_label = ctk.CTkLabel(self.root, image=self.background_image, text="")
            self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.root.configure(fg_color="#e0f2ff")

    def create_widgets(self):
        # Buttons placed directly on the root window
        button_config = {
            "width": 250,
            "height": 50,
            "font": ("Arial", 16, "bold"),
            "corner_radius": 10,
            "text_color": "white",
            "hover_color": "#1e40af"
        }

        # Position buttons vertically centered
        login_btn = ctk.CTkButton(self.root, text="Login", fg_color="#2563eb", 
                                command=self.open_login, **button_config)
        login_btn.place(relx=0.5, rely=0.35, anchor="center")

        signup_btn = ctk.CTkButton(self.root, text="Sign Up", fg_color="#10b981", 
                                 command=self.open_signup, **button_config)
        signup_btn.place(relx=0.5, rely=0.45, anchor="center")

        admin_btn = ctk.CTkButton(self.root, text="Admin Panel", fg_color="#6366f1", 
                                command=self.open_admin_login, **button_config)
        admin_btn.place(relx=0.5, rely=0.55, anchor="center")

        exit_btn = ctk.CTkButton(self.root, text="Exit", fg_color="#ef4444", 
                               command=self.root.destroy, **button_config)
        exit_btn.place(relx=0.5, rely=0.65, anchor="center")

    def open_login(self):
        self.root.withdraw()
        try:
            subprocess.run(["python", "login_signup.py"])
        except Exception as e:
            print(f"Error opening login window: {e}")
        self.root.destroy()

    def open_signup(self):
        self.root.withdraw()
        try:
            subprocess.run(["python", "login_signup.py", "signup"])
        except Exception as e:
            print(f"Error opening signup window: {e}")
        self.root.destroy()

    def open_admin_login(self):
        self.root.withdraw()
        try:
            subprocess.run(["python", "admin/admin_view.py", "login"])
        except Exception as e:
            print(f"Error opening admin login window: {e}")
        self.root.destroy()

def main():
    print("Checking database connection...")
    conn = connect_db()
    if conn:
        conn.close()
        print("Connected to MySQL successfully")
    else:
        print("Failed to connect to MySQL, exiting")
        sys.exit(1)
    
    print("Setting up database...")
    if not setup_database():
        print("Failed to setup database, exiting")
        messagebox.showerror("Database Error", "Failed to setup database tables")
        sys.exit(1)
    
    print("Checking image files...")
    check_image_files()
    
    print("Starting SuperMarket Management System...")
    root = ctk.CTk()
    app = SuperMarketApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
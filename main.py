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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            image BLOB
        )
        """)
        
        print("Creating Products table")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'available',
            image BLOB
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
            INSERT INTO Users (first_name, last_name, username, email, password, role, status, image)
            VALUES ('Admin', 'User', 'admin123', 'admin@supermarket.com', %s, 'admin', 'active', NULL)
            """, (hashed_password,))
            
            hashed_password = hash_password("user123")
            cursor.execute("""
            INSERT INTO Users (first_name, last_name, username, email, password, role, status, image)
            VALUES ('John', 'Doe', 'user1', 'user1@example.com', %s, 'user', 'active', NULL)
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
                ("Fresh Apples", 2.00, 50, "available", None),
                ("Organic Bananas", 1.50, 30, "available", None),
                ("Fresh Broccoli", 1.80, 25, "available", None),
                ("Whole Wheat Bread", 2.50, 20, "available", None),
                ("Almond Milk", 3.00, 15, "available", None),
                ("Eggs", 2.00, 40, "available", None),
                ("Chicken Breast", 8.00, 10, "available", None),
                ("Brown Rice", 2.00, 35, "available", None)
            ]
            
            for product in products:
                cursor.execute("""
                INSERT INTO Products (name, price, stock, status, image)
                VALUES (%s, %s, %s, %s, %s)
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
            image_path = "images/landing.jpg"
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
        bg_image = ctk.CTkImage(Image.open("images/landing.jpg"), size=(900, 600))

        # Background label with image
        bg_label = ctk.CTkLabel(self.root, image=bg_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Buttons container frame (transparent background)
        buttons_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        buttons_frame.place(relx=0.01, rely=0.98, anchor="sw")  # Closer to the bottom-left

        # Common button styles with semi-transparent background
        button_style = {
            "width": 130,
            "height": 45,
            "font": ("Arial", 16, "bold"),
            "corner_radius": 15,  # Rounded buttons
            "fg_color": "#3a7ebf",  # Semi-transparent blue that matches the theme
            "hover_color": "#2a5d8f",  # Darker blue on hover
            "text_color": "#ffffff",  # White text for visibility
            "border_width": 2,
            "border_color": "#ffffff"  # White border for better visibility
        }
        
        # Login Button
        login_btn = ctk.CTkButton(buttons_frame, text="Login",
                                command=self.open_login, **button_style)
        login_btn.pack(side="left", padx=10)

        # Sign Up Button
        signup_btn = ctk.CTkButton(buttons_frame, text="Sign Up",
                                command=self.open_signup, **button_style)
        signup_btn.pack(side="left", padx=10)

        # Admin Panel Button
        admin_btn = ctk.CTkButton(buttons_frame, text="Admin Panel",
                                command=self.open_admin_login, **button_style)
        admin_btn.pack(side="left", padx=10)

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
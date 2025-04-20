import sys
import os
# Add parent directory to path so we can import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
import subprocess
import re
import csv
import datetime

from admin.admin_nav import AdminNavigation
from config_db import connect_db
from utils_file import hash_password, read_login_file, write_login_file

class AdminApp:
    def __init__(self, root, username=None):
        self.root = root
        self.root.title("SuperMarket - Admin Panel")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        self.root.minsize(900, 600)  # Set minimum window size
        
        # Set environment variables
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Current user info
        self.current_user = {
            "user_id": None,
            "username": None,
            "first_name": None,
            "last_name": None,
            "role": None
        }
        
        # Variables for editing items
        self.editing_product_id = None
        self.editing_user_id = None
        
        # Authenticate user if username provided
        if username and username != "login":
            if not self.get_user_info(username):
                messagebox.showerror("Authentication Error", "You need admin privileges to access this page.")
                self.root.destroy()
                return
            
            # Setup UI for authenticated admin
            self.setup_main_ui()
            
            # Default to inventory management on startup
            self.show_inventory_management()
        else:
            # Try to read from login file first
            username_from_file, role = read_login_file()
            if username_from_file and role == "admin":
                if self.get_user_info(username_from_file):
                    # Setup UI for authenticated admin
                    self.setup_main_ui()
                    # Default to inventory management on startup
                    self.show_inventory_management()
                    return
            
            # Show login screen for admin if not logged in
            self.setup_login_ui()
    
    def get_user_info(self, username):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT user_id, username, first_name, last_name, role FROM Users WHERE username = %s",
                (username,)
            )
            
            user = cursor.fetchone()
            if user:
                self.current_user["user_id"] = user["user_id"]
                self.current_user["username"] = user["username"]
                self.current_user["first_name"] = user["first_name"]
                self.current_user["last_name"] = user["last_name"]
                self.current_user["role"] = user["role"]
                
                # Save user info for other scripts
                write_login_file(user["username"], user["role"])
                
                # Check if user is admin
                if user["role"] != "admin":
                    messagebox.showerror("Access Denied", "You don't have admin privileges.")
                    return False
                
                return True
            
            return False
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def setup_login_ui(self):
        # Main frame with modern design similar to user login
        self.main_frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=10)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.9)
        
        # Left Side (Login Form)
        self.left_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=0)
        self.left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        
        # Create a form container for better alignment
        self.form_container = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.form_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)
        
        # SuperMarket Title
        self.title_label = ctk.CTkLabel(self.form_container, text="SuperMarket Admin", 
                                      font=("Arial", 28, "bold"), text_color="#2563eb")
        self.title_label.pack(anchor="w", pady=(0, 5))
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(self.form_container, text="Manage your supermarket business operations.", 
                                         font=("Arial", 14), text_color="gray")
        self.subtitle_label.pack(anchor="w", pady=(0, 30))
        
        # Login Details Header
        self.login_header = ctk.CTkLabel(self.form_container, text="Enter admin credentials", 
                                       font=("Arial", 18, "bold"), text_color="black")
        self.login_header.pack(anchor="w", pady=(0, 5))
        
        # Login Instruction
        self.login_instruction = ctk.CTkLabel(self.form_container, text="Please login with your admin account", 
                                           font=("Arial", 14), text_color="gray")
        self.login_instruction.pack(anchor="w", pady=(0, 30))
        
        # Username Label
        self.username_label = ctk.CTkLabel(self.form_container, text="Username", font=("Arial", 14), text_color="gray")
        self.username_label.pack(anchor="w", pady=(0, 5))
        
        # Username Entry
        self.admin_username = ctk.CTkEntry(self.form_container, font=("Arial", 14), height=40, 
                                         border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.admin_username.pack(fill="x", pady=(0, 15))
        
        # Password Label
        self.password_label = ctk.CTkLabel(self.form_container, text="Password", font=("Arial", 14), text_color="gray")
        self.password_label.pack(anchor="w", pady=(0, 5))
        
        # Create a frame to hold password entry field and toggle button
        self.password_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        self.password_frame.pack(fill="x", pady=(0, 5))
        
        # Password Entry
        self.admin_password = ctk.CTkEntry(self.password_frame, font=("Arial", 14), height=40, 
                                         border_color="#e5e7eb", border_width=1, corner_radius=5, show="*")
        self.admin_password.pack(side="left", fill="x", expand=True)
        
        # Create password toggle button with eye emoji
        self.password_toggle_btn = ctk.CTkButton(
            self.password_frame, 
            text="👁️",  # Open eye emoji (default state - password hidden)
            width=40,
            height=40,
            fg_color="transparent",
            hover_color="#e5e7eb",
            corner_radius=5,
            command=self.toggle_password_visibility
        )
        self.password_toggle_btn.pack(side="right", padx=(5, 0))
        
        # Login Button
        self.login_btn = ctk.CTkButton(self.form_container, text="Login", font=("Arial", 14, "bold"), 
                                     fg_color="#2563eb", hover_color="#1d4ed8",
                                     height=40, corner_radius=5, command=self.admin_login)
        self.login_btn.pack(fill="x", pady=(15, 20))
        
        # Back to Main Button
        self.back_btn = ctk.CTkButton(self.form_container, text="Back to Main", font=("Arial", 14), 
                                    fg_color="#6b7280", hover_color="#4b5563",
                                    height=40, corner_radius=5, command=self.back_to_main)
        self.back_btn.pack(fill="x", pady=(0, 20))
        
        # Right Side (Image)
        self.right_frame = ctk.CTkFrame(self.main_frame, fg_color="#EBF3FF", corner_radius=0)
        self.right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        
        # Create a centered frame for the image
        self.image_container = ctk.CTkFrame(self.right_frame, fg_color="#EBF3FF", corner_radius=5)
        self.image_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Load and display the shopping cart image with transparency
        self.image_path = "images/shopping.png"
        try:
            # Create the CTkImage with transparency support
            self.img = ctk.CTkImage(light_image=Image.open(self.image_path), 
                                  dark_image=Image.open(self.image_path),
                                  size=(252, 252))
            
            # Create a label with transparent background
            self.image_label = ctk.CTkLabel(self.image_container, image=self.img, text="", bg_color="transparent")
            self.image_label.pack(fill="both", expand=True)
            
        except Exception as e:
            print(f"Error loading image: {e}")
            self.error_label = ctk.CTkLabel(self.image_container, text="🛒", font=("Arial", 72), text_color="#2563eb")
            self.error_label.pack(pady=50)
        
        # Bind the window resize event
        self.root.bind("<Configure>", self.adjust_login_layout)
    
    def adjust_login_layout(self, event=None):
        """Adjust login layout based on window size"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Update main frame
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", 
                         relwidth=min(0.95, 1400/width) if width > 800 else 0.98, 
                         relheight=min(0.9, 900/height) if height > 600 else 0.98)
        
        # Adjust layout based on screen size
        if width < 1000:
            # Stack vertically on smaller screens
            self.left_frame.place(relx=0.5, rely=0, relwidth=1, relheight=0.6, anchor="n")
            self.right_frame.place(relx=0.5, rely=1, relwidth=1, relheight=0.4, anchor="s")
            
            # Adjust form container
            self.form_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
            
            # Adjust image size for vertical layout
            if hasattr(self, 'img'):
                self.img.configure(size=(int(width*0.3), int(width*0.3)))
        else:
            # Side by side on larger screens
            self.left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
            self.right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
            
            # Adjust form container
            self.form_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)
            
            # Adjust image size for horizontal layout
            if hasattr(self, 'img'):
                img_size = min(int(width*0.2), 252)
                self.img.configure(size=(img_size, img_size))
    
    def toggle_password_visibility(self):
        current_show_value = self.admin_password.cget("show")
        if current_show_value == "":  # Currently showing password
            self.admin_password.configure(show="*")
            self.password_toggle_btn.configure(text="👁️")  # Open eye when password is hidden
        else:  # Currently hiding password
            self.admin_password.configure(show="")
            self.password_toggle_btn.configure(text="👁️‍🗨️")  # Eye with speech bubble to indicate visible
    
    def admin_login(self):
        username = self.admin_username.get()
        password = self.admin_password.get()
        
        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password.")
            return
        
        # Hash the password
        hashed_password = hash_password(password)
        
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT user_id, first_name, last_name, role FROM Users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            
            user = cursor.fetchone()
            
            if user and user["role"] == "admin":
                # Store user info
                self.current_user["user_id"] = user["user_id"]
                self.current_user["username"] = username
                self.current_user["first_name"] = user["first_name"]
                self.current_user["last_name"] = user["last_name"]
                self.current_user["role"] = user["role"]
                
                # Save login info for other scripts
                write_login_file(username, user["role"])
                
                messagebox.showinfo("Success", f"Welcome {user['first_name']} {user['last_name']}!")
                
                # Clear login UI
                for widget in self.root.winfo_children():
                    widget.destroy()
                
                # Setup admin UI
                self.setup_main_ui()
                
                # Show inventory management by default
                self.show_inventory_management()
            else:
                messagebox.showerror("Access Denied", "Invalid credentials or you don't have admin privileges.")
                
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def back_to_main(self):
        self.root.destroy()
        subprocess.run(["python", os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")])
    
    def setup_main_ui(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#f3f4f6", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)
        
        # Add navigation sidebar
        self.nav = AdminNavigationExtended(self.main_frame, self)
        
        # Add user info in sidebar
        if self.current_user["first_name"]:
            user_info = f"{self.current_user['first_name']} {self.current_user['last_name']}"
            user_label = ctk.CTkLabel(self.nav.sidebar, text=f"Welcome, {user_info}", 
                                    font=("Arial", 14), text_color="white")
            user_label.pack(pady=(0, 20))
        
        # Content frame - will hold different content based on navigation
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=15)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    def clear_content_frame(self):
        # Destroy all widgets in the content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_inventory_management(self):
        self.clear_content_frame()
        
        # Header
        header_label = ctk.CTkLabel(self.content_frame, text="Inventory Management",
                                   font=("Arial", 24, "bold"), text_color="#2563eb")
        header_label.pack(anchor="w", padx=30, pady=(30, 20))
        
        # Add New Item Section
        add_item_section = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=10,
                                      border_width=1, border_color="#e5e7eb")
        add_item_section.pack(fill="x", padx=30, pady=10)
        
        add_item_label = ctk.CTkLabel(add_item_section, text="Add New Item",
                                    font=("Arial", 18, "bold"), text_color="black")
        add_item_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Form layout with grid for better alignment
        form_frame = ctk.CTkFrame(add_item_section, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=10)
        
        # Item Name Entry - Row 1
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=5)
        
        name_label = ctk.CTkLabel(name_frame, text="Item Name", width=100, font=("Arial", 14), text_color="gray")
        name_label.pack(side="left", padx=(0, 10))
        
        self.item_name_entry = ctk.CTkEntry(name_frame, placeholder_text="Enter item name",
                                     height=40, corner_radius=5)
        self.item_name_entry.pack(side="left", fill="x", expand=True)
        
        # Price Entry - Row 2
        price_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        price_frame.pack(fill="x", pady=5)
        
        price_label = ctk.CTkLabel(price_frame, text="Price ($)", width=100, font=("Arial", 14), text_color="gray")
        price_label.pack(side="left", padx=(0, 10))
        
        self.price_entry = ctk.CTkEntry(price_frame, placeholder_text="Enter price",
                                 height=40, corner_radius=5)
        self.price_entry.pack(side="left", fill="x", expand=True)
        
        # Stock Entry - Row 3
        stock_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        stock_frame.pack(fill="x", pady=5)
        
        stock_label = ctk.CTkLabel(stock_frame, text="Stock", width=100, font=("Arial", 14), text_color="gray")
        stock_label.pack(side="left", padx=(0, 10))
        
        self.stock_entry = ctk.CTkEntry(stock_frame, placeholder_text="Enter quantity in stock",
                                 height=40, corner_radius=5)
        self.stock_entry.pack(side="left", fill="x", expand=True)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(add_item_section, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Add Item Button
        self.add_item_btn = ctk.CTkButton(buttons_frame, text="Add Item",
                                   fg_color="#10b981", hover_color="#059669",
                                   font=("Arial", 14), height=40, width=120,
                                   command=self.handle_add_update_product)
        self.add_item_btn.pack(side="left", padx=(0, 10))
        
        # Clear Form Button
        clear_btn = ctk.CTkButton(buttons_frame, text="Clear Form",
                                fg_color="#6b7280", hover_color="#4b5563",
                                font=("Arial", 14), height=40, width=120,
                                command=self.clear_product_fields)
        clear_btn.pack(side="left")
        
        # Existing Inventory Section
        inventory_section = ctk.CTkFrame(self.content_frame, fg_color="white")
        inventory_section.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Header with filter/search
        header_frame = ctk.CTkFrame(inventory_section, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 15))
        
        inventory_label = ctk.CTkLabel(header_frame, text="Existing Inventory",
                                     font=("Arial", 18, "bold"), text_color="black")
        inventory_label.pack(side="left")
        
        # Search/filter frame
        search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_frame.pack(side="right")
        
        self.inventory_search = ctk.CTkEntry(search_frame, placeholder_text="Search items...",
                                      height=35, width=200, corner_radius=5)
        self.inventory_search.pack(side="left", padx=(0, 10))
        
        search_btn = ctk.CTkButton(search_frame, text="Search",
                                 fg_color="#3b82f6", hover_color="#2563eb",
                                 font=("Arial", 14), height=35, width=80,
                                 command=self.search_inventory)
        search_btn.pack(side="left")
        
        # Create a custom style for the treeview
        style = ttk.Style()
        style.configure("Treeview", 
                        background="white",
                        fieldbackground="white", 
                        rowheight=40)
        style.configure("Treeview.Heading", 
                        font=('Arial', 12, 'bold'),
                        background="#f8fafc", 
                        foreground="black")
        style.map('Treeview', background=[('selected', '#e5e7eb')])
        
        # Create a frame for the table
        table_frame = ctk.CTkFrame(inventory_section, fg_color="#f8fafc", corner_radius=10)
        table_frame.pack(fill="both", expand=True, pady=5)
        
        # Create columns
        columns = ("name", "price", "stock", "actions")
        
        # Create treeview
        self.inventory_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.inventory_table.heading("name", text="Item Name")
        self.inventory_table.heading("price", text="Price")
        self.inventory_table.heading("stock", text="Stock")
        self.inventory_table.heading("actions", text="Actions")
        
        # Define column widths and alignment
        self.inventory_table.column("name", width=300, anchor="w")
        self.inventory_table.column("price", width=100, anchor="center")
        self.inventory_table.column("stock", width=100, anchor="center")
        self.inventory_table.column("actions", width=200, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.inventory_table.yview)
        self.inventory_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.inventory_table.pack(fill="both", expand=True)
        
        # Bind double-click event for editing
        self.inventory_table.bind("<Double-1>", self.edit_product)
        
        # Create buttons frame
        buttons_frame = ctk.CTkFrame(inventory_section, fg_color="white")
        buttons_frame.pack(fill="x", pady=10)
        
        # Edit and Delete buttons
        edit_btn = ctk.CTkButton(buttons_frame, text="Edit Selected", 
                                fg_color="#eab308", hover_color="#ca8a04",
                                font=("Arial", 14), height=40, width=150,
                                command=lambda: self.edit_product(None))
        edit_btn.pack(side="left", padx=10)
        
        delete_btn = ctk.CTkButton(buttons_frame, text="Delete Selected", 
                                  fg_color="#ef4444", hover_color="#dc2626",
                                  font=("Arial", 14), height=40, width=150,
                                  command=self.delete_selected_product)
        delete_btn.pack(side="left", padx=10)
        
        # Refresh button for inventory
        refresh_btn = ctk.CTkButton(buttons_frame, text="Refresh", 
                                   fg_color="#3b82f6", hover_color="#2563eb",
                                   font=("Arial", 14), height=40, width=150,
                                   command=self.refresh_inventory_table)
        refresh_btn.pack(side="right", padx=10)
        
        # Populate inventory table
        self.refresh_inventory_table()
    
    def fetch_inventory(self, search_term=None):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            if search_term:
                cursor.execute(
                    "SELECT product_id, name, price, stock FROM Products WHERE name LIKE %s ORDER BY name",
                    (f"%{search_term}%",)
                )
            else:
                cursor.execute("SELECT product_id, name, price, stock FROM Products ORDER BY name")
            
            products = cursor.fetchall()
            return products
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def search_inventory(self):
        search_term = self.inventory_search.get().strip()
        self.refresh_inventory_table(search_term)
    
    def refresh_inventory_table(self, search_term=None):
        # Clear existing items
        for item in self.inventory_table.get_children():
            self.inventory_table.delete(item)
        
        # Fetch and display products
        products = self.fetch_inventory(search_term)
        
        for product in products:
            product_id = product["product_id"]
            name = product["name"]
            price = f"${float(product['price']):.2f}"
            stock = product["stock"]
            
            self.inventory_table.insert("", "end", values=(name, price, stock, ""), tags=(str(product_id),))

    def clear_product_fields(self):
        self.item_name_entry.delete(0, 'end')
        self.item_name_entry.insert(0, "")
        
        self.price_entry.delete(0, 'end')
        self.price_entry.insert(0, "")
        
        self.stock_entry.delete(0, 'end')
        self.stock_entry.insert(0, "")
        
        # Reset state
        self.add_item_btn.configure(text="Add Item")
        self.editing_product_id = None

    def handle_add_update_product(self):
        name = self.item_name_entry.get()
        price = self.price_entry.get()
        stock = self.stock_entry.get()
        
        if self.editing_product_id:
            # Update existing product
            if self.update_product(self.editing_product_id, name, price, stock):
                messagebox.showinfo("Success", f"Product '{name}' updated successfully!")
                self.refresh_inventory_table()
                self.clear_product_fields()
        else:
            # Add new product
            if self.add_product(name, price, stock):
                messagebox.showinfo("Success", f"Product '{name}' added successfully!")
                self.refresh_inventory_table()
                self.clear_product_fields()
    
    def add_product(self, name, price, stock):
        if not name or not price or not stock:
            messagebox.showwarning("Input Error", "Please fill out all fields.")
            return False
        
        try:
            # Validate price and stock are numeric
            try:
                price_val = float(price)
                stock_val = int(stock)
                
                if price_val <= 0:
                    messagebox.showwarning("Input Error", "Price must be greater than zero.")
                    return False
                
                if stock_val < 0:
                    messagebox.showwarning("Input Error", "Stock cannot be negative.")
                    return False
                    
            except ValueError:
                messagebox.showwarning("Input Error", "Price and Stock must be numeric values.")
                return False
            
            connection = connect_db()
            cursor = connection.cursor()
            
            # Check if product with same name already exists
            cursor.execute("SELECT product_id FROM Products WHERE name = %s", (name,))
            if cursor.fetchone():
                messagebox.showwarning("Input Error", f"Product '{name}' already exists.")
                return False
            
            # Insert new product
            cursor.execute(
                "INSERT INTO Products (name, price, stock) VALUES (%s, %s, %s)",
                (name, price_val, stock_val)
            )
            
            connection.commit()
            return True
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def update_product(self, product_id, name, price, stock):
        if not name or not price or not stock:
            messagebox.showwarning("Input Error", "Please fill out all fields.")
            return False
        
        try:
            # Validate price and stock are numeric
            try:
                price_val = float(price)
                stock_val = int(stock)
                
                if price_val <= 0:
                    messagebox.showwarning("Input Error", "Price must be greater than zero.")
                    return False
                
                if stock_val < 0:
                    messagebox.showwarning("Input Error", "Stock cannot be negative.")
                    return False
                    
            except ValueError:
                messagebox.showwarning("Input Error", "Price and Stock must be numeric values.")
                return False
            
            connection = connect_db()
            cursor = connection.cursor()
            
            # Check if another product with same name exists
            cursor.execute("SELECT product_id FROM Products WHERE name = %s AND product_id != %s", 
                         (name, product_id))
            if cursor.fetchone():
                messagebox.showwarning("Input Error", f"Another product with name '{name}' already exists.")
                return False
            
            # Update product
            cursor.execute(
                "UPDATE Products SET name = %s, price = %s, stock = %s WHERE product_id = %s",
                (name, price_val, stock_val, product_id)
            )
            
            connection.commit()
            return True
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def edit_product(self, event):
        selected_items = self.inventory_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a product to edit.")
            return
        
        item = selected_items[0]
        values = self.inventory_table.item(item, 'values')
        
        if not values:
            return
        
        # Get product ID from tag
        product_id = int(self.inventory_table.item(item, 'tags')[0])
        
        # Fill entry fields with selected product details
        self.item_name_entry.delete(0, 'end')
        self.item_name_entry.insert(0, values[0])  # Name
        
        self.price_entry.delete(0, 'end')
        self.price_entry.insert(0, values[1].replace(',', ''))  # Price without $ sign
        
        self.stock_entry.delete(0, 'end')
        self.stock_entry.insert(0, values[2])  # Stock
        
        # Change button text and store product ID
        self.add_item_btn.configure(text="Update Item")
        self.editing_product_id = product_id

    def delete_selected_product(self):
        selected_items = self.inventory_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a product to delete.")
            return
        
        item = selected_items[0]
        values = self.inventory_table.item(item, 'values')
        
        if not values:
            return
        
        # Get product ID from tag
        product_id = int(self.inventory_table.item(item, 'tags')[0])
        product_name = values[0]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{product_name}'?")
        if not confirm:
            return
        
        # Delete the product
        if self.delete_product(product_id):
            messagebox.showinfo("Success", f"Product '{product_name}' deleted successfully!")
            self.refresh_inventory_table()
            self.clear_product_fields()
    
    def delete_product(self, product_id):
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # First check if product is referenced in any cart
            cursor.execute(
                "SELECT COUNT(*) FROM CartItems WHERE product_id = %s",
                (product_id,)
            )
            
            count = cursor.fetchone()[0]
            if count > 0:
                messagebox.showwarning(
                    "Cannot Delete", 
                    "This product is in active carts or orders. Consider marking it as out of stock instead."
                )
                return False
            
            # Delete the product
            cursor.execute(
                "DELETE FROM Products WHERE product_id = %s",
                (product_id,)
            )
            
            connection.commit()
            return True
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    def show_user_management(self):
        self.clear_content_frame()
        
        # Header
        header_label = ctk.CTkLabel(self.content_frame, text="User Management",
                                   font=("Arial", 24, "bold"), text_color="#2563eb")
        header_label.pack(anchor="w", padx=30, pady=(30, 20))
        
        # Create tabview for different user management sections
        tabview = ctk.CTkTabview(self.content_frame, corner_radius=15)
        tabview.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Create tabs
        add_user_tab = tabview.add("Add User")
        manage_users_tab = tabview.add("Manage Users")
        
        # ===== Add User Tab =====
        # Add New User Section with improved UI
        add_user_frame = ctk.CTkFrame(add_user_tab, fg_color="white", corner_radius=10)
        add_user_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        add_user_label = ctk.CTkLabel(add_user_frame, text="Add New User",
                                    font=("Arial", 18, "bold"), text_color="#2563eb")
        add_user_label.pack(anchor="w", padx=20, pady=(15, 20))
        
        # Form layout with better spacing
        form_frame = ctk.CTkFrame(add_user_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=10)
        
        # First Name Entry - Row 1
        first_name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        first_name_frame.pack(fill="x", pady=5)
        
        first_name_label = ctk.CTkLabel(first_name_frame, text="First Name", width=100, font=("Arial", 14), text_color="gray")
        first_name_label.pack(side="left", padx=(0, 10))
        
        self.first_name_entry = ctk.CTkEntry(first_name_frame, placeholder_text="Enter first name",
                                         height=40, corner_radius=5)
        self.first_name_entry.pack(side="left", fill="x", expand=True)
        
        # Last Name Entry - Row 2
        last_name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        last_name_frame.pack(fill="x", pady=5)
        
        last_name_label = ctk.CTkLabel(last_name_frame, text="Last Name", width=100, font=("Arial", 14), text_color="gray")
        last_name_label.pack(side="left", padx=(0, 10))
        
        self.last_name_entry = ctk.CTkEntry(last_name_frame, placeholder_text="Enter last name",
                                        height=40, corner_radius=5)
        self.last_name_entry.pack(side="left", fill="x", expand=True)
        
        # Email Entry - Row 3
        email_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        email_frame.pack(fill="x", pady=5)
        
        email_label = ctk.CTkLabel(email_frame, text="Email", width=100, font=("Arial", 14), text_color="gray")
        email_label.pack(side="left", padx=(0, 10))
        
        self.email_entry = ctk.CTkEntry(email_frame, placeholder_text="Enter email address",
                                     height=40, corner_radius=5)
        self.email_entry.pack(side="left", fill="x", expand=True)
        
        # Role Selection - Row 4
        role_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        role_frame.pack(fill="x", pady=5)
        
        role_label = ctk.CTkLabel(role_frame, text="Role", width=100, font=("Arial", 14), text_color="gray")
        role_label.pack(side="left", padx=(0, 10))
        
        self.role_var = ctk.StringVar(value="user")
        
        user_radio = ctk.CTkRadioButton(role_frame, text="Regular User", variable=self.role_var, value="user")
        user_radio.pack(side="left", padx=(0, 15))
        
        admin_radio = ctk.CTkRadioButton(role_frame, text="Administrator", variable=self.role_var, value="admin")
        admin_radio.pack(side="left")
        
        # Password Entry - Row 5
        password_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=5)
        
        password_label = ctk.CTkLabel(password_frame, text="Password", width=100, font=("Arial", 14), text_color="gray")
        password_label.pack(side="left", padx=(0, 10))
        
        self.password_entry = ctk.CTkEntry(password_frame, placeholder_text="Enter password or leave blank for default",
                                        height=40, corner_radius=5, show="*")
        self.password_entry.pack(side="left", fill="x", expand=True)
        
        # Password note
        password_note = ctk.CTkLabel(form_frame, text="Note: If left blank, the default password will be 'password123'",
                                   font=("Arial", 12), text_color="gray")
        password_note.pack(anchor="w", pady=(5, 15))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(add_user_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=10)
        
        # Add User Button
        self.add_user_btn = ctk.CTkButton(buttons_frame, text="Add User",
                                     fg_color="#10b981", hover_color="#059669",
                                     font=("Arial", 14), height=40, width=150,
                                     command=self.handle_add_user)
        self.add_user_btn.pack(side="left", padx=(0, 10))
        
        # Clear Form Button
        clear_btn = ctk.CTkButton(buttons_frame, text="Clear Form",
                                fg_color="#6b7280", hover_color="#4b5563",
                                font=("Arial", 14), height=40, width=150,
                                command=self.clear_user_fields)
        clear_btn.pack(side="left")
        
        # ===== Manage Users Tab =====
        # Existing Users Section with better UI
        manage_users_frame = ctk.CTkFrame(manage_users_tab, fg_color="white", corner_radius=10)
        manage_users_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        users_label = ctk.CTkLabel(manage_users_frame, text="Existing Users",
                                 font=("Arial", 18, "bold"), text_color="#2563eb")
        users_label.pack(anchor="w", padx=20, pady=(15, 20))
        
        # Search frame
        search_frame = ctk.CTkFrame(manage_users_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.user_search = ctk.CTkEntry(search_frame, placeholder_text="Search users by name or email...",
                                  height=35, width=300, corner_radius=5)
        self.user_search.pack(side="left", padx=(0, 10))
        
        search_btn = ctk.CTkButton(search_frame, text="Search",
                                 fg_color="#3b82f6", hover_color="#2563eb",
                                 font=("Arial", 14), height=35, width=80,
                                 command=self.search_users)
        search_btn.pack(side="left")
        
        # Create a custom style for the treeview
        style = ttk.Style()
        style.configure("Treeview", 
                        background="white",
                        fieldbackground="white", 
                        rowheight=40)
        style.configure("Treeview.Heading", 
                        font=('Arial', 12, 'bold'),
                        background="#f8fafc", 
                        foreground="black")
        style.map('Treeview', background=[('selected', '#e5e7eb')])
        
        # Create a frame for the table
        table_frame = ctk.CTkFrame(manage_users_frame, fg_color="#f8fafc", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create columns
        columns = ("name", "email", "role", "actions")
        
        # Create treeview
        self.users_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.users_table.heading("name", text="Name")
        self.users_table.heading("email", text="Email")
        self.users_table.heading("role", text="Role")
        self.users_table.heading("actions", text="Actions")
        
        # Define column widths and alignment
        self.users_table.column("name", width=200, anchor="w")
        self.users_table.column("email", width=250, anchor="w")
        self.users_table.column("role", width=100, anchor="center")
        self.users_table.column("actions", width=200, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_table.yview)
        self.users_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.users_table.pack(fill="both", expand=True)
        
        # Bind double-click event for editing
        self.users_table.bind("<Double-1>", self.open_edit_user_dialog)
        
        # Create action buttons frame
        action_frame = ctk.CTkFrame(manage_users_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=10)
        
        # Edit button
        edit_btn = ctk.CTkButton(action_frame, text="Edit Selected", 
                               fg_color="#eab308", hover_color="#ca8a04",
                               font=("Arial", 14), height=40, width=150,
                               command=lambda: self.open_edit_user_dialog(None))
        edit_btn.pack(side="left", padx=(0, 10))
        
        # Delete button
        delete_btn = ctk.CTkButton(action_frame, text="Delete Selected", 
                                 fg_color="#ef4444", hover_color="#dc2626",
                                 font=("Arial", 14), height=40, width=150,
                                 command=self.delete_selected_user)
        delete_btn.pack(side="left", padx=(0, 10))
        
        # Reset Password button
        reset_btn = ctk.CTkButton(action_frame, text="Reset Password", 
                                fg_color="#3b82f6", hover_color="#2563eb",
                                font=("Arial", 14), height=40, width=150,
                                command=self.reset_selected_password)
        reset_btn.pack(side="left")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(action_frame, text="Refresh", 
                                  fg_color="#10b981", hover_color="#059669",
                                  font=("Arial", 14), height=40, width=120,
                                  command=self.refresh_users_table)
        refresh_btn.pack(side="right")
        
        # Populate users table
        self.refresh_users_table()
    
    def fetch_users(self, search_term=None):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            if search_term:
                # Search by first name, last name, or username (email)
                cursor.execute(
                    """
                    SELECT user_id, first_name, last_name, username, email, role 
                    FROM Users 
                    WHERE first_name LIKE %s OR last_name LIKE %s OR username LIKE %s OR email LIKE %s
                    ORDER BY role, first_name, last_name
                    """,
                    (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
                )
            else:
                cursor.execute(
                    """
                    SELECT user_id, first_name, last_name, username, email, role 
                    FROM Users 
                    ORDER BY role, first_name, last_name
                    """
                )
            
            users = cursor.fetchall()
            return users
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def search_users(self):
        search_term = self.user_search.get().strip()
        self.refresh_users_table(search_term)
    
    def refresh_users_table(self, search_term=None):
        # Clear existing items
        for item in self.users_table.get_children():
            self.users_table.delete(item)
        
        # Fetch and display users
        users = self.fetch_users(search_term)
        
        for user in users:
            user_id = user["user_id"]
            full_name = f"{user['first_name']} {user['last_name']}"
            email = user.get("email", user["username"])
            if "@" not in email:
                email = f"{email}@example.com"  # Add domain if missing
            role = user["role"].capitalize()
            
            self.users_table.insert("", "end", values=(full_name, email, role, ""), tags=(str(user_id),))
    
    def clear_user_fields(self):
        if hasattr(self, 'first_name_entry'):
            self.first_name_entry.delete(0, 'end')
            self.first_name_entry.insert(0, "")
            
            self.last_name_entry.delete(0, 'end')
            self.last_name_entry.insert(0, "")
            
            self.email_entry.delete(0, 'end')
            self.email_entry.insert(0, "")
            
            self.role_var.set("user")
            
            self.password_entry.delete(0, 'end')
            self.password_entry.insert(0, "")
            
            # Reset state
            self.add_user_btn.configure(text="Add User")
            self.editing_user_id = None    
    def handle_add_user(self):
        first_name = self.first_name_entry.get().strip()
        last_name = self.last_name_entry.get().strip()
        email = self.email_entry.get().strip()
        role = self.role_var.get()
        password = self.password_entry.get()
        
        if not first_name or not last_name or not email:
            messagebox.showwarning("Input Error", "Please enter first name, last name, and email.")
            return
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showwarning("Input Error", "Please enter a valid email address.")
            return
        
        # Use default password if not provided
        if not password:
            password = "password123"
        
        # Add the user to database
        if self.add_user(first_name, last_name, email, role, password):
            messagebox.showinfo("Success", f"User '{first_name} {last_name}' added successfully!")
            self.refresh_users_table()
            self.clear_user_fields()
    
    def add_user(self, first_name, last_name, email, role, password="password123"):
        if not first_name or not last_name or not email or not role:
            messagebox.showwarning("Input Error", "Please fill out all required fields.")
            return False
        
        # Create username from email (part before @)
        username = email.split('@')[0]
        
        # Hash the password
        hashed_password = hash_password(password)
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Check if username already exists
            cursor.execute(
                "SELECT user_id FROM Users WHERE username = %s",
                (username,)
            )
            
            if cursor.fetchone():
                messagebox.showwarning("Input Error", "A user with this username already exists.")
                return False
            
            # Insert new user
            cursor.execute(
                """
                INSERT INTO Users (first_name, last_name, username, email, password, role) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (first_name, last_name, username, email, hashed_password, role)
            )
            
            connection.commit()
            return True
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def open_edit_user_dialog(self, event):
        selected_items = self.users_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a user to edit.")
            return
        
        item = selected_items[0]
        values = self.users_table.item(item, 'values')
        
        if not values:
            return
        
        # Get user ID from tag
        user_id = int(self.users_table.item(item, 'tags')[0])
        
        # Create a popup dialog for editing user
        self.edit_dialog = ctk.CTkToplevel(self.root)
        self.edit_dialog.title("Edit User")
        self.edit_dialog.geometry("500x400")
        self.edit_dialog.resizable(False, False)
        self.edit_dialog.grab_set()  # Make dialog modal
        
        # Center dialog on screen
        self.edit_dialog.update_idletasks()
        width = self.edit_dialog.winfo_width()
        height = self.edit_dialog.winfo_height()
        x = (self.edit_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.edit_dialog.winfo_screenheight() // 2) - (height // 2)
        self.edit_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Content frame
        content_frame = ctk.CTkFrame(self.edit_dialog, fg_color="white", corner_radius=10)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_label = ctk.CTkLabel(content_frame, text="Edit User",
                                   font=("Arial", 18, "bold"), text_color="#2563eb")
        header_label.pack(anchor="w", pady=(10, 20))
        
        # Fetch user details from database
        user_details = self.fetch_user_details(user_id)
        if not user_details:
            messagebox.showerror("Error", "Failed to fetch user details.")
            self.edit_dialog.destroy()
            return
        
        # Form layout
        # First Name Entry - Row 1
        first_name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        first_name_frame.pack(fill="x", pady=5)
        
        first_name_label = ctk.CTkLabel(first_name_frame, text="First Name", width=100, font=("Arial", 14), text_color="gray")
        first_name_label.pack(side="left", padx=(0, 10))
        
        self.edit_first_name = ctk.CTkEntry(first_name_frame, height=40, corner_radius=5)
        self.edit_first_name.pack(side="left", fill="x", expand=True)
        self.edit_first_name.insert(0, user_details.get("first_name", ""))
        
        # Last Name Entry - Row 2
        last_name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        last_name_frame.pack(fill="x", pady=5)
        
        last_name_label = ctk.CTkLabel(last_name_frame, text="Last Name", width=100, font=("Arial", 14), text_color="gray")
        last_name_label.pack(side="left", padx=(0, 10))
        
        self.edit_last_name = ctk.CTkEntry(last_name_frame, height=40, corner_radius=5)
        self.edit_last_name.pack(side="left", fill="x", expand=True)
        self.edit_last_name.insert(0, user_details.get("last_name", ""))
        
        # Email Entry - Row 3
        email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        email_frame.pack(fill="x", pady=5)
        
        email_label = ctk.CTkLabel(email_frame, text="Email", width=100, font=("Arial", 14), text_color="gray")
        email_label.pack(side="left", padx=(0, 10))
        
        self.edit_email = ctk.CTkEntry(email_frame, height=40, corner_radius=5)
        self.edit_email.pack(side="left", fill="x", expand=True)
        self.edit_email.insert(0, user_details.get("email", ""))
        
        # Role Selection - Row 4
        role_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        role_frame.pack(fill="x", pady=5)
        
        role_label = ctk.CTkLabel(role_frame, text="Role", width=100, font=("Arial", 14), text_color="gray")
        role_label.pack(side="left", padx=(0, 10))
        
        self.edit_role_var = ctk.StringVar(value=user_details.get("role", "user"))
        
        user_radio = ctk.CTkRadioButton(role_frame, text="Regular User", variable=self.edit_role_var, value="user")
        user_radio.pack(side="left", padx=(0, 15))
        
        admin_radio = ctk.CTkRadioButton(role_frame, text="Administrator", variable=self.edit_role_var, value="admin")
        admin_radio.pack(side="left")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=20)
        
        # Save Button
        save_btn = ctk.CTkButton(buttons_frame, text="Save Changes",
                               fg_color="#10b981", hover_color="#059669",
                               font=("Arial", 14), height=40, width=150,
                               command=lambda: self.save_user_edits(user_id))
        save_btn.pack(side="left", padx=(0, 10))
        
        # Cancel Button
        cancel_btn = ctk.CTkButton(buttons_frame, text="Cancel",
                                 fg_color="#6b7280", hover_color="#4b5563",
                                 font=("Arial", 14), height=40, width=150,
                                 command=self.edit_dialog.destroy)
        cancel_btn.pack(side="left")
    
    def fetch_user_details(self, user_id):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT user_id, first_name, last_name, username, email, role 
                FROM Users 
                WHERE user_id = %s
                """,
                (user_id,)
            )
            
            user = cursor.fetchone()
            return user
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def save_user_edits(self, user_id):
        first_name = self.edit_first_name.get().strip()
        last_name = self.edit_last_name.get().strip()
        email = self.edit_email.get().strip()
        role = self.edit_role_var.get()
        
        if not first_name or not last_name or not email:
            messagebox.showwarning("Input Error", "Please fill out all fields.", parent=self.edit_dialog)
            return
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showwarning("Input Error", "Please enter a valid email address.", parent=self.edit_dialog)
            return
        
        # Create username from email (part before @)
        username = email.split('@')[0]
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Check if username already exists for another user
            cursor.execute(
                "SELECT user_id FROM Users WHERE username = %s AND user_id != %s",
                (username, user_id)
            )
            
            if cursor.fetchone():
                messagebox.showwarning("Input Error", 
                                      "Another user with this username already exists.", 
                                      parent=self.edit_dialog)
                return
            
            # Update user
            cursor.execute(
                """
                UPDATE Users 
                SET first_name = %s, last_name = %s, username = %s, email = %s, role = %s 
                WHERE user_id = %s
                """,
                (first_name, last_name, username, email, role, user_id)
            )
            
            connection.commit()
            messagebox.showinfo("Success", "User updated successfully!")
            self.edit_dialog.destroy()
            self.refresh_users_table()
            
        except Exception as err:
            messagebox.showerror("Database Error", str(err), parent=self.edit_dialog)
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def delete_selected_user(self):
        selected_items = self.users_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a user to delete.")
            return
        
        item = selected_items[0]
        values = self.users_table.item(item, 'values')
        
        if not values:
            return
        
        # Get user ID from tag
        user_id = int(self.users_table.item(item, 'tags')[0])
        user_name = values[0]
        
        # Check if user is trying to delete themselves
        if user_id == self.current_user["user_id"]:
            messagebox.showwarning("Cannot Delete", "You cannot delete your own account while logged in.")
            return
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{user_name}'?")
        if not confirm:
            return
        
        # Delete the user
        if self.delete_user(user_id):
            messagebox.showinfo("Success", f"User '{user_name}' deleted successfully!")
            self.refresh_users_table()
    
    def delete_user(self, user_id):
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Check if user has orders or carts
            cursor.execute("SELECT COUNT(*) FROM Orders WHERE user_id = %s", (user_id,))
            order_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM Carts WHERE user_id = %s", (user_id,))
            cart_count = cursor.fetchone()[0]
            
            if order_count > 0 or cart_count > 0:
                messagebox.showwarning(
                    "Cannot Delete", 
                    "This user has orders or carts. Consider deactivating their account instead."
                )
                return False
            
            # Delete the user
            cursor.execute(
                "DELETE FROM Users WHERE user_id = %s",
                (user_id,)
            )
            
            connection.commit()
            return True
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def reset_selected_password(self):
        selected_items = self.users_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a user to reset their password.")
            return
        
        item = selected_items[0]
        values = self.users_table.item(item, 'values')
        
        if not values:
            return
        
        # Get user ID from tag
        user_id = int(self.users_table.item(item, 'tags')[0])
        user_name = values[0]
        
        # Confirm reset
        confirm = messagebox.askyesno("Confirm Reset", f"Are you sure you want to reset the password for '{user_name}'?")
        if not confirm:
            return
        
        # Reset the password
        if self.reset_password(user_id):
            messagebox.showinfo("Success", f"Password for '{user_name}' has been reset to 'password123'!")
    
    def reset_password(self, user_id, default_password="password123"):
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Hash the default password
            hashed_password = hash_password(default_password)
            
            # Update user's password
            cursor.execute(
                "UPDATE Users SET password = %s WHERE user_id = %s",
                (hashed_password, user_id)
            )
            
            connection.commit()
            return True
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
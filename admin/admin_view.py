import sys
import os
import numpy as np
from matplotlib import pyplot as plt
# Add parent directory to path so we can import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
import subprocess
import re
import csv
import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from admin.admin_nav import AdminNavigation
from config_db import connect_db
from utils_file import hash_password, read_login_file, write_login_file

class AdminNavigationExtended(AdminNavigation):
    def __init__(self, parent_frame, admin_app):
        self.admin_app = admin_app
        super().__init__(parent_frame)
        
        # Add the current section indicator
        self.current_section = "Manage Inventory"
        self.section_indicators = {}
        self.update_navigation_highlight()
    
    def navigate_to(self, destination):
        self.current_section = destination
        self.update_navigation_highlight()
        
        if destination == "Manage Inventory":
            self.admin_app.show_inventory_management()
        elif destination == "Manage Users":
            self.admin_app.show_user_management()
        elif destination == "Generate Report":
            self.admin_app.show_report_generation()
        elif destination == "Logout":
            self.admin_app.logout()
    
    def update_navigation_highlight(self):
        # This method would visually highlight the current section in the navigation menu
        # In a real implementation, this would update the styling of the navigation buttons
        pass

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
        
        # Bind resize event to adjust layout
        self.root.bind("<Configure>", self.on_window_resize)
        
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
    
    def on_window_resize(self, event=None):
        """Handle window resize events"""
        # Only proceed if we have the necessary attributes
        if hasattr(self, 'content_frame'):
            # Get new window size
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # Adjust layout based on current view
            if hasattr(self, 'current_view'):
                if self.current_view == "inventory":
                    self.adjust_inventory_layout(width, height)
                elif self.current_view == "users":
                    self.adjust_users_layout(width, height)
                elif self.current_view == "reports":
                    self.adjust_reports_layout(width, height)
    
    def adjust_inventory_layout(self, width, height):
        """Adjust the inventory management layout based on window size"""
        if hasattr(self, 'add_item_section') and hasattr(self, 'inventory_section'):
            # For smaller screens, stack the sections vertically
            if width < 900:
                # Adjust add item section to full width
                self.add_item_section.pack(fill="x", padx=20, pady=10)
                
                # Make form fields use most of the width
                for entry in [self.item_name_entry, self.price_entry, self.stock_entry]:
                    if entry.winfo_exists():
                        entry.configure(width=max(200, width - 150))
                
                # Adjust inventory table width
                if hasattr(self, 'inventory_table'):
                    table_width = width - 60  # Account for padding
                    self.inventory_table.column("name", width=int(table_width * 0.4))
                    self.inventory_table.column("price", width=int(table_width * 0.2))
                    self.inventory_table.column("stock", width=int(table_width * 0.2))
                    self.inventory_table.column("actions", width=int(table_width * 0.2))
            else:
                # For larger screens, use the default layout
                self.add_item_section.pack(fill="x", padx=30, pady=10)
                
                # Reset form field widths
                for entry in [self.item_name_entry, self.price_entry, self.stock_entry]:
                    if entry.winfo_exists():
                        entry.configure(width=300)
                
                # Reset table column widths
                if hasattr(self, 'inventory_table'):
                    self.inventory_table.column("name", width=300)
                    self.inventory_table.column("price", width=100)
                    self.inventory_table.column("stock", width=100)
                    self.inventory_table.column("actions", width=200)
    
    def adjust_users_layout(self, width, height):
        """Adjust the user management layout based on window size"""
        # Adjust tabview padding based on screen width
        if hasattr(self, 'user_tabview'):
            if width < 900:
                self.user_tabview.pack(fill="both", expand=True, padx=10, pady=10)
            else:
                self.user_tabview.pack(fill="both", expand=True, padx=30, pady=10)
    
    def adjust_reports_layout(self, width, height):
        """Adjust the reports layout based on window size"""
        # For report tabs, adjust the layout of panels for smaller screens
        if hasattr(self, 'report_tabview'):
            # If the screen is narrow, stack the report panels vertically instead of side by side
            if width < 900 and hasattr(self, 'sales_left_panel') and hasattr(self, 'sales_right_panel'):
                # Change left and right panels to be stacked
                self.sales_left_panel.configure(width=width - 60)
                self.sales_left_panel.pack(side="top", fill="x", pady=(0, 10))
                
                self.sales_right_panel.configure(width=width - 60)
                self.sales_right_panel.pack(side="top", fill="both", expand=True)
                
                # Also adjust inventory and user report panels if they exist
                if hasattr(self, 'inventory_left_panel') and hasattr(self, 'inventory_right_panel'):
                    self.inventory_left_panel.configure(width=width - 60)
                    self.inventory_left_panel.pack(side="top", fill="x", pady=(0, 10))
                    
                    self.inventory_right_panel.configure(width=width - 60)
                    self.inventory_right_panel.pack(side="top", fill="both", expand=True)
                
                if hasattr(self, 'user_left_panel') and hasattr(self, 'user_right_panel'):
                    self.user_left_panel.configure(width=width - 60)
                    self.user_left_panel.pack(side="top", fill="x", pady=(0, 10))
                    
                    self.user_right_panel.configure(width=width - 60)
                    self.user_right_panel.pack(side="top", fill="both", expand=True)
            elif width >= 900:
                # Restore side-by-side layout for wider screens
                if hasattr(self, 'sales_left_panel') and hasattr(self, 'sales_right_panel'):
                    self.sales_left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)
                    self.sales_right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
                
                if hasattr(self, 'inventory_left_panel') and hasattr(self, 'inventory_right_panel'):
                    self.inventory_left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)
                    self.inventory_right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
                
                if hasattr(self, 'user_left_panel') and hasattr(self, 'user_right_panel'):
                    self.user_left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)
                    self.user_right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
    
    def logout(self):
        # Remove the user file when logging out
        if os.path.exists("current_user.txt"):
            os.remove("current_user.txt")
        
        self.root.destroy()
        subprocess.run(["python", os.path.join(os.path.dirname(os.path.dirname(__file__)), "login_signup.py")])
    
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
        # Using a scrollable frame to handle overflow content automatically
        self.content_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="white", corner_radius=15)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    def clear_content_frame(self):
        # Destroy all widgets in the content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_inventory_management(self):
        self.clear_content_frame()
        self.current_view = "inventory"
        
        # Header
        header_label = ctk.CTkLabel(self.content_frame, text="Inventory Management",
                                   font=("Arial", 24, "bold"), text_color="#2563eb")
        header_label.pack(anchor="w", padx=30, pady=(10, 20))
        
        # Add New Item Section
        self.add_item_section = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=10,
                                      border_width=1, border_color="#e5e7eb")
        self.add_item_section.pack(fill="x", padx=30, pady=10)
        
        add_item_label = ctk.CTkLabel(self.add_item_section, text="Add New Item",
                                    font=("Arial", 18, "bold"), text_color="black")
        add_item_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Form layout with grid for better alignment
        form_frame = ctk.CTkFrame(self.add_item_section, fg_color="transparent")
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
        buttons_frame = ctk.CTkFrame(self.add_item_section, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Wrap buttons in a flex-like container
        button_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        button_container.pack(fill="x")
        
        # Add Item Button
        self.add_item_btn = ctk.CTkButton(button_container, text="Add Item",
                                   fg_color="#10b981", hover_color="#059669",
                                   font=("Arial", 14), height=40, width=120,
                                   command=self.handle_add_update_product)
        self.add_item_btn.pack(side="left", padx=(0, 10))
        
        # Clear Form Button
        clear_btn = ctk.CTkButton(button_container, text="Clear Form",
                                fg_color="#6b7280", hover_color="#4b5563",
                                font=("Arial", 14), height=40, width=120,
                                command=self.clear_product_fields)
        clear_btn.pack(side="left")
        
        # Existing Inventory Section
        self.inventory_section = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.inventory_section.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Header with filter/search - using a flex-like layout
        header_frame = ctk.CTkFrame(self.inventory_section, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 15))
        
        # Create a container for the left side (title)
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(side="left", fill="y")
        
        inventory_label = ctk.CTkLabel(title_container, text="Existing Inventory",
                                     font=("Arial", 18, "bold"), text_color="black")
        inventory_label.pack(side="left")
        
        # Create a container for the right side (search)
        search_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_container.pack(side="right", fill="y")
        
        # Search/filter frame with responsive width
        search_frame = ctk.CTkFrame(search_container, fg_color="transparent")
        search_frame.pack(side="right")
        
        self.inventory_search = ctk.CTkEntry(search_frame, placeholder_text="Search items...",
                                      height=35, width=200, corner_radius=5)
        self.inventory_search.pack(side="left", padx=(0, 10))
        
        search_btn = ctk.CTkButton(search_frame, text="Search",
                                 fg_color="#3b82f6", hover_color="#2563eb",
                                 font=("Arial", 14), height=35, width=80,
                                 command=self.search_inventory)
        search_btn.pack(side="left", padx=(0, 10))
        
        # Clear search button
        clear_search_btn = ctk.CTkButton(search_frame, text="Clear",
                                      fg_color="#ef4444", hover_color="#dc2626",
                                      font=("Arial", 14), height=35, width=80,
                                      command=self.clear_inventory_search)
        clear_search_btn.pack(side="left")
    
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
    def show_report_generation(self):
        self.clear_content_frame()
        
        # Header
        header_label = ctk.CTkLabel(self.content_frame, text="Report Generation",
                                font=("Arial", 24, "bold"), text_color="#2563eb")
        header_label.pack(anchor="w", padx=30, pady=(30, 20))
        
        # Create tabview for different report types
        tabview = ctk.CTkTabview(self.content_frame, corner_radius=15)
        tabview.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Create tabs
        sales_tab = tabview.add("Sales Report")
        inventory_tab = tabview.add("Inventory Report")
        user_tab = tabview.add("User Activity")
        
        # ===== Sales Report Tab =====
        self.setup_sales_report_tab(sales_tab)
        
        # ===== Inventory Report Tab =====
        self.setup_inventory_report_tab(inventory_tab)
        
        # ===== User Activity Tab =====
        self.setup_user_activity_tab(user_tab)

    def setup_sales_report_tab(self, parent_frame):
        # Main frame with two panels
        report_frame = ctk.CTkFrame(parent_frame, fg_color="white", corner_radius=10)
        report_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel - Options
        left_panel = ctk.CTkFrame(report_frame, fg_color="white", corner_radius=10,
                                border_width=1, border_color="#e5e7eb")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)
        
        options_label = ctk.CTkLabel(left_panel, text="Report Options",
                                    font=("Arial", 18, "bold"), text_color="#2563eb")
        options_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Date Range
        date_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        date_frame.pack(fill="x", padx=20, pady=10)
        
        period_label = ctk.CTkLabel(date_frame, text="Time Period:", font=("Arial", 14), text_color="gray")
        period_label.pack(side="left", padx=(0, 10))
        
        # Period options
        self.sales_period_var = ctk.StringVar(value="last_30_days")
        
        # Create period radio buttons
        periods = [
            ("Last 7 Days", "last_7_days"),
            ("Last 30 Days", "last_30_days"),
            ("Last 90 Days", "last_90_days"),
            ("This Year", "this_year"),
            ("Custom Range", "custom_range")
        ]
        
        period_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        period_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        for text, value in periods:
            radio = ctk.CTkRadioButton(period_frame, text=text, variable=self.sales_period_var, 
                                    value=value, command=self.toggle_custom_date_range)
            radio.pack(side="left", padx=(0, 15))
        
        # Custom date range frame (hidden by default)
        self.custom_date_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        
        # From date
        from_frame = ctk.CTkFrame(self.custom_date_frame, fg_color="transparent")
        from_frame.pack(side="left", padx=(20, 10))
        
        from_label = ctk.CTkLabel(from_frame, text="From:", font=("Arial", 14), text_color="gray")
        from_label.pack(side="left", padx=(0, 5))
        
        self.sales_from_date = ctk.CTkEntry(from_frame, placeholder_text="YYYY-MM-DD",
                                    width=150, height=30, corner_radius=5)
        self.sales_from_date.pack(side="left")
        
        # To date
        to_frame = ctk.CTkFrame(self.custom_date_frame, fg_color="transparent")
        to_frame.pack(side="left")
        
        to_label = ctk.CTkLabel(to_frame, text="To:", font=("Arial", 14), text_color="gray")
        to_label.pack(side="left", padx=(0, 5))
        
        self.sales_to_date = ctk.CTkEntry(to_frame, placeholder_text="YYYY-MM-DD",
                                    width=150, height=30, corner_radius=5)
        self.sales_to_date.pack(side="left")
        
        # Chart type
        chart_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        chart_frame.pack(fill="x", padx=20, pady=10)
        
        chart_label = ctk.CTkLabel(chart_frame, text="Chart Type:", font=("Arial", 14), text_color="gray")
        chart_label.pack(side="left", padx=(0, 10))
        
        self.sales_chart_var = ctk.StringVar(value="bar")
        
        bar_radio = ctk.CTkRadioButton(chart_frame, text="Bar Chart", variable=self.sales_chart_var, value="bar")
        bar_radio.pack(side="left", padx=(0, 15))
        
        line_radio = ctk.CTkRadioButton(chart_frame, text="Line Chart", variable=self.sales_chart_var, value="line")
        line_radio.pack(side="left", padx=(0, 15))
        
        pie_radio = ctk.CTkRadioButton(chart_frame, text="Pie Chart", variable=self.sales_chart_var, value="pie")
        pie_radio.pack(side="left")
        
        # Report Format
        format_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        format_frame.pack(fill="x", padx=20, pady=10)
        
        format_label = ctk.CTkLabel(format_frame, text="Export Format:", font=("Arial", 14), text_color="gray")
        format_label.pack(side="left", padx=(0, 10))
        
        self.sales_format_var = ctk.StringVar(value="csv")
        
        csv_radio = ctk.CTkRadioButton(format_frame, text="CSV", variable=self.sales_format_var, value="csv")
        csv_radio.pack(side="left", padx=(0, 15))
        
        txt_radio = ctk.CTkRadioButton(format_frame, text="Text", variable=self.sales_format_var, value="txt")
        txt_radio.pack(side="left", padx=(0, 15))
        
        pdf_radio = ctk.CTkRadioButton(format_frame, text="PDF", variable=self.sales_format_var, value="pdf")
        pdf_radio.pack(side="left")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Generate Report Button
        generate_btn = ctk.CTkButton(buttons_frame, text="Generate Report",
                                    fg_color="#10b981", hover_color="#059669",
                                    font=("Arial", 14), height=40, width=150,
                                    command=self.generate_sales_report)
        generate_btn.pack(side="left", padx=(0, 10))
        
        # Preview Button
        self.preview_graph_btn = ctk.CTkButton(buttons_frame, text="Preview Graph",
                                        fg_color="#3b82f6", hover_color="#2563eb",
                                        font=("Arial", 14), height=40, width=150,
                                        command=self.preview_sales_graph)
        self.preview_graph_btn.pack(side="left", padx=(0, 10))
        
        # Download Button (disabled until report is generated)
        self.sales_download_btn = ctk.CTkButton(buttons_frame, text="Download Report",
                                        fg_color="#6366f1", hover_color="#4f46e5",
                                        font=("Arial", 14), height=40, width=150,
                                        state="disabled", command=self.download_sales_report)
        self.sales_download_btn.pack(side="left")
        
        # Right panel - Preview
        self.right_panel = ctk.CTkFrame(report_frame, fg_color="#f8fafc", corner_radius=10,
                                    border_width=1, border_color="#e5e7eb")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
        
        # Preview header
        preview_header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        preview_header.pack(fill="x", padx=20, pady=(15, 5))
        
        preview_label = ctk.CTkLabel(preview_header, text="Report Preview",
                                    font=("Arial", 18, "bold"), text_color="#2563eb")
        preview_label.pack(side="left")
        
        # Tab view for switching between graph and text preview
        self.preview_tabs = ctk.CTkTabview(self.right_panel, corner_radius=5)
        self.preview_tabs.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        self.graph_tab = self.preview_tabs.add("Graph View")
        self.text_tab = self.preview_tabs.add("Text View")
        
        # Frame for graph display
        self.graph_frame = ctk.CTkFrame(self.graph_tab, fg_color="white", corner_radius=5)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message in graph frame
        self.graph_message = ctk.CTkLabel(self.graph_frame, text="Generate a report and click 'Preview Graph' to visualize data",
                                    font=("Arial", 14), text_color="gray")
        self.graph_message.pack(expand=True)
        
        # Text preview area
        self.sales_preview = ctk.CTkTextbox(self.text_tab, fg_color="white", corner_radius=5,
                                    width=800, height=300)
        self.sales_preview.pack(fill="both", expand=True, padx=10, pady=10)
        self.sales_preview.insert("1.0", "Report preview will appear here. Generate a report to see data.")
        
        # Store report data for graph and download
        self.sales_report_data = None
        self.sales_data = None

    def setup_inventory_report_tab(self, parent_frame):
        # Main frame with two panels
        report_frame = ctk.CTkFrame(parent_frame, fg_color="white", corner_radius=10)
        report_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel - Options
        left_panel = ctk.CTkFrame(report_frame, fg_color="white", corner_radius=10,
                                border_width=1, border_color="#e5e7eb")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)
        
        options_label = ctk.CTkLabel(left_panel, text="Report Options",
                                    font=("Arial", 18, "bold"), text_color="#2563eb")
        options_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Report Type
        type_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        type_frame.pack(fill="x", padx=20, pady=10)
        
        type_label = ctk.CTkLabel(type_frame, text="Report Type:", font=("Arial", 14), text_color="gray")
        type_label.pack(side="left", padx=(0, 10))
        
        self.inventory_type_var = ctk.StringVar(value="all_products")
        
        all_radio = ctk.CTkRadioButton(type_frame, text="All Products", 
                                    variable=self.inventory_type_var, value="all_products")
        all_radio.pack(side="left", padx=(0, 15))
        
        low_stock_radio = ctk.CTkRadioButton(type_frame, text="Low Stock Items", 
                                        variable=self.inventory_type_var, value="low_stock")
        low_stock_radio.pack(side="left", padx=(0, 15))
        
        out_of_stock_radio = ctk.CTkRadioButton(type_frame, text="Out of Stock", 
                                            variable=self.inventory_type_var, value="out_of_stock")
        out_of_stock_radio.pack(side="left")
        
        # Sort By
        sort_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        sort_frame.pack(fill="x", padx=20, pady=10)
        
        sort_label = ctk.CTkLabel(sort_frame, text="Sort By:", font=("Arial", 14), text_color="gray")
        sort_label.pack(side="left", padx=(0, 10))
        
        self.inventory_sort_var = ctk.StringVar(value="name")
        
        name_radio = ctk.CTkRadioButton(sort_frame, text="Name", 
                                    variable=self.inventory_sort_var, value="name")
        name_radio.pack(side="left", padx=(0, 15))
        
        price_radio = ctk.CTkRadioButton(sort_frame, text="Price", 
                                    variable=self.inventory_sort_var, value="price")
        price_radio.pack(side="left", padx=(0, 15))
        
        stock_radio = ctk.CTkRadioButton(sort_frame, text="Stock Level", 
                                    variable=self.inventory_sort_var, value="stock")
        stock_radio.pack(side="left")
        
        # Chart type
        chart_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        chart_frame.pack(fill="x", padx=20, pady=10)
        
        chart_label = ctk.CTkLabel(chart_frame, text="Chart Type:", font=("Arial", 14), text_color="gray")
        chart_label.pack(side="left", padx=(0, 10))
        
        self.inventory_chart_var = ctk.StringVar(value="bar")
        
        bar_radio = ctk.CTkRadioButton(chart_frame, text="Bar Chart", variable=self.inventory_chart_var, value="bar")
        bar_radio.pack(side="left", padx=(0, 15))
        
        pie_radio = ctk.CTkRadioButton(chart_frame, text="Pie Chart", variable=self.inventory_chart_var, value="pie")
        pie_radio.pack(side="left", padx=(0, 15))
        
        treemap_radio = ctk.CTkRadioButton(chart_frame, text="Treemap", variable=self.inventory_chart_var, value="treemap")
        treemap_radio.pack(side="left")
        
        # Report Format
        format_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        format_frame.pack(fill="x", padx=20, pady=10)
        
        format_label = ctk.CTkLabel(format_frame, text="Export Format:", font=("Arial", 14), text_color="gray")
        format_label.pack(side="left", padx=(0, 10))
        
        self.inventory_format_var = ctk.StringVar(value="csv")
        
        csv_radio = ctk.CTkRadioButton(format_frame, text="CSV", variable=self.inventory_format_var, value="csv")
        csv_radio.pack(side="left", padx=(0, 15))
        
        txt_radio = ctk.CTkRadioButton(format_frame, text="Text", variable=self.inventory_format_var, value="txt")
        txt_radio.pack(side="left", padx=(0, 15))
        
        pdf_radio = ctk.CTkRadioButton(format_frame, text="PDF", variable=self.inventory_format_var, value="pdf")
        pdf_radio.pack(side="left")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Generate Report Button
        generate_btn = ctk.CTkButton(buttons_frame, text="Generate Report",
                                    fg_color="#10b981", hover_color="#059669",
                                    font=("Arial", 14), height=40, width=150,
                                    command=self.generate_inventory_report)
        generate_btn.pack(side="left", padx=(0, 10))
        
        # Preview Button
        self.preview_inventory_graph_btn = ctk.CTkButton(buttons_frame, text="Preview Graph",
                                                fg_color="#3b82f6", hover_color="#2563eb",
                                                font=("Arial", 14), height=40, width=150,
                                                command=self.preview_inventory_graph)
        self.preview_inventory_graph_btn.pack(side="left", padx=(0, 10))
        
        # Download Button (disabled until report is generated)
        self.inventory_download_btn = ctk.CTkButton(buttons_frame, text="Download Report",
                                            fg_color="#6366f1", hover_color="#4f46e5",
                                            font=("Arial", 14), height=40, width=150,
                                            state="disabled", command=self.download_inventory_report)
        self.inventory_download_btn.pack(side="left")
        
        # Right panel - Preview
        self.inventory_right_panel = ctk.CTkFrame(report_frame, fg_color="#f8fafc", corner_radius=10,
                                            border_width=1, border_color="#e5e7eb")
        self.inventory_right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
        
        # Preview header
        preview_header = ctk.CTkFrame(self.inventory_right_panel, fg_color="transparent")
        preview_header.pack(fill="x", padx=20, pady=(15, 5))
        
        preview_label = ctk.CTkLabel(preview_header, text="Inventory Report Preview",
                                    font=("Arial", 18, "bold"), text_color="#2563eb")
        preview_label.pack(side="left")
        
        # Tab view for switching between graph and text preview
        self.inventory_tabs = ctk.CTkTabview(self.inventory_right_panel, corner_radius=5)
        self.inventory_tabs.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        self.inventory_graph_tab = self.inventory_tabs.add("Graph View")
        self.inventory_text_tab = self.inventory_tabs.add("Text View")
        
        # Frame for graph display
        self.inventory_graph_frame = ctk.CTkFrame(self.inventory_graph_tab, fg_color="white", corner_radius=5)
        self.inventory_graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message in graph frame
        self.inventory_graph_message = ctk.CTkLabel(self.inventory_graph_frame, 
                                            text="Generate a report and click 'Preview Graph' to visualize data",
                                            font=("Arial", 14), text_color="gray")
        self.inventory_graph_message.pack(expand=True)
        
        # Text preview area
        self.inventory_preview = ctk.CTkTextbox(self.inventory_text_tab, fg_color="white", corner_radius=5)
        self.inventory_preview.pack(fill="both", expand=True, padx=10, pady=10)
        self.inventory_preview.insert("1.0", "Report preview will appear here. Generate a report to see data.")
        
        # Store report data for download
        self.inventory_report_data = None
        self.inventory_data = None
    def preview_inventory_graph(self):
        """Generate and display a graph visualization of inventory data"""
        if not self.inventory_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Clear existing graph
        for widget in self.inventory_graph_frame.winfo_children():
            widget.destroy()
        
        # Create figure for the graph
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        
        # Get chart type
        chart_type = self.inventory_chart_var.get()
        
        try:
            # Extract data for graphing
            if not self.inventory_data or len(self.inventory_data) == 0:
                # Show message if no data
                self.inventory_graph_message = ctk.CTkLabel(self.inventory_graph_frame, 
                                                    text="No data available for visualization",
                                                    font=("Arial", 14), text_color="gray")
                self.inventory_graph_message.pack(expand=True)
                return
            
            # Limit to top 15 products for better visualization
            data_to_show = self.inventory_data
            if len(data_to_show) > 15:
                # Sort by stock if stock is the primary metric we're showing
                sorted_data = sorted(data_to_show, key=lambda x: x['stock'], reverse=True)
                data_to_show = sorted_data[:15]
            
            # Extract names and stock levels
            names = [item['name'] if len(item['name']) < 15 else item['name'][:12] + '...' for item in data_to_show]
            stock_levels = [item['stock'] for item in data_to_show]
            prices = [float(item['price']) for item in data_to_show]
            values = [float(item['price']) * item['stock'] for item in data_to_show]
            
            # Create appropriate chart type
            if chart_type == "bar":
                # Create horizontal bar chart for better readability with many items
                bars = ax.barh(names, stock_levels, color='#3b82f6')
                ax.set_title('Inventory Stock Levels')
                ax.set_xlabel('Units in Stock')
                
                # Add value labels on bars
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax.text(width + 0.3, bar.get_y() + bar.get_height()/2,
                            f'{width}', ha='left', va='center')
                
                # Adjust y-axis to prevent overlapping labels
                plt.tight_layout()
                
            elif chart_type == "pie":
                # For pie chart, show product values (price * quantity) instead of just quantity
                
                # Only show top 8 items in pie chart for readability
                if len(data_to_show) > 8:
                    # Sort by value
                    sorted_data = sorted(data_to_show, key=lambda x: float(x['price']) * x['stock'], reverse=True)
                    top_items = sorted_data[:7]  # Take top 7
                    
                    # Sum up remaining items
                    other_value = sum(float(item['price']) * item['stock'] for item in sorted_data[7:])
                    
                    # Extract data
                    names = [item['name'] if len(item['name']) < 15 else item['name'][:12] + '...' for item in top_items]
                    names.append('Other Products')
                    values = [float(item['price']) * item['stock'] for item in top_items]
                    values.append(other_value)
                else:
                    # Extract data
                    names = [item['name'] if len(item['name']) < 15 else item['name'][:12] + '...' for item in data_to_show]
                    values = [float(item['price']) * item['stock'] for item in data_to_show]
                
                # Colors for different products
                colors = plt.cm.tab20.colors[:len(names)]
                
                # Create pie chart
                wedges, texts, autotexts = ax.pie(
                    values, 
                    labels=names,
                    autopct='%1.1f%%', 
                    startangle=90, 
                    colors=colors
                )
                
                # Equal aspect ratio ensures that pie is drawn as a circle
                ax.axis('equal')
                ax.set_title('Inventory Value Distribution')
                
                # Make text more visible
                for text in texts:
                    text.set_fontsize(8)
                for autotext in autotexts:
                    autotext.set_fontsize(8)
                    autotext.set_color('white')
                    
            elif chart_type == "treemap":
                # Create a treemap using matplotlib's nested rectangles
                # Sort by value
                sorted_data = sorted(data_to_show, key=lambda x: float(x['price']) * x['stock'], reverse=True)
                
                # Extract data
                names = [item['name'] if len(item['name']) < 15 else item['name'][:12] + '...' for item in sorted_data]
                values = [float(item['price']) * item['stock'] for item in sorted_data]
                
                # Calculate total value
                total_value = sum(values)
                
                # Create a custom treemap (simplified version)
                # We'll create a grid of rectangles sized proportionally to values
                rows, cols = 3, 5  # Adjust grid size based on number of items
                rects = []
                colors = plt.cm.viridis(np.linspace(0, 1, len(values)))
                
                # Create rectangles proportional to values
                for i, (name, value, color) in enumerate(zip(names, values, colors)):
                    # Calculate rectangle size
                    size = value / total_value
                    rect = plt.Rectangle((0, 0), size * 10, size * 10, color=color)
                    rects.append(rect)
                
                # Clear the axis
                ax.clear()
                
                # Add a text title
                ax.text(0.5, 0.95, 'Inventory Value Distribution', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, fontsize=14, fontweight='bold')
                
                # Manually place rectangles in a grid-like layout
                max_cols = 4
                row, col = 0, 0
                max_width = 1.0 / max_cols
                max_height = 0.8 / ((len(values) // max_cols) + 1)
                
                for i, (name, value, color) in enumerate(zip(names, values, colors)):
                    # Calculate relative size
                    size = value / total_value
                    
                    # Place rectangle
                    rect_width = max_width * (0.5 + size * 2)  # Adjust width based on value
                    rect_height = max_height * (0.5 + size * 2)  # Adjust height based on value
                    
                    # Ensure rectangle stays within bounds
                    rect_width = min(rect_width, max_width * 0.95)
                    rect_height = min(rect_height, max_height * 0.95)
                    
                    # Calculate position
                    x_pos = col * max_width + (max_width - rect_width) / 2
                    y_pos = 0.9 - (row * max_height + (max_height - rect_height) / 2)
                    
                    # Create rectangle
                    rect = plt.Rectangle((x_pos, y_pos), rect_width, rect_height, 
                                    fill=True, color=color, alpha=0.8)
                    ax.add_patch(rect)
                    
                    # Add text
                    ax.text(x_pos + rect_width/2, y_pos + rect_height/2, 
                        f"{name}\n${value:.2f}", 
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=8, color='white')
                    
                    # Move to next position
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                
                # Remove axis ticks and spines
                ax.set_xticks([])
                ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_visible(False)
                
                # Set axis limits
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
            
            # Add data summary above the chart
            total_stock = sum(item['stock'] for item in self.inventory_data)
            total_value = sum(float(item['price']) * item['stock'] for item in self.inventory_data)
            out_of_stock = sum(1 for item in self.inventory_data if item['stock'] == 0)
            low_stock = sum(1 for item in self.inventory_data if 0 < item['stock'] <= 10)
            
            title_text = f'Total Products: {len(self.inventory_data)} | '
            title_text += f'Value: ${total_value:.2f} | '
            title_text += f'Units: {total_stock} | '
            title_text += f'Out of Stock: {out_of_stock} | '
            title_text += f'Low Stock: {low_stock}'
            
            if chart_type != "treemap":  # For treemap, we've already added a title
                ax.set_title(title_text, fontsize=9, pad=15)
            
            # Adjust layout for better fit
            plt.tight_layout()
            
            # Embed the graph in the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=self.inventory_graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Switch to graph tab
            self.inventory_tabs.set("Graph View")
            
        except Exception as e:
            # If there's an error, show error message
            for widget in self.inventory_graph_frame.winfo_children():
                widget.destroy()
            error_label = ctk.CTkLabel(self.inventory_graph_frame, text=f"Error creating graph: {str(e)}",
                                    font=("Arial", 14), text_color="#ef4444")
            error_label.pack(expand=True)
            print(f"Graph error: {e}")  # Print to console for debugging

    def setup_user_activity_tab(self, parent_frame):
        # Main frame with two panels
        report_frame = ctk.CTkFrame(parent_frame, fg_color="white", corner_radius=10)
        report_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel - Options
        left_panel = ctk.CTkFrame(report_frame, fg_color="white", corner_radius=10,
                                border_width=1, border_color="#e5e7eb")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)
        
        options_label = ctk.CTkLabel(left_panel, text="Report Options",
                                    font=("Arial", 18, "bold"), text_color="#2563eb")
        options_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Report Type
        type_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        type_frame.pack(fill="x", padx=20, pady=10)
        
        type_label = ctk.CTkLabel(type_frame, text="User Type:", font=("Arial", 14), text_color="gray")
        type_label.pack(side="left", padx=(0, 10))
        
        self.user_type_var = ctk.StringVar(value="all_users")
        
        all_radio = ctk.CTkRadioButton(type_frame, text="All Users", 
                                    variable=self.user_type_var, value="all_users")
        all_radio.pack(side="left", padx=(0, 15))
        
        admin_radio = ctk.CTkRadioButton(type_frame, text="Admins Only", 
                                    variable=self.user_type_var, value="admins")
        admin_radio.pack(side="left", padx=(0, 15))
        
        customer_radio = ctk.CTkRadioButton(type_frame, text="Customers Only", 
                                        variable=self.user_type_var, value="customers")
        customer_radio.pack(side="left")
        
        # Activity Filter
        filter_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        filter_label = ctk.CTkLabel(filter_frame, text="Activity:", font=("Arial", 14), text_color="gray")
        filter_label.pack(side="left", padx=(0, 10))
        
        self.user_activity_var = ctk.StringVar(value="all_activity")
        
        all_activity_radio = ctk.CTkRadioButton(filter_frame, text="All Activity", 
                                            variable=self.user_activity_var, value="all_activity")
        all_activity_radio.pack(side="left", padx=(0, 15))
        
        orders_radio = ctk.CTkRadioButton(filter_frame, text="Orders Only", 
                                        variable=self.user_activity_var, value="orders")
        orders_radio.pack(side="left")
        
        # Time Period
        period_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        period_frame.pack(fill="x", padx=20, pady=10)
        
        period_label = ctk.CTkLabel(period_frame, text="Time Period:", font=("Arial", 14), text_color="gray")
        period_label.pack(side="left", padx=(0, 10))
        
        self.user_period_var = ctk.StringVar(value="last_30_days")
        
        last_7_radio = ctk.CTkRadioButton(period_frame, text="Last 7 Days", 
                                        variable=self.user_period_var, value="last_7_days")
        last_7_radio.pack(side="left", padx=(0, 15))
        
        last_30_radio = ctk.CTkRadioButton(period_frame, text="Last 30 Days", 
                                        variable=self.user_period_var, value="last_30_days")
        last_30_radio.pack(side="left", padx=(0, 15))
        
        all_time_radio = ctk.CTkRadioButton(period_frame, text="All Time", 
                                        variable=self.user_period_var, value="all_time")
        all_time_radio.pack(side="left")
        
        # Chart type
        chart_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        chart_frame.pack(fill="x", padx=20, pady=10)
        
        chart_label = ctk.CTkLabel(chart_frame, text="Chart Type:", font=("Arial", 14), text_color="gray")
        chart_label.pack(side="left", padx=(0, 10))
        
        self.user_chart_var = ctk.StringVar(value="bar")
        
        bar_radio = ctk.CTkRadioButton(chart_frame, text="Bar Chart", variable=self.user_chart_var, value="bar")
        bar_radio.pack(side="left", padx=(0, 15))
        
        pie_radio = ctk.CTkRadioButton(chart_frame, text="Pie Chart", variable=self.user_chart_var, value="pie")
        pie_radio.pack(side="left", padx=(0, 15))
        
        bubble_radio = ctk.CTkRadioButton(chart_frame, text="Bubble Chart", variable=self.user_chart_var, value="bubble")
        bubble_radio.pack(side="left")
        
        # Report Format
        format_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        format_frame.pack(fill="x", padx=20, pady=10)
        
        format_label = ctk.CTkLabel(format_frame, text="Export Format:", font=("Arial", 14), text_color="gray")
        format_label.pack(side="left", padx=(0, 10))
        
        self.user_format_var = ctk.StringVar(value="csv")
        
        csv_radio = ctk.CTkRadioButton(format_frame, text="CSV", variable=self.user_format_var, value="csv")
        csv_radio.pack(side="left", padx=(0, 15))
        
        txt_radio = ctk.CTkRadioButton(format_frame, text="Text", variable=self.user_format_var, value="txt")
        txt_radio.pack(side="left", padx=(0, 15))
        
        pdf_radio = ctk.CTkRadioButton(format_frame, text="PDF", variable=self.user_format_var, value="pdf")
        pdf_radio.pack(side="left")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Generate Report Button
        generate_btn = ctk.CTkButton(buttons_frame, text="Generate Report",
                                    fg_color="#10b981", hover_color="#059669",
                                    font=("Arial", 14), height=40, width=150,
                                    command=self.generate_user_report)
        generate_btn.pack(side="left", padx=(0, 10))
        
        # Preview Button
        self.preview_user_graph_btn = ctk.CTkButton(buttons_frame, text="Preview Graph",
                                            fg_color="#3b82f6", hover_color="#2563eb",
                                            font=("Arial", 14), height=40, width=150,
                                            command=self.preview_user_graph)
        self.preview_user_graph_btn.pack(side="left", padx=(0, 10))
        
        # Download Button (disabled until report is generated)
        self.user_download_btn = ctk.CTkButton(buttons_frame, text="Download Report",
                                        fg_color="#6366f1", hover_color="#4f46e5",
                                        font=("Arial", 14), height=40, width=150,
                                        state="disabled", command=self.download_user_report)
        self.user_download_btn.pack(side="left")
        
        # Right panel - Preview
        self.user_right_panel = ctk.CTkFrame(report_frame, fg_color="#f8fafc", corner_radius=10,
                                        border_width=1, border_color="#e5e7eb")
        self.user_right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
        
        # Preview header
        preview_header = ctk.CTkFrame(self.user_right_panel, fg_color="transparent")
        preview_header.pack(fill="x", padx=20, pady=(15, 5))
        
        preview_label = ctk.CTkLabel(preview_header, text="User Activity Report Preview",
                                    font=("Arial", 18, "bold"), text_color="#2563eb")
        preview_label.pack(side="left")
        
        # Tab view for switching between graph and text preview
        self.user_tabs = ctk.CTkTabview(self.user_right_panel, corner_radius=5)
        self.user_tabs.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        self.user_graph_tab = self.user_tabs.add("Graph View")
        self.user_text_tab = self.user_tabs.add("Text View")
        
        # Frame for graph display
        self.user_graph_frame = ctk.CTkFrame(self.user_graph_tab, fg_color="white", corner_radius=5)
        self.user_graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message in graph frame
        self.user_graph_message = ctk.CTkLabel(self.user_graph_frame, 
                                        text="Generate a report and click 'Preview Graph' to visualize data",
                                        font=("Arial", 14), text_color="gray")
        self.user_graph_message.pack(expand=True)
        
        # Text preview area
        self.user_preview = ctk.CTkTextbox(self.user_text_tab, fg_color="white", corner_radius=5)
        self.user_preview.pack(fill="both", expand=True, padx=10, pady=10)
        self.user_preview.insert("1.0", "Report preview will appear here. Generate a report to see data.")
        
        # Store report data for download
        self.user_report_data = None
        self.user_data = None

    def toggle_custom_date_range(self):
        """Show or hide custom date range based on selection"""
        if self.sales_period_var.get() == "custom_range":
            self.custom_date_frame.pack(fill="x", padx=20, pady=(0, 10))
        else:
            self.custom_date_frame.pack_forget()

    def generate_sales_report(self):
        """Generate sales report based on selected options"""
        period = self.sales_period_var.get()
        report_format = self.sales_format_var.get()
        
        # Define date range based on selected period
        today = datetime.datetime.now()
        from_date = None
        to_date = today
        
        if period == "last_7_days":
            from_date = today - datetime.timedelta(days=7)
        elif period == "last_30_days":
            from_date = today - datetime.timedelta(days=30)
        elif period == "last_90_days":
            from_date = today - datetime.timedelta(days=90)
        elif period == "this_year":
            from_date = datetime.datetime(today.year, 1, 1)
        elif period == "custom_range":
            try:
                from_date = datetime.datetime.strptime(self.sales_from_date.get(), "%Y-%m-%d")
                to_date = datetime.datetime.strptime(self.sales_to_date.get(), "%Y-%m-%d")
                
                if from_date > to_date:
                    messagebox.showwarning("Invalid Date Range", "From date must be before to date.")
                    return
            except ValueError:
                messagebox.showwarning("Invalid Date Format", "Please use YYYY-MM-DD format for dates.")
                return
        
        # Fetch sales data for the period
        self.sales_data = self.fetch_sales_data(from_date, to_date)
        
        if not self.sales_data:
            self.sales_preview.delete("1.0", "end")
            self.sales_preview.insert("1.0", "No sales data found for the selected period.")
            self.sales_download_btn.configure(state="disabled")
            
            # Clear any existing graph
            for widget in self.graph_frame.winfo_children():
                widget.destroy()
            self.graph_message = ctk.CTkLabel(self.graph_frame, text="No data available for visualization",
                                        font=("Arial", 14), text_color="gray")
            self.graph_message.pack(expand=True)
            return
        
        # Format data for preview and download
        self.sales_report_data = self.format_sales_data(self.sales_data, report_format)
        
        # Show preview in text view
        self.sales_preview.delete("1.0", "end")
        self.sales_preview.insert("1.0", self.sales_report_data)
        
        # Enable download and preview buttons
        self.sales_download_btn.configure(state="normal")
        self.preview_tabs.set("Text View")
        
        # Show success message
        messagebox.showinfo("Report Generated", "Sales report has been generated successfully. You can now preview the graph or download the report.")

    def fetch_sales_data(self, from_date, to_date):
        """Fetch sales data from database for given period"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Format dates for SQL query
            from_date_str = from_date.strftime("%Y-%m-%d %H:%M:%S") if from_date else None
            to_date_str = to_date.strftime("%Y-%m-%d %H:%M:%S") if to_date else None
            
            # Query to get orders in date range
            if from_date and to_date:
                cursor.execute("""
                    SELECT o.order_id, u.username, u.first_name, u.last_name, 
                        o.order_date, o.total_amount, o.status
                    FROM Orders o
                    JOIN Users u ON o.user_id = u.user_id
                    WHERE o.order_date BETWEEN %s AND %s
                    ORDER BY o.order_date DESC
                """, (from_date_str, to_date_str))
            elif from_date:
                cursor.execute("""
                    SELECT o.order_id, u.username, u.first_name, u.last_name, 
                        o.order_date, o.total_amount, o.status
                    FROM Orders o
                    JOIN Users u ON o.user_id = u.user_id
                    WHERE o.order_date >= %s
                    ORDER BY o.order_date DESC
                """, (from_date_str,))
            else:
                cursor.execute("""
                    SELECT o.order_id, u.username, u.first_name, u.last_name, 
                        o.order_date, o.total_amount, o.status
                    FROM Orders o
                    JOIN Users u ON o.user_id = u.user_id
                    ORDER BY o.order_date DESC
                """)
            
            orders = cursor.fetchall()
            
            # If we have orders, fetch details for each order
            if orders:
                for order in orders:
                    # Get items in this order
                    cursor.execute("""
                        SELECT p.name, ci.quantity, p.price
                        FROM CartItems ci
                        JOIN Products p ON ci.product_id = p.product_id
                        WHERE ci.cart_id = (
                            SELECT cart_id FROM Orders WHERE order_id = %s
                        )
                    """, (order['order_id'],))
                    
                    order['items'] = cursor.fetchall()
            
            return orders
            
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def format_sales_data(self, sales_data, format_type):
        """Format sales data for display and download"""
        if format_type == "csv":
            # CSV format
            header = "Order ID,Date,Customer,Status,Total Amount\n"
            rows = []
            
            for order in sales_data:
                date = order['order_date'].strftime("%Y-%m-%d %H:%M")
                customer = f"{order['first_name']} {order['last_name']}"
                status = order['status']
                total = f"${float(order['total_amount']):.2f}"
                
                row = f"{order['order_id']},{date},{customer},{status},{total}"
                rows.append(row)
            
            return header + "\n".join(rows)
        else:
            # Text format (more detailed)
            report = "SALES REPORT\n"
            report += "=" * 50 + "\n\n"
            
            # Summary
            total_sales = sum(float(order['total_amount']) for order in sales_data)
            report += f"Total Orders: {len(sales_data)}\n"
            report += f"Total Revenue: ${total_sales:.2f}\n\n"
            report += "=" * 50 + "\n\n"
            
            # Detailed orders
            for order in sales_data:
                date = order['order_date'].strftime("%Y-%m-%d %H:%M")
                customer = f"{order['first_name']} {order['last_name']}"
                status = order['status']
                total = f"${float(order['total_amount']):.2f}"
                
                report += f"ORDER #{order['order_id']} - {date}\n"
                report += f"Customer: {customer}\n"
                report += f"Status: {status}\n"
                report += f"Total: {total}\n"
                
                # Add item details if available
                if 'items' in order and order['items']:
                    report += "\nItems:\n"
                    for item in order['items']:
                        item_total = float(item['price']) * item['quantity']
                        report += f"  - {item['name']} x {item['quantity']} (${float(item['price']):.2f} each) = ${item_total:.2f}\n"
                
                report += "\n" + "-" * 50 + "\n\n"
            
            return report
    def preview_sales_graph(self):
        """Generate and display a graph visualization of sales data"""
        if not self.sales_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Clear existing graph
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        # Create figure for the graph
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        
        # Get chart type
        chart_type = self.sales_chart_var.get()
        
        try:
            # Extract data for graphing
            if not self.sales_data:
                # Show message if no data
                self.graph_message = ctk.CTkLabel(self.graph_frame, text="No data available for visualization",
                                            font=("Arial", 14), text_color="gray")
                self.graph_message.pack(expand=True)
                return
            
            # Group data by date (daily)
            date_totals = {}
            for order in self.sales_data:
                date_str = order['order_date'].strftime("%Y-%m-%d")
                if date_str in date_totals:
                    date_totals[date_str] += float(order['total_amount'])
                else:
                    date_totals[date_str] = float(order['total_amount'])
            
            # Sort dates
            sorted_dates = sorted(date_totals.keys())
            totals = [date_totals[date] for date in sorted_dates]
            
            # Format dates for display (short format)
            display_dates = [date.split('-')[1] + '/' + date.split('-')[2] for date in sorted_dates]
            
            # Create appropriate chart type
            if chart_type == "bar":
                bars = ax.bar(display_dates, totals, color='#3b82f6')
                ax.set_title('Daily Sales')
                ax.set_xlabel('Date (MM/DD)')
                ax.set_ylabel('Sales Amount ($)')
                
                # Add value labels on top of each bar
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'${height:.2f}', ha='center', va='bottom', rotation=0,
                            fontsize=8)
                    
            elif chart_type == "line":
                ax.plot(display_dates, totals, marker='o', linestyle='-', color='#3b82f6', linewidth=2)
                ax.set_title('Sales Trend')
                ax.set_xlabel('Date (MM/DD)')
                ax.set_ylabel('Sales Amount ($)')
                
                # Add grid for better readability
                ax.grid(True, linestyle='--', alpha=0.7)
                
            elif chart_type == "pie":
                # For pie chart, group by status instead of date
                status_totals = {}
                for order in self.sales_data:
                    status = order['status']
                    if status in status_totals:
                        status_totals[status] += float(order['total_amount'])
                    else:
                        status_totals[status] = float(order['total_amount'])
                
                # Colors for different statuses
                colors = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6']
                
                # Create pie chart
                wedges, texts, autotexts = ax.pie(
                    status_totals.values(), 
                    labels=status_totals.keys(),
                    autopct='%1.1f%%', 
                    startangle=90, 
                    colors=colors
                )
                
                # Equal aspect ratio ensures that pie is drawn as a circle
                ax.axis('equal')
                ax.set_title('Sales by Status')
                
                # Make text more visible
                for text in texts:
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_color('white')
            
            # Add data summary above the chart
            total_sales = sum(float(order['total_amount']) for order in self.sales_data)
            avg_order = total_sales / len(self.sales_data) if self.sales_data else 0
            ax.set_title(f'Total Sales: ${total_sales:.2f} | Orders: {len(self.sales_data)} | Avg: ${avg_order:.2f}',
                    fontsize=10, pad=15)
            
            # Adjust layout for better fit
            plt.tight_layout()
            
            # Embed the graph in the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Switch to graph tab
            self.preview_tabs.set("Graph View")
            
        except Exception as e:
            # If there's an error, show error message
            for widget in self.graph_frame.winfo_children():
                widget.destroy()
            error_label = ctk.CTkLabel(self.graph_frame, text=f"Error creating graph: {str(e)}",
                                    font=("Arial", 14), text_color="#ef4444")
            error_label.pack(expand=True)

    def download_sales_report(self):
        """Download sales report to file"""
        if not self.sales_report_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Determine file extension
        ext = "csv" if self.sales_format_var.get() == "csv" else "txt"
        
        # Get save location from user
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[
                (f"{ext.upper()} files", f"*.{ext}"),
                ("All files", "*.*")
            ],
            title="Save Sales Report"
        )
        
        if not filename:
            return  # User cancelled
        
        # Save the file
        try:
            with open(filename, 'w', newline='') as file:
                file.write(self.sales_report_data)
            
            messagebox.showinfo("Success", f"Report saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            
    def generate_inventory_report(self):
        """Generate inventory report based on selected options"""
        report_type = self.inventory_type_var.get()
        sort_by = self.inventory_sort_var.get()
        report_format = self.inventory_format_var.get()
        
        # Fetch inventory data
        self.inventory_data = self.fetch_inventory_data(report_type, sort_by)
        
        if not self.inventory_data:
            self.inventory_preview.delete("1.0", "end")
            self.inventory_preview.insert("1.0", "No inventory data found.")
            self.inventory_download_btn.configure(state="disabled")
            
            # Clear any existing graph
            for widget in self.inventory_graph_frame.winfo_children():
                widget.destroy()
            self.inventory_graph_message = ctk.CTkLabel(self.inventory_graph_frame, text="No data available for visualization",
                                                font=("Arial", 14), text_color="gray")
            self.inventory_graph_message.pack(expand=True)
            return
        
        # Format data for preview and download
        self.inventory_report_data = self.format_inventory_data(self.inventory_data, report_format)
        
        # Show preview in text view
        self.inventory_preview.delete("1.0", "end")
        self.inventory_preview.insert("1.0", self.inventory_report_data)
        
        # Enable download button
        self.inventory_download_btn.configure(state="normal")
        self.inventory_tabs.set("Text View")
        
        # Show success message
        messagebox.showinfo("Report Generated", "Inventory report has been generated successfully. You can now preview the graph or download the report.")
    def fetch_inventory_data(self, report_type, sort_by):
        """Fetch inventory data from database"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Prepare SQL based on report type and sort order
            query = "SELECT product_id, name, price, stock FROM Products"
            
            # Filter by report type
            if report_type == "low_stock":
                query += " WHERE stock <= 10 AND stock > 0"
            elif report_type == "out_of_stock":
                query += " WHERE stock = 0"
            
            # Add sort order
            if sort_by == "name":
                query += " ORDER BY name"
            elif sort_by == "price":
                query += " ORDER BY price DESC"
            elif sort_by == "stock":
                query += " ORDER BY stock"
            
            cursor.execute(query)
            products = cursor.fetchall()
            
            return products
            
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def format_inventory_data(self, inventory_data, format_type):
        """Format inventory data for display and download"""
        if format_type == "csv":
            # CSV format
            header = "Product ID,Name,Price,Stock,Value\n"
            rows = []
            
            for product in inventory_data:
                price = float(product['price'])
                stock = product['stock']
                value = price * stock
                row = f"{product['product_id']},{product['name']},${price:.2f},{stock},${value:.2f}"
                rows.append(row)
            
            return header + "\n".join(rows)
        else:
            # Text format (more detailed)
            report = "INVENTORY REPORT\n"
            report += "=" * 50 + "\n\n"
            
            # Summary
            total_products = len(inventory_data)
            total_value = sum(float(product['price']) * product['stock'] for product in inventory_data)
            out_of_stock = sum(1 for product in inventory_data if product['stock'] == 0)
            low_stock = sum(1 for product in inventory_data if 0 < product['stock'] <= 10)
            
            report += f"Total Products: {total_products}\n"
            report += f"Total Inventory Value: ${total_value:.2f}\n"
            report += f"Out of Stock Items: {out_of_stock}\n"
            report += f"Low Stock Items: {low_stock}\n\n"
            report += "=" * 50 + "\n\n"
            
            # Product details
            report += "PRODUCT DETAILS:\n\n"
            
            for product in inventory_data:
                price = float(product['price'])
                stock = product['stock']
                value = price * stock
                
                report += f"Product ID: {product['product_id']}\n"
                report += f"Name: {product['name']}\n"
                report += f"Price: ${price:.2f}\n"
                report += f"Stock: {stock}\n"
                report += f"Total Value: ${value:.2f}\n"
                
                # Add stock status indicator
                if stock == 0:
                    report += "Status: OUT OF STOCK\n"
                elif stock <= 10:
                    report += "Status: LOW STOCK\n"
                else:
                    report += "Status: In Stock\n"
                
                report += "\n" + "-" * 50 + "\n\n"
            
            return report

    def download_inventory_report(self):
        """Download inventory report to file"""
        if not self.inventory_report_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Determine file extension
        ext = "csv" if self.inventory_format_var.get() == "csv" else "txt"
        
        # Get save location from user
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[
                (f"{ext.upper()} files", f"*.{ext}"),
                ("All files", "*.*")
            ],
            title="Save Inventory Report"
        )
        
        if not filename:
            return  # User cancelled
        
        # Save the file
        try:
            with open(filename, 'w', newline='') as file:
                file.write(self.inventory_report_data)
            
            messagebox.showinfo("Success", f"Report saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def generate_user_report(self):
        """Generate user activity report based on selected options"""
        user_type = self.user_type_var.get()
        activity_type = self.user_activity_var.get()
        period = self.user_period_var.get()
        report_format = self.user_format_var.get()
        
        # Define date range based on selected period
        today = datetime.datetime.now()
        from_date = None
        
        if period == "last_7_days":
            from_date = today - datetime.timedelta(days=7)
        elif period == "last_30_days":
            from_date = today - datetime.timedelta(days=30)
        
        # Fetch user data
        user_data = self.fetch_user_data(user_type, activity_type, from_date)
        
        if not user_data:
            self.user_preview.delete("1.0", "end")
            self.user_preview.insert("1.0", "No user data found for the selected criteria.")
            self.user_download_btn.configure(state="disabled")
            return
        
        # Format data for preview and download
        self.user_report_data = self.format_user_data(user_data, report_format)
        
        # Show preview
        self.user_preview.delete("1.0", "end")
        self.user_preview.insert("1.0", self.user_report_data)
        
        # Enable download button
        self.user_download_btn.configure(state="normal")

    def fetch_user_data(self, user_type, activity_type, from_date):
        """Fetch user data from database based on criteria"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Base query for users
            user_query = """
                SELECT user_id, first_name, last_name, username, email, role, created_at
                FROM Users
            """
            
            # Apply user type filter
            if user_type == "admins":
                user_query += " WHERE role = 'admin'"
            elif user_type == "customers":
                user_query += " WHERE role = 'user'"
            
            user_query += " ORDER BY created_at DESC"
            
            # Execute user query
            cursor.execute(user_query)
            users = cursor.fetchall()
            
            # If requested activity includes orders, get order data
            if activity_type in ["all_activity", "orders"] and users:
                for user in users:
                    # Query to get user's orders
                    order_query = """
                        SELECT order_id, order_date, total_amount, status
                        FROM Orders
                        WHERE user_id = %s
                    """
                    
                    # Add date filter if needed
                    if from_date:
                        order_query += " AND order_date >= %s"
                        cursor.execute(order_query, (user["user_id"], from_date))
                    else:
                        cursor.execute(order_query, (user["user_id"],))
                    
                    user["orders"] = cursor.fetchall()
                    
                    # Count total orders (including those outside the date range)
                    cursor.execute(
                        "SELECT COUNT(*) as total_orders FROM Orders WHERE user_id = %s",
                        (user["user_id"],)
                    )
                    total_orders = cursor.fetchone()
                    user["total_orders"] = total_orders["total_orders"] if total_orders else 0
            
            return users
            
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def format_user_data(self, user_data, format_type):
        """Format user data for display and download"""
        if format_type == "csv":
            # CSV format
            header = "User ID,Name,Email,Role,Created Date,Orders Count,Total Spent\n"
            rows = []
            
            for user in user_data:
                name = f"{user['first_name']} {user['last_name']}"
                email = user.get("email", user["username"])
                if not email and user.get("username"):
                    email = user["username"]
                role = user["role"]
                created = user["created_at"].strftime("%Y-%m-%d") if user["created_at"] else "N/A"
                
                # Calculate orders stats
                orders_count = len(user.get("orders", []))
                total_spent = sum(float(order["total_amount"]) for order in user.get("orders", []))
                
                row = f"{user['user_id']},{name},{email},{role},{created},{orders_count},${total_spent:.2f}"
                rows.append(row)
            
            return header + "\n".join(rows)
        else:
            # Text format (more detailed)
            report = "USER ACTIVITY REPORT\n"
            report += "=" * 50 + "\n\n"
            
            # Summary
            total_users = len(user_data)
            admin_count = sum(1 for user in user_data if user["role"] == "admin")
            customer_count = sum(1 for user in user_data if user["role"] == "user")
            
            report += f"Total Users: {total_users}\n"
            report += f"Administrators: {admin_count}\n"
            report += f"Regular Users: {customer_count}\n\n"
            report += "=" * 50 + "\n\n"
            
            # User details
            for user in user_data:
                report += f"USER: {user['first_name']} {user['last_name']}\n"
                report += f"ID: {user['user_id']}\n"
                
                email = user.get("email", user["username"])
                if not email and user.get("username"):
                    email = user["username"]
                report += f"Email: {email}\n"
                
                report += f"Role: {user['role']}\n"
                report += f"Created: {user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else 'N/A'}\n"
                
                # Order information if available
                if "orders" in user and user["orders"]:
                    orders_count = len(user["orders"])
                    total_spent = sum(float(order["total_amount"]) for order in user["orders"])
                    
                    report += f"Orders in Period: {orders_count}\n"
                    report += f"Total Spent in Period: ${total_spent:.2f}\n"
                    
                    if "total_orders" in user:
                        report += f"Total Orders (All Time): {user['total_orders']}\n\n"
                    
                    report += "Recent Orders:\n"
                    for order in sorted(user["orders"], key=lambda x: x["order_date"], reverse=True)[:5]:  # Show up to 5 most recent orders
                        date = order["order_date"].strftime("%Y-%m-%d %H:%M")
                        amount = float(order["total_amount"])
                        status = order["status"]
                        
                        report += f"  - Order #{order['order_id']} ({date}): ${amount:.2f} - {status}\n"
                else:
                    report += "No orders found in selected period.\n"
                
                report += "\n" + "-" * 50 + "\n\n"
            
            return report

    def download_user_report(self):
        """Download user report to file"""
        if not self.user_report_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Determine file extension
        ext = "csv" if self.user_format_var.get() == "csv" else "txt"
        
        # Get save location from user
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[
                (f"{ext.upper()} files", f"*.{ext}"),
                ("All files", "*.*")
            ],
            title="Save User Activity Report"
        )
        
        if not filename:
            return  # User cancelled
        
        # Save the file
        try:
            with open(filename, 'w', newline='') as file:
                file.write(self.user_report_data)
            
            messagebox.showinfo("Success", f"Report saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    
    # Check if username was provided from command line
    login_mode = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "login":
            login_mode = True
            print("Starting in login mode")  # Debug message
        else:
            username = sys.argv[1]
            print(f"Starting with username: {username}")  # Debug message
    else:
        # Try to read from file
        username, role = read_login_file()
        if not username or role != "admin":
            login_mode = True
            print("No valid admin credentials found, starting in login mode")  # Debug message
    
    # Print debugging information
    print(f"Admin view starting with login_mode={login_mode}")
    
    try:
        app = AdminApp(root, None if login_mode else username)
        root.mainloop()
    except Exception as e:
        print(f"Error starting AdminApp: {e}")
        # If running in GUI mode, show error dialog
        if 'root' in locals() and root:
            messagebox.showerror("Error", f"Failed to start admin panel: {e}")
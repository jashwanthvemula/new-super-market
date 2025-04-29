import io
import sys
import os
import numpy as np
from matplotlib import pyplot as plt
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
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
    def _init_(self, parent_frame, admin_app):
        self.admin_app = admin_app
        super()._init_(parent_frame)
    
    def navigate_to(self, destination):
        if destination == "Manage Inventory":
            self.admin_app.show_inventory_management()
        elif destination == "Manage Users":
            self.admin_app.show_user_management()
        elif destination == "Generate Report":
            self.admin_app.show_report_generation()
        elif destination == "Logout":
            self.admin_app.logout()
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
    def clear_inventory_search(self):
        """Clear the inventory search field and refresh the table"""
        if hasattr(self, 'inventory_search'):
            self.inventory_search.delete(0, 'end')
            self.refresh_inventory_table()
    
    def adjust_reports_layout(self, width, height):
        """Adjust the reports layout based on window size"""
        if hasattr(self, 'report_tabview'):
            # For narrow screens, reduce padding and adjust panel heights
            if width < 900:
                # Sales and Inventory (side-by-side layout)
                self._adjust_report_tab_layout(self.sales_left_panel, self.sales_right_panel, width, True)
                if hasattr(self, 'inventory_left_panel') and hasattr(self, 'inventory_right_panel'):
                    self._adjust_report_tab_layout(self.inventory_left_panel, self.inventory_right_panel, width, True)
                # User Activity (vertical layout)
                if hasattr(self, 'user_options_panel') and hasattr(self, 'user_preview_panel'):
                    # Reduce padding for narrow screens
                    self.user_options_panel.configure(padx=5, pady=(0, 5))
                    self.user_preview_panel.configure(padx=5, pady=(5, 0))
                    # Limit options panel height to prevent overflow
                    self.user_options_panel.pack_configure(fill="x", expand=False)
                    self.user_preview_panel.pack_configure(fill="both", expand=True)
            else:
                # Sales and Inventory (restore side-by-side)
                self._adjust_report_tab_layout(self.sales_left_panel, self.sales_right_panel, width, False)
                if hasattr(self, 'inventory_left_panel') and hasattr(self, 'inventory_right_panel'):
                    self._adjust_report_tab_layout(self.inventory_left_panel, self.inventory_right_panel, width, False)
                # User Activity (restore default vertical layout)
                if hasattr(self, 'user_options_panel') and hasattr(self, 'user_preview_panel'):
                    self.user_options_panel.configure(padx=10, pady=(0, 10))
                    self.user_preview_panel.configure(padx=10, pady=(10, 0))
                    self.user_options_panel.pack_configure(fill="x", expand=False)
                    self.user_preview_panel.pack_configure(fill="both", expand=True)
    def _adjust_report_tab_layout(self, left_panel, right_panel, width, vertical_layout):
        """Helper method to adjust layout of report tab panels"""
            # First, unpack both panels
        left_panel.pack_forget()
        right_panel.pack_forget()
            
            # Then repack based on layout mode
        if vertical_layout:
            left_panel.configure(width=width - 60)
            left_panel.pack(side="top", fill="x", pady=(0, 10))
                
            right_panel.configure(width=width - 60)
            right_panel.pack(side="top", fill="both", expand=True)
        else:
            left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)
            right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
    def ensure_reports_folder(self):
        """Create reports folder if it doesn't exist"""
        reports_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        if not os.path.exists(reports_path):
            os.makedirs(reports_path)
        return reports_path
            
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
    
# This is an update to the admin_login method in admin_view.py

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
                "SELECT user_id, first_name, last_name, role, status FROM Users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            
            user = cursor.fetchone()
            
            if user and user["role"] == "admin":
                # Check if admin account is active
                if user["status"] != "active":
                    messagebox.showerror("Account Disabled", "Your admin account has been disabled. Please contact another administrator.")
                    return
                    
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
    
    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Check file size (e.g., max 1MB)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                if file_size > 1:
                    messagebox.showwarning("File Too Large", "Image size must be less than 1MB.")
                    return
                
                with open(file_path, 'rb') as file:
                    self.selected_image_data = file.read()
                self.image_name_label.configure(text=os.path.basename(file_path))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read image: {str(e)}")
                self.selected_image_data = None
                self.image_name_label.configure(text="No image selected")
        else:
            self.selected_image_data = None
            self.image_name_label.configure(text="No image selected")

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
        
        # Image Upload - Row 4
        image_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        image_frame.pack(fill="x", pady=5)
        
        image_label = ctk.CTkLabel(image_frame, text="Image", width=100, font=("Arial", 14), text_color="gray")
        image_label.pack(side="left", padx=(0, 10))
        
        self.image_button = ctk.CTkButton(image_frame, text="Select Image",
                                        fg_color="#3b82f6", hover_color="#2563eb",
                                        font=("Arial", 14), height=40, width=150,
                                        command=self.select_image)
        self.image_button.pack(side="left")
        
        # Display selected image name
        self.image_name_label = ctk.CTkLabel(image_frame, text="No image selected", font=("Arial", 12), text_color="gray")
        self.image_name_label.pack(side="left", padx=(10, 0))
        
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
        
        # Initialize selected image data
        self.selected_image_data = None
        
        # Existing Inventory Section (unchanged)
        self.inventory_section = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.inventory_section.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Header with filter/search - using a flex-like layout
        header_frame = ctk.CTkFrame(self.inventory_section, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 15))
        
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(side="left", fill="y")
        
        inventory_label = ctk.CTkLabel(title_container, text="Existing Inventory",
                                    font=("Arial", 18, "bold"), text_color="black")
        inventory_label.pack(side="left")
        
        search_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_container.pack(side="right", fill="y")
        
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
        
        clear_search_btn = ctk.CTkButton(search_frame, text="Clear",
                                    fg_color="#ef4444", hover_color="#dc2626",
                                    font=("Arial", 14), height=35, width=80,
                                    command=self.clear_inventory_search)
        clear_search_btn.pack(side="left")
        
        table_frame = ctk.CTkFrame(self.inventory_section, fg_color="white")
        table_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("name", "price", "stock", "status", "actions")
        self.inventory_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.inventory_table.heading("name", text="Name")
        self.inventory_table.heading("price", text="Price")
        self.inventory_table.heading("stock", text="Stock")
        self.inventory_table.heading("status", text="Status")
        self.inventory_table.heading("actions", text="Actions")
        
        self.inventory_table.column("name", width=300, anchor="w")
        self.inventory_table.column("price", width=100, anchor="center")
        self.inventory_table.column("stock", width=100, anchor="center")
        self.inventory_table.column("status", width=100, anchor="center")
        self.inventory_table.column("actions", width=200, anchor="center")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.inventory_table.yview)
        self.inventory_table.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.inventory_table.pack(fill="both", expand=True)
        
        self.inventory_table.bind("<Double-1>", self.edit_product)
        
        action_frame = ctk.CTkFrame(self.inventory_section, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=10)
        
        edit_btn = ctk.CTkButton(action_frame, text="Edit Selected",
                            fg_color="#eab308", hover_color="#ca8a04",
                            font=("Arial", 14), height=40, width=120,
                            command=lambda: self.edit_product(None))
        edit_btn.pack(side="left", padx=(0, 10))
        
        toggle_status_btn = ctk.CTkButton(action_frame, text="Toggle Status",
                                        fg_color="#8b5cf6", hover_color="#7c3aed",
                                        font=("Arial", 14), height=40, width=120,
                                        command=self.toggle_product_status)
        toggle_status_btn.pack(side="left", padx=(0, 10))
        
        delete_btn = ctk.CTkButton(action_frame, text="Delete Selected",
                                fg_color="#ef4444", hover_color="#dc2626",
                                font=("Arial", 14), height=40, width=120,
                                command=self.delete_selected_product)
        delete_btn.pack(side="left")
        
        refresh_btn = ctk.CTkButton(action_frame, text="Refresh",
                                fg_color="#10b981", hover_color="#059669",
                                font=("Arial", 14), height=40, width=120,
                                command=self.refresh_inventory_table)
        refresh_btn.pack(side="right")
        
        self.refresh_inventory_table()
    def fetch_inventory(self, search_term=None):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            if search_term:
                cursor.execute(
                    "SELECT product_id, name, price, stock, status FROM Products WHERE name LIKE %s ORDER BY name",
                    (f"%{search_term}%",)
                )
            else:
                cursor.execute("SELECT product_id, name, price, stock, status FROM Products ORDER BY name")
            
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
            status = product["status"].capitalize()
            
            # Set row color based on status
            tag = "inactive" if status.lower() != "active" else ""
            
            self.inventory_table.insert("", "end", values=(name, price, stock, status, ""), tags=(str(product_id), tag))
        
        # Configure tag colors
        self.inventory_table.tag_configure("inactive", background="#f1f5f9")
    def update_product_status(self, product_id, status):
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            cursor.execute(
                "UPDATE Products SET status = %s WHERE product_id = %s",
                (status, product_id)
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
    def toggle_product_status(self):
        selected_items = self.inventory_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a product.")
            return
        
        item = selected_items[0]
        values = self.inventory_table.item(item, 'values')
        
        if not values:
            return
        
        # Get product ID from tag
        product_id = int(self.inventory_table.item(item, 'tags')[0])
        product_name = values[0]
        current_status = values[3].lower()
        
        # Confirm action
        new_status = "inactive" if current_status == "active" else "active"
        action = "disable" if current_status == "active" else "enable"
        
        confirm = messagebox.askyesno("Confirm Action", f"Are you sure you want to {action} '{product_name}'?")
        if not confirm:
            return
        
        # Update product status
        if self.update_product_status(product_id, new_status):
            messagebox.showinfo("Success", f"Product '{product_name}' has been {action}d.")
            self.refresh_inventory_table()

    def clear_product_fields(self):
        self.item_name_entry.delete(0, 'end')
        self.item_name_entry.insert(0, "")
        
        self.price_entry.delete(0, 'end')
        self.price_entry.insert(0, "")
        
        self.stock_entry.delete(0, 'end')
        self.stock_entry.insert(0, "")
        
        # Reset image selection
        self.selected_image_data = None
        self.image_name_label.configure(text="No image selected")
        
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
            
            # Insert new product with image data
            cursor.execute(
                "INSERT INTO Products (name, price, stock, image, status) VALUES (%s, %s, %s, %s, %s)",
                (name, price_val, stock_val, self.selected_image_data, "active")
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
    
    def update_product(self, product_id, name, price, stock, status="active"):
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
            
            # Update product with image data
            cursor.execute(
                "UPDATE Products SET name = %s, price = %s, stock = %s, image = %s, status = %s WHERE product_id = %s",
                (name, price_val, stock_val, self.selected_image_data, status, product_id)
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
        """Open an improved dialog to edit product details with properly visible buttons"""
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
        
        # Fetch product details from database
        product_details = self.fetch_product_details(product_id)
        if not product_details:
            messagebox.showerror("Error", "Failed to fetch product details.")
            return
        
        # Create a modern and visually appealing popup dialog
        self.edit_product_dialog = ctk.CTkToplevel(self.root)
        self.edit_product_dialog.title("Edit Product")
        self.edit_product_dialog.geometry("550x650")  # Increased height to ensure buttons are visible
        self.edit_product_dialog.resizable(False, False)
        self.edit_product_dialog.grab_set()  # Make dialog modal
        
        # Center dialog on screen
        self.edit_product_dialog.update_idletasks()
        width = self.edit_product_dialog.winfo_width()
        height = self.edit_product_dialog.winfo_height()
        x = (self.edit_product_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.edit_product_dialog.winfo_screenheight() // 2) - (height // 2)
        self.edit_product_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create a scrollable main frame to ensure all content is accessible
        main_frame = ctk.CTkScrollableFrame(self.edit_product_dialog, fg_color="#f8fafc")
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Content frame with modern card design
        content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15, 
                                border_width=1, border_color="#e2e8f0")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with colored accent
        header_frame = ctk.CTkFrame(content_frame, fg_color="#3b82f6", corner_radius=0, height=8)
        header_frame.pack(fill="x", padx=0, pady=(0, 15))
        
        # Create a grid layout for form elements
        form_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=25, pady=(5, 15))
        
        # Title
        title_label = ctk.CTkLabel(form_frame, text="Edit Product", 
                                font=("Arial", 22, "bold"), text_color="#1e293b")
        title_label.pack(anchor="w", pady=(5, 20))
        
        # Product ID (read-only)
        id_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        id_frame.pack(fill="x", pady=(0, 15))
        
        id_label = ctk.CTkLabel(id_frame, text="Product ID:", 
                            font=("Arial", 14, "bold"), text_color="#64748b", width=120)
        id_label.pack(side="left")
        
        id_value = ctk.CTkLabel(id_frame, text=str(product_id), 
                            font=("Arial", 14), text_color="#334155")
        id_value.pack(side="left", padx=(10, 0))
        
        # Product Name
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=(0, 15))
        
        name_label = ctk.CTkLabel(name_frame, text="Name:", 
                            font=("Arial", 14, "bold"), text_color="#64748b", width=120)
        name_label.pack(side="left")
        
        self.edit_name_entry = ctk.CTkEntry(name_frame, 
                                        height=40, 
                                        corner_radius=8,
                                        border_width=1,
                                        border_color="#cbd5e1",
                                        fg_color="white",
                                        font=("Arial", 14))
        self.edit_name_entry.pack(side="left", fill="x", expand=True)
        self.edit_name_entry.insert(0, product_details.get("name", ""))
        
        # Price with currency symbol
        price_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        price_frame.pack(fill="x", pady=(0, 15))
        
        price_label = ctk.CTkLabel(price_frame, text="Price ($):", 
                                font=("Arial", 14, "bold"), text_color="#64748b", width=120)
        price_label.pack(side="left")
        
        # Create a container for price with currency symbol background
        price_container = ctk.CTkFrame(price_frame, fg_color="transparent")
        price_container.pack(side="left", fill="x", expand=True)
        
        self.edit_price_entry = ctk.CTkEntry(price_container, 
                                        height=40, 
                                        corner_radius=8,
                                        border_width=1,
                                        border_color="#cbd5e1",
                                        fg_color="white",
                                        font=("Arial", 14))
        self.edit_price_entry.pack(fill="x", expand=True)
        self.edit_price_entry.insert(0, str(product_details.get("price", "")).replace('$', ''))
        
        # Stock with stepper buttons
        stock_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        stock_frame.pack(fill="x", pady=(0, 15))
        
        stock_label = ctk.CTkLabel(stock_frame, text="Stock:", 
                                font=("Arial", 14, "bold"), text_color="#64748b", width=120)
        stock_label.pack(side="left")
        
        # Create a container with stock entry and buttons
        stock_container = ctk.CTkFrame(stock_frame, fg_color="transparent")
        stock_container.pack(side="left", fill="x", expand=True)
        
        # Stock stepper buttons
        self.edit_stock_var = ctk.StringVar(value=str(product_details.get("stock", 0)))
        
        # Minus button
        minus_btn = ctk.CTkButton(stock_container, text="-", 
                            width=40, height=40, 
                            corner_radius=8,
                            fg_color="#e2e8f0", 
                            hover_color="#cbd5e1",
                            text_color="#334155",
                            font=("Arial", 16, "bold"),
                            command=lambda: self.decrease_stock())
        minus_btn.pack(side="left")
        
        # Stock entry
        self.edit_stock_entry = ctk.CTkEntry(stock_container, 
                                        height=40, 
                                        width=80,
                                        textvariable=self.edit_stock_var,
                                        corner_radius=8,
                                        border_width=1,
                                        border_color="#cbd5e1",
                                        fg_color="white",
                                        font=("Arial", 14),
                                        justify="center")
        self.edit_stock_entry.pack(side="left", padx=10)
        
        # Plus button
        plus_btn = ctk.CTkButton(stock_container, text="+", 
                            width=40, height=40, 
                            corner_radius=8,
                            fg_color="#e2e8f0", 
                            hover_color="#cbd5e1",
                            text_color="#334155",
                            font=("Arial", 16, "bold"),
                            command=lambda: self.increase_stock())
        plus_btn.pack(side="left")
        
        # Image selection with preview
        image_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        image_frame.pack(fill="x", pady=(0, 15))
        
        image_label = ctk.CTkLabel(image_frame, text="Image:", 
                                font=("Arial", 14, "bold"), text_color="#64748b", width=120)
        image_label.pack(side="left", anchor="n")
        
        # Container for image selection and preview
        image_container = ctk.CTkFrame(image_frame, fg_color="transparent")
        image_container.pack(side="left", fill="x", expand=True)
        
        # Image preview frame with placeholder
        self.image_preview_frame = ctk.CTkFrame(image_container, 
                                            fg_color="#f1f5f9", 
                                            corner_radius=8,
                                            width=120, height=120)
        self.image_preview_frame.pack(side="top", anchor="w", pady=(0, 10))
        self.image_preview_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Image preview label or placeholder
        self.image_preview_label = ctk.CTkLabel(self.image_preview_frame, 
                                            text="No Image", 
                                            font=("Arial", 12), 
                                            text_color="#64748b")
        self.image_preview_label.pack(expand=True)
        
        # Try to display the existing image
        if product_details.get("image"):
            try:
                # Convert binary data to image
                image_data = product_details["image"]
                if image_data:
                    # Create a PIL Image from binary data
                    pil_image = Image.open(io.BytesIO(image_data))
                    
                    # Resize image to fit preview
                    pil_image.thumbnail((115, 115))
                    
                    # Convert to CTkImage
                    preview_image = ctk.CTkImage(
                        light_image=pil_image,
                        dark_image=pil_image,
                        size=(115, 115)
                    )
                    
                    # Update preview label
                    self.image_preview_label.configure(image=preview_image, text="")
                    self.edit_selected_image_data = image_data
                else:
                    self.edit_selected_image_data = None
            except Exception as e:
                print(f"Error loading image preview: {e}")
                self.edit_selected_image_data = None
        else:
            self.edit_selected_image_data = None
        
        # Button to select image
        self.edit_image_button = ctk.CTkButton(image_container, 
                                            text="Select Image",
                                            fg_color="#3b82f6", 
                                            hover_color="#2563eb",
                                            font=("Arial", 14), 
                                            height=36,
                                            corner_radius=8,
                                            command=self.select_edit_image)
        self.edit_image_button.pack(side="top", anchor="w")
        
        # Status options with styled radio buttons
        status_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 15))
        
        status_label = ctk.CTkLabel(status_frame, text="Status:", 
                                font=("Arial", 14, "bold"), text_color="#64748b", width=120)
        status_label.pack(side="left", anchor="n")
        
        # Container for radio buttons with visual enhancement
        status_container = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_container.pack(side="left", fill="x", expand=True)
        
        self.edit_status_var = ctk.StringVar(value=product_details.get("status", "active"))
        
        # Active status with colored indicator
        active_frame = ctk.CTkFrame(status_container, fg_color="transparent")
        active_frame.pack(anchor="w", pady=(0, 5))
        
        active_indicator = ctk.CTkFrame(active_frame, fg_color="#10b981", width=8, height=16, corner_radius=4)
        active_indicator.pack(side="left", padx=(0, 10))
        
        active_radio = ctk.CTkRadioButton(active_frame, text="Active", 
                                    variable=self.edit_status_var, value="active",
                                    font=("Arial", 14),
                                    fg_color="#10b981",
                                    border_color="#10b981")
        active_radio.pack(side="left")
        
        # Inactive status with colored indicator
        inactive_frame = ctk.CTkFrame(status_container, fg_color="transparent")
        inactive_frame.pack(anchor="w")
        
        inactive_indicator = ctk.CTkFrame(inactive_frame, fg_color="#f97316", width=8, height=16, corner_radius=4)
        inactive_indicator.pack(side="left", padx=(0, 10))
        
        inactive_radio = ctk.CTkRadioButton(inactive_frame, text="Inactive", 
                                        variable=self.edit_status_var, value="inactive",
                                        font=("Arial", 14),
                                        fg_color="#f97316",
                                        border_color="#f97316")
        inactive_radio.pack(side="left")
        
        # Description or notes (optional)
        notes_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        notes_frame.pack(fill="x", pady=(0, 15))
        
        notes_label = ctk.CTkLabel(notes_frame, text="Notes:", 
                                font=("Arial", 14, "bold"), text_color="#64748b", width=120)
        notes_label.pack(side="left", anchor="n")
        
        self.edit_notes = ctk.CTkTextbox(notes_frame, 
                                    height=80, 
                                    corner_radius=8,
                                    border_width=1,
                                    border_color="#cbd5e1",
                                    fg_color="white",
                                    font=("Arial", 14))
        self.edit_notes.pack(side="left", fill="x", expand=True)
        
        # Add description text if available
        if product_details.get("description"):
            self.edit_notes.insert("1.0", product_details["description"])
        
        # Create a separate frame for buttons at the bottom of the dialog
        # This is outside the scrollable area to ensure visibility
        buttons_container = ctk.CTkFrame(self.edit_product_dialog, fg_color="#f1f5f9", height=80)
        buttons_container.pack(side="bottom", fill="x", padx=0, pady=0)
        
        # Make sure the container has a minimum height
        buttons_container.pack_propagate(False)
        
        # Center the buttons
        buttons_frame = ctk.CTkFrame(buttons_container, fg_color="transparent")
        buttons_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Cancel button
        cancel_btn = ctk.CTkButton(buttons_frame, text="Cancel",
                                fg_color="#e2e8f0", 
                                hover_color="#cbd5e1",
                                text_color="#334155",
                                font=("Arial", 14, "bold"), 
                                height=46,
                                width=150,
                                corner_radius=8,
                                command=self.edit_product_dialog.destroy)
        cancel_btn.pack(side="left", padx=(0, 15))
        
        # Save button
        save_btn = ctk.CTkButton(buttons_frame, text="Save Changes",
                            fg_color="#3b82f6", 
                            hover_color="#2563eb",
                            font=("Arial", 14, "bold"), 
                            height=46,
                            width=200,
                            corner_radius=8,
                            command=lambda: self.save_product_edits(product_id))
        save_btn.pack(side="left")
        
        # Store the product ID for later use
        self.editing_product_id = product_id

    def increase_stock(self):
        """Increase stock value in edit product dialog"""
        try:
            current = int(self.edit_stock_var.get())
            self.edit_stock_var.set(str(current + 1))
        except ValueError:
            self.edit_stock_var.set("1")
    def decrease_stock(self):
        """Decrease stock value in edit product dialog"""
        try:
            current = int(self.edit_stock_var.get())
            if current > 0:
                self.edit_stock_var.set(str(current - 1))
        except ValueError:
            self.edit_stock_var.set("0")
    def select_edit_image(self):
        """Open a file dialog to select an image file for editing with improved preview"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Read image file
            with open(file_path, 'rb') as file:
                self.edit_selected_image_data = file.read()
            
            # Create a preview
            try:
                # Clear previous image
                for widget in self.image_preview_frame.winfo_children():
                    widget.destroy()
                    
                # Create a PIL Image from binary data
                pil_image = Image.open(io.BytesIO(self.edit_selected_image_data))
                
                # Resize image to fit preview
                pil_image.thumbnail((115, 115))
                
                # Convert to CTkImage
                preview_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(115, 115)
                )
                
                # Create new label with image
                image_label = ctk.CTkLabel(self.image_preview_frame, 
                                    image=preview_image, 
                                    text="")
                image_label.pack(expand=True)
                
                # Store reference to prevent garbage collection
                self.image_preview_label = image_label
                
            except Exception as e:
                # If image preview fails, show text label
                error_label = ctk.CTkLabel(self.image_preview_frame, 
                                        text=f"Preview Error",
                                        font=("Arial", 12), 
                                        text_color="#ef4444")
                error_label.pack(expand=True)
                print(f"Error creating preview: {e}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read image: {str(e)}", parent=self.edit_product_dialog)
            self.edit_selected_image_data = None
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
    def fetch_product_details(self, product_id):
        """Fetch complete product details from the database"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT * FROM Products WHERE product_id = %s",
                (product_id,)
            )
            
            product = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return product if product else {}
        except Exception as e:
            print(f"Error fetching product details: {e}")
            return {}
    
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
        self.current_view = "users"  # Set current view for resize handling
        
        # Header
        header_label = ctk.CTkLabel(self.content_frame, text="User Management",
                                font=("Arial", 24, "bold"), text_color="#2563eb")
        header_label.pack(anchor="w", padx=30, pady=(30, 20))
        
        # Create tabview for different user management sections
        self.user_tabview = ctk.CTkTabview(self.content_frame, corner_radius=15)
        self.user_tabview.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Create tabs
        add_user_tab = self.user_tabview.add("Add User")
        manage_users_tab = self.user_tabview.add("Manage Users")
        
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
        
        # Create a custom style for the treeview with improved visibility
        style = ttk.Style()
        style.configure("Treeview", 
                        background="white",
                        foreground="black",
                        fieldbackground="white", 
                        rowheight=40)
        style.configure("Treeview.Heading", 
                        font=('Arial', 12, 'bold'),
                        background="#f8fafc", 
                        foreground="black")
        style.map('Treeview', 
                background=[('selected', '#e5e7eb')],
                foreground=[('selected', 'black')])
        
        # Create a frame for the table
        table_frame = ctk.CTkFrame(manage_users_frame, fg_color="#f8fafc", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create columns
        columns = ("name", "email", "role", "status", "actions")
        
        # Create treeview with explicit height
        self.users_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Define headings
        self.users_table.heading("name", text="Name")
        self.users_table.heading("email", text="Email")
        self.users_table.heading("role", text="Role")
        self.users_table.heading("status", text="Status") # Add status heading
        self.users_table.heading("actions", text="Actions")
        
        # Define column widths and alignment
        self.users_table.column("name", width=180, anchor="w")
        self.users_table.column("email", width=220, anchor="w")
        self.users_table.column("role", width=80, anchor="center")
        self.users_table.column("status", width=80, anchor="center") # Add status column
        self.users_table.column("actions", width=150, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_table.yview)
        self.users_table.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar first, then the treeview
        scrollbar.pack(side="right", fill="y")
        self.users_table.pack(side="left", fill="both", expand=True)
        
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

        # Add this Toggle Status button here:
        toggle_status_btn = ctk.CTkButton(action_frame, text="Toggle Status", 
                                        fg_color="#8b5cf6", hover_color="#7c3aed",
                                        font=("Arial", 14), height=40, width=150,
                                        command=self.toggle_user_status)
        toggle_status_btn.pack(side="left", padx=(0, 10))

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
        
        # Add a debug button
        debug_frame = ctk.CTkFrame(manage_users_frame, fg_color="transparent")
        debug_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        debug_btn = ctk.CTkButton(debug_frame, text="Test Display", 
                            fg_color="#6366f1", hover_color="#4f46e5",
                            font=("Arial", 14), height=35, width=150,
                            command=self.test_users_display)
        debug_btn.pack(side="left")
        
        # Add test function for debugging
        def test_users_display(self):
            """Test function to directly add users to the table"""
            try:
                # Clear the table
                for item in self.users_table.get_children():
                    self.users_table.delete(item)
                
                # Add test entries directly to the table
                self.users_table.insert("", "end", values=("Admin User", "admin@supermarket.com", "Admin", ""), tags=("1",))
                self.users_table.insert("", "end", values=("John Doe", "user1@example.com", "User", ""), tags=("2",))
                self.users_table.insert("", "end", values=("Test User", "test@example.com", "User", ""), tags=("3",))
                
                messagebox.showinfo("Test", "Added test users to the table")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add test users: {str(e)}")
                print(f"Error in test_users_display: {str(e)}")
        
        # Assign the method to the class
        self.test_users_display = test_users_display.__get__(self, self.__class__)
        
        # Now update the refresh_users_table method to properly handle your data
        def updated_refresh_users_table(self, search_term=None):
            """Updated method to properly display users in the table"""
            # Clear existing items
            for item in self.users_table.get_children():
                self.users_table.delete(item)
            
            # Fetch and display users
            users = self.fetch_users(search_term)
            print(f"Got {len(users)} users to display")
            
            # Add each user with error handling
            for user in users:
                try:
                    # Extract values from your data structure
                    user_id = user["user_id"]
                    full_name = f"{user['first_name']} {user['last_name']}"
                    email = user["email"]
                    role = user["role"].capitalize()
                    
                    # Insert with your exact data structure
                    self.users_table.insert(
                        "", "end", 
                        values=(full_name, email, role, ""),
                        tags=(str(user_id),)
                    )
                except Exception as e:
                    print(f"Error adding user {user.get('user_id')}: {str(e)}")
            
            # Print how many items were added
            items = self.users_table.get_children()
            print(f"Table now has {len(items)} rows")
        
        # Replace the original method with the improved version
        self.refresh_users_table = updated_refresh_users_table.__get__(self, self.__class__)
        
        # Populate users table on startup
        self.refresh_users_table()
    def toggle_user_status(self):
        """Toggle a user's status between active and inactive"""
        selected_items = self.users_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a user.")
            return
        
        item = selected_items[0]
        values = self.users_table.item(item, 'values')
        
        if not values:
            return
        
        # Get user ID from tag
        user_id = int(self.users_table.item(item, 'tags')[0])
        user_name = values[0]
        current_status = values[3].lower()
        
        # Check if user is trying to disable themselves
        if user_id == self.current_user["user_id"]:
            messagebox.showwarning("Cannot Disable", "You cannot disable your own account while logged in.")
            return
        
        # Confirm action
        new_status = "inactive" if current_status == "active" else "active"
        action = "disable" if current_status == "active" else "enable"
        
        confirm = messagebox.askyesno("Confirm Action", f"Are you sure you want to {action} '{user_name}'?")
        if not confirm:
            return
        
        # Update user status
        if self.update_user_status(user_id, new_status):
            messagebox.showinfo("Success", f"User '{user_name}' has been {action}d.")
            self.refresh_users_table()
    def update_user_status(self, user_id, status):
        """Update user status in database"""
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            cursor.execute(
                "UPDATE Users SET status = %s WHERE user_id = %s",
                (status, user_id)
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

    def refresh_users_table(self, search_term=None):
        """Refresh the users table with data from the database"""
        print("Refreshing users table")  # Debug print
        
        # Clear existing items
        for item in self.users_table.get_children():
            self.users_table.delete(item)
        
        # Fetch and display users
        users = self.fetch_users(search_term)
        print(f"Got {len(users)} users to display")
        
        # Process each user
        for user in users:
            try:
                # Extract user data
                user_id = user["user_id"] 
                full_name = f"{user['first_name']} {user['last_name']}"
                email = user["email"]
                role = user["role"].capitalize()
                status = user.get("status", "active").capitalize()  # Get status with default
                
                # Set row color based on status
                tag = "inactive" if status.lower() != "active" else ""
                
                # Debug print
                print(f"Adding user to table: {full_name}, {email}, {role}, {status}")
                
                # Insert into table with status
                item_id = self.users_table.insert(
                    "", "end",  # parent and index
                    values=(full_name, email, role, status, ""),  # values for each column
                    tags=(str(user_id), tag)  # tags for identifying the row and styling
                )
                
                print(f"Added user {full_name} with item_id: {item_id}")
                
            except Exception as e:
                # Print any errors but continue processing other users
                print(f"Error adding user {user.get('user_id', 'unknown')}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Configure tag colors for inactive users
        self.users_table.tag_configure("inactive", background="#f1f5f9")
        
        # Debug: Show how many items are now in the table
        items = self.users_table.get_children()
        print(f"Table now has {len(items)} rows after refresh")
        
        # Make sure table is visible and update display
        self.users_table.update()

    def fetch_users(self, search_term=None):
        """Fetch users from database with optional search filter"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            if search_term:
                # Add wildcard characters to the search term for partial matching
                search_pattern = f"%{search_term}%"
                
                # Search through first name, last name, username, and email
                cursor.execute(
                    """
                    SELECT user_id, first_name, last_name, username, email, role, status 
                    FROM Users 
                    WHERE first_name LIKE %s OR last_name LIKE %s 
                    OR username LIKE %s OR email LIKE %s
                    ORDER BY role, first_name, last_name
                    """,
                    (search_pattern, search_pattern, search_pattern, search_pattern)
                )
            else:
                cursor.execute(
                    """
                    SELECT user_id, first_name, last_name, username, email, role, status 
                    FROM Users 
                    ORDER BY role, first_name, last_name
                    """
                )
            
            users = cursor.fetchall()
            return users
        except Exception as err:
            print(f"Error fetching users: {err}")  # Add print for debugging
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def search_users(self):
        """Search users based on input text"""
        search_term = self.user_search.get().strip()
        
        if not search_term:
            # If search field is empty, show all users
            self.refresh_users_table()
            return
        
        # Refresh the table with search results
        self.refresh_users_table(search_term)
    def update_user_search_frame(self, manage_users_frame):
        """Create an improved search frame for user management"""
        # Search frame with better UI
        search_frame = ctk.CTkFrame(manage_users_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Create a container for search components
        search_container = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_container.pack(side="left", fill="y")
        
        # Search label
        search_label = ctk.CTkLabel(search_container, text="Search:", 
                                font=("Arial", 14), text_color="gray")
        search_label.pack(side="left", padx=(0, 10))
        
        # Search entry with increased width
        self.user_search = ctk.CTkEntry(search_container, placeholder_text="Search by name or email...",
                                height=35, width=250, corner_radius=5)
        self.user_search.pack(side="left", padx=(0, 10))
        
        # Bind the Enter key to trigger search
        self.user_search.bind("<Return>", lambda event: self.search_users())
        
        # Search button
        search_btn = ctk.CTkButton(search_container, text="Search",
                                fg_color="#3b82f6", hover_color="#2563eb",
                                font=("Arial", 14), height=35, width=80,
                                command=self.search_users)
        search_btn.pack(side="left", padx=(0, 10))
        
        # Clear search button
        clear_btn = ctk.CTkButton(search_container, text="Clear",
                                fg_color="#ef4444", hover_color="#dc2626",
                                font=("Arial", 14), height=35, width=80,
                                command=self.clear_user_search)
        clear_btn.pack(side="left")
        
        # Create a container for the right side controls (if needed)
        right_container = ctk.CTkFrame(search_frame, fg_color="transparent")
        right_container.pack(side="right", fill="y")
    
        return search_frame
    def clear_user_search(self):
        """Clear the user search field and refresh the table"""
        if hasattr(self, 'user_search'):
            self.user_search.delete(0, 'end')
            self.refresh_users_table()
    def fetch_users(self, search_term=None):
        """Fetch users from database with optional search filter"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            if search_term:
                # Add wildcard characters to the search term for partial matching
                search_pattern = f"%{search_term}%"
                
                # Search through first name, last name, username, and email
                cursor.execute(
                    """
                    SELECT user_id, first_name, last_name, username, email, role, status 
                    FROM Users 
                    WHERE first_name LIKE %s OR last_name LIKE %s 
                    OR username LIKE %s OR email LIKE %s
                    ORDER BY role, first_name, last_name
                    """,
                    (search_pattern, search_pattern, search_pattern, search_pattern)
                )
            else:
                cursor.execute(
                    """
                    SELECT user_id, first_name, last_name, username, email, role, status 
                    FROM Users 
                    ORDER BY role, first_name, last_name
                    """
                )
            
            users = cursor.fetchall()
            return users
        except Exception as err:
            print(f"Error fetching users: {err}")  # Add print for debugging
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    def setup_users_table(self, table_frame):
        """Create and configure the users table with proper columns and styling"""
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
        
        # Define columns with proper widths
        columns = ("name", "email", "role", "status", "actions")
        
        # Create treeview
        self.users_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        self.users_table.heading("name", text="Name")
        self.users_table.heading("email", text="Email")
        self.users_table.heading("role", text="Role")
        self.users_table.heading("status", text="Status")
        self.users_table.heading("actions", text="Actions")
        
        # Define column widths and alignment - adjusted for better proportions
        self.users_table.column("name", width=200, anchor="w")
        self.users_table.column("email", width=200, anchor="w")
        self.users_table.column("role", width=100, anchor="center")
        self.users_table.column("status", width=100, anchor="center")
        self.users_table.column("actions", width=150, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_table.yview)
        self.users_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.users_table.pack(fill="both", expand=True)
        
        # Bind double-click event for editing
        self.users_table.bind("<Double-1>", self.open_edit_user_dialog)
        
        # Configure tag for inactive users
        self.users_table.tag_configure("inactive", background="#f1f5f9")
        
        return self.users_table
    def debug_user_search(self):
        """Debugging helper for user search functionality"""
        search_term = self.user_search.get().strip()
        print(f"Debug: Searching for users with term: '{search_term}'")
        
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Test database connection
            print("Debug: Testing database connection...")
            if not connection or not connection.is_connected():
                print("Debug: Failed to connect to database")
                return
            print("Debug: Database connection successful")
            
            # Get total users count (sanity check)
            cursor.execute("SELECT COUNT(*) as count FROM Users")
            total_count = cursor.fetchone()["count"]
            print(f"Debug: Total users in database: {total_count}")
            
            if search_term:
                # Add wildcard characters to the search term for partial matching
                search_pattern = f"%{search_term}%"
                
                # Test search query
                print(f"Debug: Testing search with pattern: '{search_pattern}'")
                query = """
                    SELECT user_id, first_name, last_name, username, email, role, status 
                    FROM Users 
                    WHERE first_name LIKE %s OR last_name LIKE %s 
                    OR username LIKE %s OR email LIKE %s
                    ORDER BY role, first_name, last_name
                """
                
                print(f"Debug: Executing query: {query}")
                cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
                
                users = cursor.fetchall()
                print(f"Debug: Found {len(users)} users matching the search criteria")
                
                # Print out each matching user (with sensitive info redacted)
                for i, user in enumerate(users):
                    print(f"Debug: User {i+1}:")
                    print(f"  - ID: {user['user_id']}")
                    print(f"  - Name: {user['first_name']} {user['last_name']}")
                    print(f"  - Username: {user['username']}")
                    print(f"  - Role: {user['role']}")
                    print(f"  - Status: {user.get('status', 'active')}")
            
            print("Debug: User search debugging completed")
            
        except Exception as err:
            print(f"Debug ERROR: {err}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def repair_user_table(self):
        """Fix common issues with user table structure"""
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            print("Checking Users table structure...")
            
            # Check if status column exists
            cursor.execute("SHOW COLUMNS FROM Users LIKE 'status'")
            has_status_column = cursor.fetchone() is not None
            
            if not has_status_column:
                print("Adding missing 'status' column to Users table...")
                cursor.execute("ALTER TABLE Users ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'")
                connection.commit()
                print("Status column added successfully")
            else:
                print("Status column exists in Users table")
            
            # Set status to active for any NULL values
            cursor.execute("UPDATE Users SET status = 'active' WHERE status IS NULL")
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                print(f"Fixed {rows_updated} users with NULL status values")
                connection.commit()
            
            print("User table repair completed")
            messagebox.showinfo("Repair Complete", "User table structure has been checked and repaired if needed.")
            
        except Exception as err:
            print(f"Repair ERROR: {err}")
            messagebox.showerror("Repair Failed", f"An error occurred: {err}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    # Optional: Add a debug button to the admin interface
    def add_debug_button(self, parent_frame):
        """Add a debug button (for development purposes only)"""
        debug_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        debug_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        debug_btn = ctk.CTkButton(debug_frame, text="Debug Search", 
                            fg_color="#6b7280", hover_color="#4b5563",
                            font=("Arial", 12), height=30, width=120,
                            command=self.debug_user_search)
        debug_btn.pack(side="left", padx=(0, 10))
        
        repair_btn = ctk.CTkButton(debug_frame, text="Repair Table", 
                                fg_color="#6b7280", hover_color="#4b5563",
                                font=("Arial", 12), height=30, width=120,
                                command=self.repair_user_table)
        repair_btn.pack(side="left")
        
        # Add a note that this is for development only
        debug_note = ctk.CTkLabel(debug_frame, text="(Development tools - remove before production)", 
                            font=("Arial", 10), text_color="gray")
        debug_note.pack(side="left", padx=(10, 0))


    # def search_users(self):
    #     """Search users based on input text"""
    #     search_term = self.user_search.get().strip()
        
    #     if not search_term:
    #         # If search field is empty, show all users
    #         self.refresh_users_table()
    #         return
        
    #     # Refresh the table with search results
    #     self.refresh_users_table(search_term)
    
    def search_users(self):
        """Search users based on input text"""
        search_term = self.user_search.get().strip()
        
        if not search_term:
            # If search field is empty, show all users
            self.refresh_users_table()
            return
        
        # Clear existing items in the table
        for item in self.users_table.get_children():
            self.users_table.delete(item)
        
        # Fetch and display users matching the search term
        users = self.fetch_users(search_term)
        
        if not users:
            # No users found - show a message
            messagebox.showinfo("Search Results", "No users found matching your search criteria.")
            # Reset to show all users
            self.refresh_users_table()
            return
        
        # Display the filtered users
        for user in users:
            user_id = user["user_id"]
            full_name = f"{user['first_name']} {user['last_name']}"
            email = user.get("email", user["username"])
            if "@" not in email and email:
                email = f"{email}@example.com"  # Add domain if missing
            role = user["role"].capitalize()
            status = user.get("status", "active").capitalize()  # Get status with default
            
            # Set row color based on status
            tag = "inactive" if status.lower() != "active" else ""
            
            self.users_table.insert("", "end", values=(full_name, email, role, status, ""), 
                                tags=(str(user_id), tag))
        
        # Configure tag colors
        self.users_table.tag_configure("inactive", background="#f1f5f9")
        
    def refresh_users_table(self, search_term=None):
        """Refresh the users table with current data"""
        # Clear existing items
        for item in self.users_table.get_children():
            self.users_table.delete(item)
        
        # Fetch and display users
        users = self.fetch_users(search_term)
        
        for user in users:
            user_id = user["user_id"]
            full_name = f"{user['first_name']} {user['last_name']}"
            email = user.get("email", user["username"])
            if "@" not in email and email:
                email = f"{email}@example.com"  # Add domain if missing
            role = user["role"].capitalize()
            status = user.get("status", "active").capitalize()  # Get status with default
            
            # Set row color based on status
            tag = "inactive" if status.lower() != "active" else ""
            
            self.users_table.insert("", "end", values=(full_name, email, role, status, ""), 
                                tags=(str(user_id), tag))
        
        # Configure tag colors
        self.users_table.tag_configure("inactive", background="#f1f5f9")
    
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
        self.current_view = "reports"

        # Header
        header_label = ctk.CTkLabel(self.content_frame, text="Report Generation",
                                font=("Arial", 24, "bold"), text_color="#2563eb")
        header_label.pack(anchor="w", padx=30, pady=(30, 20))

        # Create tabview for different report types - ONLY TWO TABS
        self.report_tabview = ctk.CTkTabview(self.content_frame, corner_radius=15, height=600)
        self.report_tabview.pack(fill="both", expand=True, padx=30, pady=10)

        # Create only two tabs - remove User Activity
        sales_tab = self.report_tabview.add("Sales Report")
        inventory_tab = self.report_tabview.add("Inventory Report")

        # Setup each tab
        self.setup_sales_report_tab(sales_tab)
        self.setup_inventory_report_tab(inventory_tab)

    def setup_sales_report_tab(self, parent_frame):
        # Main container frame
        main_container = ctk.CTkFrame(parent_frame, fg_color="white")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Top frame for options and buttons (make visible)
        options_frame = ctk.CTkFrame(main_container, fg_color="#f8fafc", corner_radius=10)
        options_frame.pack(fill="x", padx=10, pady=10)

        # Period selection - Row 1
        period_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        period_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        period_label = ctk.CTkLabel(period_frame, text="Time Period:", font=("Arial", 14, "bold"))
        period_label.pack(side="left", padx=(0, 10))
        
        self.sales_period_var = ctk.StringVar(value="last_30_days")
        
        last_7_radio = ctk.CTkRadioButton(period_frame, text="Last 7 Days",
                                    variable=self.sales_period_var, value="last_7_days")
        last_7_radio.pack(side="left", padx=(0, 10))
        
        last_30_radio = ctk.CTkRadioButton(period_frame, text="Last 30 Days",
                                        variable=self.sales_period_var, value="last_30_days")
        last_30_radio.pack(side="left", padx=(0, 10))
        
        this_year_radio = ctk.CTkRadioButton(period_frame, text="This Year",
                                        variable=self.sales_period_var, value="this_year")
        this_year_radio.pack(side="left", padx=(0, 10))

        # Format selection - Row 2
        format_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=15, pady=5)
        
        format_label = ctk.CTkLabel(format_frame, text="Export Format:", font=("Arial", 14, "bold"))
        format_label.pack(side="left", padx=(0, 10))
        
        self.sales_format_var = ctk.StringVar(value="csv")
        
        csv_radio = ctk.CTkRadioButton(format_frame, text="CSV",
                                    variable=self.sales_format_var, value="csv")
        csv_radio.pack(side="left", padx=(0, 10))
        
        txt_radio = ctk.CTkRadioButton(format_frame, text="Text",
                                    variable=self.sales_format_var, value="txt")
        txt_radio.pack(side="left", padx=(0, 10))

        # Action buttons - Row 3
        buttons_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        generate_btn = ctk.CTkButton(buttons_frame, text="Generate Report",
                                fg_color="#10b981", hover_color="#059669",
                                font=("Arial", 14), height=35,
                                command=self.generate_sales_report)
        generate_btn.pack(side="left", padx=(0, 10))
        
        preview_graph_btn = ctk.CTkButton(buttons_frame, text="Preview Graph",
                                    fg_color="#3b82f6", hover_color="#2563eb",
                                    font=("Arial", 14), height=35,
                                    command=self.preview_sales_graph)
        preview_graph_btn.pack(side="left", padx=(0, 10))
        
        self.sales_download_btn = ctk.CTkButton(buttons_frame, text="Download Report",
                                            fg_color="#6366f1", hover_color="#4f46e5",
                                            font=("Arial", 14), height=35, state="disabled",
                                            command=self.download_sales_report)
        self.sales_download_btn.pack(side="left")

        # Preview label
        preview_label = ctk.CTkLabel(main_container, text="Text Preview",
                                font=("Arial", 18, "bold"), text_color="#2563eb")
        preview_label.pack(anchor="w", padx=15, pady=(20, 10))

        # Table preview (already working in your UI)
        table_frame = ctk.CTkFrame(main_container, fg_color="white", corner_radius=5,
                            border_width=1, border_color="#e5e7eb", height=300)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Create columns
        columns = ("order_id", "date", "customer", "status", "total")
        self.sales_preview_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Define headings
        self.sales_preview_table.heading("order_id", text="Order ID")
        self.sales_preview_table.heading("date", text="Date & Time")
        self.sales_preview_table.heading("customer", text="Customer")
        self.sales_preview_table.heading("status", text="Status")
        self.sales_preview_table.heading("total", text="Total Amount")
        
        # Define column widths
        self.sales_preview_table.column("order_id", width=80, anchor="center")
        self.sales_preview_table.column("date", width=150, anchor="center")
        self.sales_preview_table.column("customer", width=200, anchor="w")
        self.sales_preview_table.column("status", width=100, anchor="center")
        self.sales_preview_table.column("total", width=100, anchor="e")
        
        # Add scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.sales_preview_table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.sales_preview_table.xview)
        self.sales_preview_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Layout with grid
        self.sales_preview_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Summary label
        self.sales_summary_label = ctk.CTkLabel(main_container, text="No data available. Generate a report to see summary.",
                                            font=("Arial", 14), text_color="#64748b")
        self.sales_summary_label.pack(anchor="w", padx=15, pady=(0, 20))
        
        # Graph preview section
        graph_label = ctk.CTkLabel(main_container, text="Graph Preview",
                                font=("Arial", 18, "bold"), text_color="#2563eb")
        graph_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        self.graph_frame = ctk.CTkFrame(main_container, fg_color="white", corner_radius=5,
                                    border_width=1, border_color="#e5e7eb", height=250)
        self.graph_frame.pack(fill="both", expand=True, padx=15, pady=(0, 20))
        
        # Initial message in graph frame
        self.graph_message = ctk.CTkLabel(self.graph_frame, 
                                    text="Generate a report and click 'Preview Graph' to visualize data",
                                    font=("Arial", 14), text_color="gray")
        self.graph_message.pack(expand=True)

    def setup_inventory_report_tab(self, parent_frame):
        # Main container frame
        main_container = ctk.CTkFrame(parent_frame, fg_color="white")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Top frame for options and buttons (make visible)
        options_frame = ctk.CTkFrame(main_container, fg_color="#f8fafc", corner_radius=10)
        options_frame.pack(fill="x", padx=10, pady=10)

        # Report Type selection - Row 1
        type_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        type_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        type_label = ctk.CTkLabel(type_frame, text="Report Type:", font=("Arial", 14, "bold"))
        type_label.pack(side="left", padx=(0, 10))
        
        self.inventory_type_var = ctk.StringVar(value="all_products")
        
        all_radio = ctk.CTkRadioButton(type_frame, text="All Products",
                                    variable=self.inventory_type_var, value="all_products")
        all_radio.pack(side="left", padx=(0, 10))
        
        low_stock_radio = ctk.CTkRadioButton(type_frame, text="Low Stock",
                                        variable=self.inventory_type_var, value="low_stock")
        low_stock_radio.pack(side="left", padx=(0, 10))
        
        out_of_stock_radio = ctk.CTkRadioButton(type_frame, text="Out of Stock",
                                            variable=self.inventory_type_var, value="out_of_stock")
        out_of_stock_radio.pack(side="left")

        # Sort By selection - Row 2
        sort_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        sort_frame.pack(fill="x", padx=15, pady=5)
        
        sort_label = ctk.CTkLabel(sort_frame, text="Sort By:", font=("Arial", 14, "bold"))
        sort_label.pack(side="left", padx=(0, 10))
        
        self.inventory_sort_var = ctk.StringVar(value="name")
        
        name_radio = ctk.CTkRadioButton(sort_frame, text="Name",
                                    variable=self.inventory_sort_var, value="name")
        name_radio.pack(side="left", padx=(0, 10))
        
        price_radio = ctk.CTkRadioButton(sort_frame, text="Price",
                                    variable=self.inventory_sort_var, value="price")
        price_radio.pack(side="left", padx=(0, 10))
        
        stock_radio = ctk.CTkRadioButton(sort_frame, text="Stock",
                                    variable=self.inventory_sort_var, value="stock")
        stock_radio.pack(side="left")

        # Format selection - Row 3
        format_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=15, pady=5)
        
        format_label = ctk.CTkLabel(format_frame, text="Export Format:", font=("Arial", 14, "bold"))
        format_label.pack(side="left", padx=(0, 10))
        
        self.inventory_format_var = ctk.StringVar(value="csv")
        
        csv_radio = ctk.CTkRadioButton(format_frame, text="CSV",
                                    variable=self.inventory_format_var, value="csv")
        csv_radio.pack(side="left", padx=(0, 10))
        
        txt_radio = ctk.CTkRadioButton(format_frame, text="Text",
                                    variable=self.inventory_format_var, value="txt")
        txt_radio.pack(side="left", padx=(0, 10))

        # Action buttons - Row 4
        buttons_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        generate_btn = ctk.CTkButton(buttons_frame, text="Generate Report",
                                fg_color="#10b981", hover_color="#059669",
                                font=("Arial", 14), height=35,
                                command=self.generate_inventory_report)
        generate_btn.pack(side="left", padx=(0, 10))
        
        preview_graph_btn = ctk.CTkButton(buttons_frame, text="Preview Graph",
                                    fg_color="#3b82f6", hover_color="#2563eb",
                                    font=("Arial", 14), height=35,
                                    command=self.preview_inventory_graph)
        preview_graph_btn.pack(side="left", padx=(0, 10))
        
        self.inventory_download_btn = ctk.CTkButton(buttons_frame, text="Download Report",
                                            fg_color="#6366f1", hover_color="#4f46e5",
                                            font=("Arial", 14), height=35, state="disabled",
                                            command=self.download_inventory_report)
        self.inventory_download_btn.pack(side="left")

        # Preview label
        preview_label = ctk.CTkLabel(main_container, text="Text Preview",
                                font=("Arial", 18, "bold"), text_color="#2563eb")
        preview_label.pack(anchor="w", padx=15, pady=(20, 10))

        # Table preview
        table_frame = ctk.CTkFrame(main_container, fg_color="white", corner_radius=5,
                            border_width=1, border_color="#e5e7eb", height=300)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Create columns
        columns = ("product_id", "name", "price", "stock", "value")
        self.inventory_preview_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Define headings
        self.inventory_preview_table.heading("product_id", text="Product ID")
        self.inventory_preview_table.heading("name", text="Product Name")
        self.inventory_preview_table.heading("price", text="Price")
        self.inventory_preview_table.heading("stock", text="Stock")
        self.inventory_preview_table.heading("value", text="Value")
        
        # Define column widths
        self.inventory_preview_table.column("product_id", width=80, anchor="center")
        self.inventory_preview_table.column("name", width=200, anchor="w")
        self.inventory_preview_table.column("price", width=100, anchor="e")
        self.inventory_preview_table.column("stock", width=80, anchor="center")
        self.inventory_preview_table.column("value", width=100, anchor="e")
        
        # Add scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.inventory_preview_table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.inventory_preview_table.xview)
        self.inventory_preview_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Layout with grid
        self.inventory_preview_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Summary label
        self.inventory_summary_label = ctk.CTkLabel(main_container, text="No data available. Generate a report to see summary.",
                                            font=("Arial", 14), text_color="#64748b")
        self.inventory_summary_label.pack(anchor="w", padx=15, pady=(0, 20))
        
        # Graph preview section
        graph_label = ctk.CTkLabel(main_container, text="Graph Preview",
                                font=("Arial", 18, "bold"), text_color="#2563eb")
        graph_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        self.inventory_graph_frame = ctk.CTkFrame(main_container, fg_color="white", corner_radius=5,
                                            border_width=1, border_color="#e5e7eb", height=250)
        self.inventory_graph_frame.pack(fill="both", expand=True, padx=15, pady=(0, 20))
        
        # Initial message in graph frame
        self.inventory_graph_message = ctk.CTkLabel(self.inventory_graph_frame, 
                                            text="Generate a report and click 'Preview Graph' to visualize data",
                                            font=("Arial", 14), text_color="gray")
        self.inventory_graph_message.pack(expand=True)

    def preview_inventory_graph(self):
        """Preview inventory data as a graph"""
        if not self.inventory_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Clear existing graph
        for widget in self.inventory_graph_frame.winfo_children():
            widget.destroy()
        
        try:
            # Create a figure with appropriate size
            fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
            
            # Limit to top 10 products for better visualization
            products = sorted(self.inventory_data, key=lambda x: x['stock'], reverse=True)[:10]
            
            if not products:
                raise ValueError("No product data available for visualization")
            
            # Extract data
            names = []
            stocks = []
            
            for product in products:
                # Truncate long names
                name = product['name']
                if len(name) > 20:
                    name = name[:17] + "..."
                names.append(name)
                stocks.append(product['stock'])
            
            # For horizontal bar chart, reverse the order
            names.reverse()
            stocks.reverse()
            
            # Create horizontal bar chart
            bars = ax.barh(names, stocks, color='#10b981')
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.3, bar.get_y() + bar.get_height()/2,
                        f'{int(width)}', ha='left', va='center', fontsize=9)
            
            # Add labels and title
            ax.set_xlabel('Stock Quantity')
            ax.set_title('Top 10 Products by Stock Quantity')
            
            # Add grid lines
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Add a summary text
            total_stock = sum(product['stock'] for product in self.inventory_data)
            total_products = len(self.inventory_data)
            total_value = sum(float(product['price']) * product['stock'] for product in self.inventory_data)
            
            summary_text = f'Total Products: {total_products} | Total Stock: {total_stock} | Total Value: ${total_value:.2f}'
            plt.figtext(0.5, 0.01, summary_text, ha='center', fontsize=10)
            
            # Ensure tight layout
            plt.tight_layout()
            
            # Create a canvas to display the plot in the tkinter window
            canvas = FigureCanvasTkAgg(fig, self.inventory_graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            # Show error message in the graph frame
            error_label = ctk.CTkLabel(
                self.inventory_graph_frame,
                text=f"Error creating graph: {str(e)}",
                font=("Arial", 14),
                text_color="#ef4444"
            )
            error_label.pack(expand=True)
            print(f"Graph error: {e}")  # Also print to console for debugging
        



    def setup_user_activity_tab(self, parent_frame):
        # Main frame
        report_frame = ctk.CTkFrame(parent_frame, fg_color="white", corner_radius=10)
        report_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Top panel - Options
        self.user_options_panel = ctk.CTkFrame(report_frame, fg_color="white", corner_radius=10,
                                            border_width=1, border_color="#e5e7eb")
        self.user_options_panel.pack(side="top", fill="x", expand=False, padx=10, pady=(0, 10))
        
        # (keep existing options code)
        
        # Bottom panel - Buttons and Preview
        self.user_preview_panel = ctk.CTkFrame(report_frame, fg_color="#f8fafc", corner_radius=10,
                                            border_width=1, border_color="#e5e7eb")
        self.user_preview_panel.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))
        
        # (keep existing buttons code)
        
        # Tab view for switching between graph and text preview
        self.user_tabs = ctk.CTkTabview(self.user_preview_panel, corner_radius=5,
                                        fg_color="white", segmented_button_fg_color="#e5e7eb",
                                        segmented_button_selected_color="#3b82f6",
                                        segmented_button_selected_hover_color="#2563eb")
        self.user_tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.user_graph_tab = self.user_tabs.add("Graph View")
        self.user_text_tab = self.user_tabs.add("Text View")
        
        # Frame for graph display (keep existing code)
        self.user_graph_frame = ctk.CTkFrame(self.user_graph_tab, fg_color="white", corner_radius=5)
        self.user_graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message in graph frame
        self.user_graph_message = ctk.CTkLabel(self.user_graph_frame, 
                                            text="Generate a report and click 'Preview Graph' to visualize data",
                                            font=("Arial", 14), text_color="gray")
        self.user_graph_message.pack(expand=True)
        
        # Frame for table with improved styling
        table_frame = ctk.CTkFrame(self.user_text_tab, fg_color="white", corner_radius=5)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create Treeview with enhanced styling
        columns = ("user_id", "name", "email", "role", "created", "orders", "spent")
        self.user_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Define headings with meaningful labels
        self.user_table.heading("user_id", text="User ID")
        self.user_table.heading("name", text="Full Name")
        self.user_table.heading("email", text="Email Address")
        self.user_table.heading("role", text="Role")
        self.user_table.heading("created", text="Created Date")
        self.user_table.heading("orders", text="Orders")
        self.user_table.heading("spent", text="Total Spent")
        
        # Define column widths and alignment for better readability
        self.user_table.column("user_id", width=70, anchor="center")
        self.user_table.column("name", width=150, anchor="w")
        self.user_table.column("email", width=180, anchor="w")
        self.user_table.column("role", width=80, anchor="center")
        self.user_table.column("created", width=100, anchor="center")
        self.user_table.column("orders", width=70, anchor="center")
        self.user_table.column("spent", width=100, anchor="e")
        
        # Add grid lines and styling
        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=("Arial", 12))
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        
        # Add tags for different roles
        self.user_table.tag_configure("admin", background="#ede9fe")  # Light purple for admins
        self.user_table.tag_configure("user", background="#f0f9ff")   # Light blue for regular users
        
        # Add scrollbars for better navigation
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.user_table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.user_table.xview)
        self.user_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Layout the table and scrollbars
        self.user_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Summary frame below the table
        summary_frame = ctk.CTkFrame(self.user_text_tab, fg_color="white", corner_radius=5)
        summary_frame.pack(fill="x", expand=False, padx=10, pady=(10, 5))
        
        self.user_summary_label = ctk.CTkLabel(
            summary_frame, 
            text="No data loaded. Generate a report to see summary.",
            font=("Arial", 14),
            text_color="#64748b"
        )
        self.user_summary_label.pack(pady=10, padx=10, anchor="w")
        
        # Store report data
        self.user_report_data = None
        self.user_data = None

    def generate_user_report(self):
        # Clear existing data
        for item in self.user_table.get_children():
            self.user_table.delete(item)
        
        # Simulate generating report data (replace with actual data logic)
        sample_data = [
            ("2", "2025-04-23 18:51", "jashwanth vemula", "completed", "$6.00"),
            ("3", "2025-04-23 23:44", "jashwanth vemula", "completed", "$14.00")
        ]
        for row in sample_data:
            self.user_table.insert("", "end", values=row)
        
        # Store data for download
        self.user_report_data = sample_data
        self.user_download_btn.configure(state="normal")

    def download_user_report(self):
        if self.user_report_data:
            import csv
            format_type = self.user_format_var.get()
            if format_type == "csv":
                with open("user_activity_report.csv", "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Order ID", "Date", "Customer", "Status", "Total Amount"])
                    writer.writerows(self.user_report_data)
                print("Report downloaded as user_activity_report.csv")
            elif format_type == "txt":
                with open("user_activity_report.txt", "w") as f:
                    f.write("Order ID,Date,Customer,Status,Total Amount\n")
                    for row in self.user_report_data:
                        f.write(",".join(row) + "\n")
                print("Report downloaded as user_activity_report.txt")
            elif format_type == "pdf":
                
                pdf = SimpleDocTemplate("user_activity_report.pdf", pagesize=letter)
                table_data = [["Order ID", "Date", "Customer", "Status", "Total Amount"]] + list(self.user_report_data)
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                pdf.build([table])
                print("Report downloaded as user_activity_report.pdf")
        else:
            print("No report data to download")

    def toggle_custom_date_range(self):
        """Show or hide custom date range based on selection"""
        if self.sales_period_var.get() == "custom_range":
            self.custom_date_frame.pack(fill="x", padx=20, pady=(0, 10))
        else:
            self.custom_date_frame.pack_forget()
    def preview_user_graph(self):
        if not self.user_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return

        # Clear existing graph
        for widget in self.user_graph_frame.winfo_children():
            widget.destroy()

        # Get window width to adjust figure size
        window_width = self.root.winfo_width()
        fig_width = max(6, min(10, window_width / 100))  # Scale between 6-10 inches
        fig_height = fig_width * 0.75  # Maintain aspect ratio

        # Create figure for the graph
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=100)

        chart_type = self.user_chart_var.get()

        try:
            if not self.user_data or len(self.user_data) == 0:
                self.user_graph_message = ctk.CTkLabel(self.user_graph_frame,
                                                    text="No data available for visualization",
                                                    font=("Arial", 14), text_color="gray")
                self.user_graph_message.pack(expand=True)
                return

            # Prepare data for visualization
            # Limit to top 15 users for better visualization, sorted by spending
            data_to_show = self.user_data
            if len(data_to_show) > 15:
                sorted_data = sorted(data_to_show, key=lambda x: sum(float(o['total_amount']) for o in x.get('orders', [])), reverse=True)
                data_to_show = sorted_data[:15]

            names = [f"{user['first_name']} {user['last_name']}"[:15] + '...' if len(f"{user['first_name']} {user['last_name']}") > 15 else f"{user['first_name']} {user['last_name']}" for user in data_to_show]
            orders_count = [len(user.get('orders', [])) for user in data_to_show]
            total_spent = [sum(float(order['total_amount']) for order in user.get('orders', [])) for user in data_to_show]
            roles = [user['role'] for user in data_to_show]

            if chart_type == "bar":
                bars = ax.barh(names, total_spent, color='#3b82f6')
                ax.set_title('User Spending')
                ax.set_xlabel('Total Spent ($)')
                ax.set_ylabel('User')

                # Add value labels on bars
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 0.3, bar.get_y() + bar.get_height()/2,
                            f'${width:.2f}', ha='left', va='center', fontsize=8)

                plt.tight_layout()

            elif chart_type == "pie":
                # Show spending distribution by role (like sales pie chart by status)
                role_spending = {}
                for user in data_to_show:
                    role = user['role']
                    spent = sum(float(order['total_amount']) for order in user.get('orders', []))
                    if role in role_spending:
                        role_spending[role] += spent
                    else:
                        role_spending[role] = spent

                labels = list(role_spending.keys())
                values = list(role_spending.values())

                if not values or sum(values) == 0:
                    self.user_graph_message = ctk.CTkLabel(self.user_graph_frame,
                                                        text="No spending data available for visualization",
                                                        font=("Arial", 14), text_color="gray")
                    self.user_graph_message.pack(expand=True)
                    plt.close(fig)
                    return

                colors = plt.cm.tab20.colors[:len(labels)]
                wedges, texts, autotexts = ax.pie(
                    values,
                    labels=labels,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors
                )
                ax.axis('equal')
                ax.set_title('Spending Distribution by Role')
                for text in texts:
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_color('white')

            elif chart_type == "line":
                # Plot spending trend over time (like sales line chart)
                date_totals = {}
                for user in data_to_show:
                    for order in user.get('orders', []):
                        date_str = order['order_date'].strftime("%Y-%m-%d")
                        if date_str in date_totals:
                            date_totals[date_str] += float(order['total_amount'])
                        else:
                            date_totals[date_str] = float(order['total_amount'])

                if not date_totals:
                    self.user_graph_message = ctk.CTkLabel(self.user_graph_frame,
                                                        text="No order data available for visualization",
                                                        font=("Arial", 14), text_color="gray")
                    self.user_graph_message.pack(expand=True)
                    plt.close(fig)
                    return

                sorted_dates = sorted(date_totals.keys())
                totals = [date_totals[date] for date in sorted_dates]
                display_dates = [date.split('-')[1] + '/' + date.split('-')[2] for date in sorted_dates]

                ax.plot(display_dates, totals, marker='o', linestyle='-', color='#3b82f6', linewidth=2)
                ax.set_title('User Spending Trend')
                ax.set_xlabel('Date (MM/DD)')
                ax.set_ylabel('Spending Amount ($)')
                ax.grid(True, linestyle='--', alpha=0.7)

            # Add data summary
            total_users = len(self.user_data)
            total_orders = sum(len(user.get('orders', [])) for user in self.user_data)
            total_spent_all = sum(sum(float(order['total_amount']) for order in user.get('orders', [])) for user in self.user_data)
            avg_spent = total_spent_all / total_users if total_users > 0 else 0

            title_text = f'Total Users: {total_users} | Orders: {total_orders} | '
            title_text += f'Total Spent: ${total_spent_all:.2f} | Avg: ${avg_spent:.2f}'

            ax.set_title(title_text, fontsize=10, pad=15)

            plt.tight_layout()

            # Embed the graph
            canvas = FigureCanvasTkAgg(fig, master=self.user_graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            for widget in self.user_graph_frame.winfo_children():
                widget.destroy()
            error_label = ctk.CTkLabel(self.user_graph_frame, text=f"Error creating graph: {str(e)}",
                                    font=("Arial", 14), text_color="#ef4444")
            error_label.pack(expand=True)
            print(f"Graph error: {e}")

    def generate_sales_report(self):
        """Generate a simplified sales report for demo purposes"""
        try:
            # Clear the existing table
            for item in self.sales_preview_table.get_children():
                self.sales_preview_table.delete(item)
            
            # For testing, create some sample data if fetch_sales_data is not working
            if not hasattr(self, 'fetch_sales_data'):
                # Create sample data for display
                self.sales_data = [
                    {
                        'order_id': 1,
                        'order_date': datetime.datetime.now() - datetime.timedelta(days=5),
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'status': 'completed',
                        'total_amount': 125.75
                    },
                    {
                        'order_id': 2,
                        'order_date': datetime.datetime.now() - datetime.timedelta(days=3),
                        'first_name': 'Jane',
                        'last_name': 'Smith',
                        'status': 'pending',
                        'total_amount': 89.99
                    },
                    {
                        'order_id': 3,
                        'order_date': datetime.datetime.now() - datetime.timedelta(days=1),
                        'first_name': 'Robert',
                        'last_name': 'Johnson',
                        'status': 'completed',
                        'total_amount': 210.50
                    }
                ]
            else:
                # Use the period selected to fetch real data
                period = self.sales_period_var.get()
                today = datetime.datetime.now()
                
                if period == "last_7_days":
                    from_date = today - datetime.timedelta(days=7)
                elif period == "last_30_days":
                    from_date = today - datetime.timedelta(days=30)
                elif period == "this_year":
                    from_date = datetime.datetime(today.year, 1, 1)
                else:
                    from_date = today - datetime.timedelta(days=30)  # Default to 30 days
                    
                self.sales_data = self.fetch_sales_data(from_date, today)
            
            # If we still don't have data, show a message
            if not self.sales_data:
                self.sales_summary_label.configure(text="No sales data found for the selected period.")
                self.sales_download_btn.configure(state="disabled")
                return
            
            # Populate the table with data
            for order in self.sales_data:
                order_id = order['order_id']
                date = order['order_date'].strftime("%Y-%m-%d %H:%M")
                customer = f"{order['first_name']} {order['last_name']}"
                status = order['status'].capitalize()
                total = f"${float(order['total_amount']):.2f}"
                
                # Add with tag based on status for conditional formatting
                status_tag = status.lower()
                self.sales_preview_table.insert("", "end", values=(order_id, date, customer, status, total), tags=(status_tag,))
            
            # Configure tags for different statuses
            self.sales_preview_table.tag_configure("completed", background="#d1fae5")  # Green for completed
            self.sales_preview_table.tag_configure("pending", background="#fef3c7")    # Yellow for pending
            self.sales_preview_table.tag_configure("cancelled", background="#fee2e2")  # Red for cancelled
            
            # Update summary
            total_orders = len(self.sales_data)
            total_sales = sum(float(order['total_amount']) for order in self.sales_data)
            
            self.sales_summary_label.configure(
                text=f"Total Orders: {total_orders} | Total Revenue: ${total_sales:.2f}"
            )
            
            # Enable download button
            self.sales_download_btn.configure(state="normal")
            
            # Show success message
            messagebox.showinfo("Success", "Sales report has been generated successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
            print(f"Error in generate_sales_report: {e}")

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
        """Format sales data for display and download with proper tabular formatting"""
        if format_type == "csv":
            # CSV format (unchanged)
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
            # Determine column widths based on actual data
            id_width = max(10, max(len(str(order['order_id'])) for order in sales_data) + 2)
            date_width = 20  # "YYYY-MM-DD HH:MM" format
            
            # Find the max name length but cap it at 25 characters
            name_width = min(25, max(len(f"{order['first_name']} {order['last_name']}") for order in sales_data) + 2)
            
            status_width = max(10, max(len(order['status']) for order in sales_data) + 2)
            amount_width = 12  # "$XXXX.XX" format
            
            # Create the header for the table
            report = "SALES REPORT\n"
            report += "=" * (id_width + date_width + name_width + status_width + amount_width + 5) + "\n\n"
            
            # Summary
            total_sales = sum(float(order['total_amount']) for order in sales_data)
            report += f"Total Orders: {len(sales_data)}\n"
            report += f"Total Revenue: ${total_sales:.2f}\n\n"
            
            # Table header with column titles
            report += "Order ID".ljust(id_width) + "Date".ljust(date_width) + "Customer".ljust(name_width)
            report += "Status".ljust(status_width) + "Total\n"
            
            # Separator line
            report += "-" * (id_width + date_width + name_width + status_width + amount_width + 5) + "\n"
            
            # Table rows with properly aligned columns
            for order in sales_data:
                order_id = str(order['order_id'])
                date = order['order_date'].strftime("%Y-%m-%d %H:%M")
                
                customer = f"{order['first_name']} {order['last_name']}"
                if len(customer) > name_width - 2:
                    customer = customer[:name_width - 5] + "..."
                    
                status = order['status']
                total = f"${float(order['total_amount']):.2f}"
                
                # Format each row with proper spacing
                row = order_id.ljust(id_width) + date.ljust(date_width) + customer.ljust(name_width)
                row += status.ljust(status_width) + total
                report += row + "\n"
            
            return report
    def preview_sales_graph(self):
        """Preview sales data as a graph"""
        if not self.sales_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Clear existing graph
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        try:
            # Create a figure with appropriate size
            fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
            
            # Group data by date
            date_totals = {}
            for order in self.sales_data:
                date_str = order['order_date'].strftime("%Y-%m-%d")
                if date_str in date_totals:
                    date_totals[date_str] += float(order['total_amount'])
                else:
                    date_totals[date_str] = float(order['total_amount'])
            
            # Sort dates
            sorted_dates = sorted(date_totals.keys())
            if not sorted_dates:
                raise ValueError("No date data available for visualization")
                
            # Get values for each date
            values = [date_totals[date] for date in sorted_dates]
            
            # Format dates for display (MM/DD)
            display_dates = [f"{date[5:7]}/{date[8:10]}" for date in sorted_dates]
            
            # Create bar chart
            bars = ax.bar(display_dates, values, color='#3b82f6')
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'${height:.2f}', ha='center', va='bottom', fontsize=9)
            
            # Add labels and title
            ax.set_xlabel('Date (MM/DD)')
            ax.set_ylabel('Sales Amount ($)')
            ax.set_title('Daily Sales')
            
            # Add grid lines
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
            # Add a summary text
            total_sales = sum(values)
            avg_sale = total_sales / len(values) if values else 0
            summary_text = f'Total Sales: ${total_sales:.2f} | Average Daily: ${avg_sale:.2f}'
            plt.figtext(0.5, 0.01, summary_text, ha='center', fontsize=10)
            
            # Ensure tight layout
            plt.tight_layout()
            
            # Create a canvas to display the plot in the tkinter window
            canvas = FigureCanvasTkAgg(fig, self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            # Show error message in the graph frame
            error_label = ctk.CTkLabel(
                self.graph_frame,
                text=f"Error creating graph: {str(e)}",
                font=("Arial", 14),
                text_color="#ef4444"
            )
            error_label.pack(expand=True)
            print(f"Graph error: {e}")  # Also print to console for debugging

    def download_sales_report(self):
        """Download sales report to a file"""
        if not self.sales_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Determine file extension based on selected format
        ext = "csv" if self.sales_format_var.get() == "csv" else "txt"
        
        # Create reports folder if it doesn't exist
        reports_path = self.ensure_reports_folder()
        
        # Generate default filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"sales_report_{timestamp}.{ext}"
        default_path = os.path.join(reports_path, default_filename)
        
        # Ask user to confirm or change filename
        filename = filedialog.asksaveasfilename(
            initialdir=reports_path,
            initialfile=default_filename,
            defaultextension=f".{ext}",
            filetypes=[
                (f"{ext.upper()} files", f"*.{ext}"),
                ("All files", "*.*")
            ],
            title="Save Sales Report"
        )
        
        # If user cancels, return without saving
        if not filename:
            return
        
        try:
            # Format data based on selected format
            if ext == "csv":
                # CSV format
                with open(filename, 'w', newline='') as file:
                    file.write("Order ID,Date,Customer,Status,Total Amount\n")
                    
                    for order in self.sales_data:
                        order_id = str(order['order_id'])
                        date = order['order_date'].strftime("%Y-%m-%d %H:%M")
                        customer = f"{order['first_name']} {order['last_name']}"
                        status = order['status']
                        total = f"${float(order['total_amount']):.2f}"
                        
                        file.write(f"{order_id},{date},{customer},{status},{total}\n")
            else:
                # Text format with better tabular structure
                with open(filename, 'w') as file:
                    file.write("SALES REPORT\n")
                    file.write("=" * 80 + "\n\n")
                    
                    # Write summary
                    total_sales = sum(float(order['total_amount']) for order in self.sales_data)
                    file.write(f"Total Orders: {len(self.sales_data)}\n")
                    file.write(f"Total Revenue: ${total_sales:.2f}\n\n")
                    
                    # Write header
                    file.write(f"{'Order ID':<10}{'Date':<20}{'Customer':<30}{'Status':<15}{'Total':<10}\n")
                    file.write("-" * 80 + "\n")
                    
                    # Write data rows
                    for order in self.sales_data:
                        order_id = str(order['order_id'])
                        date = order['order_date'].strftime("%Y-%m-%d %H:%M")
                        customer = f"{order['first_name']} {order['last_name']}"
                        status = order['status']
                        total = f"${float(order['total_amount']):.2f}"
                        
                        file.write(f"{order_id:<10}{date:<20}{customer:<30}{status:<15}{total:<10}\n")
            
            # Show success message
            messagebox.showinfo("Success", f"Report saved to:\n{os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {str(e)}")

            
    def generate_inventory_report(self):
        """Generate a simplified inventory report for demo purposes"""
        try:
            # Clear the existing table
            for item in self.inventory_preview_table.get_children():
                self.inventory_preview_table.delete(item)
            
            # For testing, create some sample data if fetch_inventory_data is not working
            if not hasattr(self, 'fetch_inventory_data'):
                # Create sample data for display
                self.inventory_data = [
                    {
                        'product_id': 1,
                        'name': 'Organic Apples',
                        'price': 2.99,
                        'stock': 45
                    },
                    {
                        'product_id': 2,
                        'name': 'Whole Grain Bread',
                        'price': 3.49,
                        'stock': 12
                    },
                    {
                        'product_id': 3,
                        'name': 'Milk (1 Gallon)',
                        'price': 4.25,
                        'stock': 8
                    },
                    {
                        'product_id': 4,
                        'name': 'Cheddar Cheese',
                        'price': 5.99,
                        'stock': 0
                    }
                ]
            else:
                # Use the settings to fetch real data
                report_type = self.inventory_type_var.get()
                sort_by = self.inventory_sort_var.get()
                self.inventory_data = self.fetch_inventory_data(report_type, sort_by)
            
            # If we still don't have data, show a message
            if not self.inventory_data:
                self.inventory_summary_label.configure(text="No inventory data found.")
                self.inventory_download_btn.configure(state="disabled")
                return
            
            # Populate the table with data
            for product in self.inventory_data:
                product_id = product['product_id']
                name = product['name']
                price = f"${float(product['price']):.2f}"
                stock = product['stock']
                value = float(product['price']) * product['stock']
                value_str = f"${value:.2f}"
                
                # Add with tag based on stock level for conditional formatting
                if stock == 0:
                    stock_tag = "out_of_stock"
                elif stock <= 10:
                    stock_tag = "low_stock"
                else:
                    stock_tag = "in_stock"
                    
                self.inventory_preview_table.insert("", "end", 
                                                values=(product_id, name, price, stock, value_str), 
                                                tags=(stock_tag,))
            
            # Configure tags for different stock levels
            self.inventory_preview_table.tag_configure("out_of_stock", background="#fee2e2") # Red for out of stock
            self.inventory_preview_table.tag_configure("low_stock", background="#fef3c7")    # Yellow for low stock
            self.inventory_preview_table.tag_configure("in_stock", background="#d1fae5")     # Green for in stock
            
            # Update summary
            total_products = len(self.inventory_data)
            total_value = sum(float(product['price']) * product['stock'] for product in self.inventory_data)
            out_of_stock = sum(1 for product in self.inventory_data if product['stock'] == 0)
            low_stock = sum(1 for product in self.inventory_data if 0 < product['stock'] <= 10)
            
            self.inventory_summary_label.configure(
                text=f"Total Products: {total_products} | Total Value: ${total_value:.2f} | Out of Stock: {out_of_stock} | Low Stock: {low_stock}"
            )
            
            # Enable download button
            self.inventory_download_btn.configure(state="normal")
            
            # Show success message
            messagebox.showinfo("Success", "Inventory report has been generated successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
            print(f"Error in generate_inventory_report: {e}")
    def fetch_inventory_data(self, report_type, sort_by):
        """Fetch inventory data from database"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Prepare SQL based on report type and sort order
            query = "SELECT product_id, name, price, stock, image FROM Products"
            
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

    def save_product_edits(self, product_id):
        """Save product edits with validation and feedback - simplified version"""
        name = self.edit_name_entry.get().strip()
        price = self.edit_price_entry.get().strip()
        stock = self.edit_stock_var.get().strip()
        status = self.edit_status_var.get()
        notes = self.edit_notes.get("1.0", "end-1c").strip()
        
        # Validate required fields
        if not name:
            messagebox.showwarning("Input Error", "Product name is required.", parent=self.edit_product_dialog)
            self.edit_name_entry.focus_set()
            return
        
        # Validate price
        try:
            price_val = float(price)
            if price_val <= 0:
                messagebox.showwarning("Input Error", "Price must be greater than zero.", parent=self.edit_product_dialog)
                self.edit_price_entry.focus_set()
                return
        except ValueError:
            messagebox.showwarning("Input Error", "Price must be a number.", parent=self.edit_product_dialog)
            self.edit_price_entry.focus_set()
            return
        
        # Validate stock
        try:
            stock_val = int(stock)
            if stock_val < 0:
                messagebox.showwarning("Input Error", "Stock cannot be negative.", parent=self.edit_product_dialog)
                self.edit_stock_entry.focus_set()
                return
        except ValueError:
            messagebox.showwarning("Input Error", "Stock must be a whole number.", parent=self.edit_product_dialog)
            self.edit_stock_entry.focus_set()
            return
        
        # Create a simple status label to show the save is in progress
        status_label = ctk.CTkLabel(
            self.edit_product_dialog,
            text="Saving changes...",
            font=("Arial", 16, "bold"),
            fg_color="#1e293b",
            text_color="white",
            corner_radius=8,
            padx=20,
            pady=10
        )
        status_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Update the dialog to show the status
        self.edit_product_dialog.update()
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Check if another product with same name exists
            cursor.execute(
                "SELECT product_id FROM Products WHERE name = %s AND product_id != %s", 
                (name, product_id)
            )
            if cursor.fetchone():
                # Remove status indicator
                status_label.destroy()
                self.edit_product_dialog.update()
                
                messagebox.showwarning("Input Error", 
                                    f"Another product with name '{name}' already exists.", 
                                    parent=self.edit_product_dialog)
                return
            
            # Update product with all fields
            cursor.execute(
                """
                UPDATE Products 
                SET name = %s, price = %s, stock = %s, image = %s, status = %s
                WHERE product_id = %s
                """,
                (name, price_val, stock_val, self.edit_selected_image_data, status, product_id)
            )
            
            connection.commit()
            
            cursor.close()
            connection.close()
            
            # Success! Close dialog and refresh inventory
            self.edit_product_dialog.destroy()
            self.refresh_inventory_table()
            
            # Show success message
            messagebox.showinfo("Success", "Product updated successfully!")
            
        except Exception as e:
            # Remove status indicator
            status_label.destroy()
            self.edit_product_dialog.update()
            
            # Show error message
            messagebox.showerror("Database Error", str(e), parent=self.edit_product_dialog)

    def format_inventory_data(self, inventory_data, format_type):
        """Format inventory data for display and download with proper tabular formatting"""
        if format_type == "csv":
            # CSV format (unchanged)
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
            # Text format with improved tabular presentation
            # First, determine column widths based on actual data
            id_width = max(10, max(len(str(product['product_id'])) for product in inventory_data) + 2)
            name_width = max(15, max(len(product['name']) for product in inventory_data) + 2)
            price_width = 10  # "$XX.XX" format
            stock_width = max(8, max(len(str(product['stock'])) for product in inventory_data) + 2)
            value_width = 12  # "$XXXX.XX" format
            
            # Create the header for the table
            report = "INVENTORY REPORT\n"
            report += "=" * (id_width + name_width + price_width + stock_width + value_width + 5) + "\n\n"
            
            # Summary
            total_products = len(inventory_data)
            total_value = sum(float(product['price']) * product['stock'] for product in inventory_data)
            out_of_stock = sum(1 for product in inventory_data if product['stock'] == 0)
            low_stock = sum(1 for product in inventory_data if 0 < product['stock'] <= 10)
            
            report += f"Total Products: {total_products}\n"
            report += f"Total Inventory Value: ${total_value:.2f}\n"
            report += f"Out of Stock Items: {out_of_stock}\n"
            report += f"Low Stock Items: {low_stock}\n\n"
            
            # Table header with column titles
            report += "Product ID".ljust(id_width) + "Name".ljust(name_width) + "Price".ljust(price_width)
            report += "Stock".ljust(stock_width) + "Value\n"
            
            # Separator line
            report += "-" * (id_width + name_width + price_width + stock_width + value_width + 5) + "\n"
            
            # Table rows with properly aligned columns
            for product in inventory_data:
                product_id = str(product['product_id'])
                name = product['name']
                # Truncate long names but keep at least 15 characters
                if len(name) > name_width - 2:
                    name = name[:name_width - 5] + "..."
                    
                price = float(product['price'])
                price_str = f"${price:.2f}"
                
                stock = str(product['stock'])
                value = price * int(stock)
                value_str = f"${value:.2f}"
                
                # Format each row with proper spacing
                row = product_id.ljust(id_width) + name.ljust(name_width) + price_str.ljust(price_width)
                row += stock.ljust(stock_width) + value_str
                report += row + "\n"
            
            return report

    def download_inventory_report(self):
        """Download inventory report to a file"""
        if not self.inventory_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Determine file extension based on selected format
        ext = "csv" if self.inventory_format_var.get() == "csv" else "txt"
        
        # Create reports folder if it doesn't exist
        reports_path = self.ensure_reports_folder()
        
        # Generate default filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"inventory_report_{timestamp}.{ext}"
        default_path = os.path.join(reports_path, default_filename)
        
        # Ask user to confirm or change filename
        filename = filedialog.asksaveasfilename(
            initialdir=reports_path,
            initialfile=default_filename,
            defaultextension=f".{ext}",
            filetypes=[
                (f"{ext.upper()} files", f"*.{ext}"),
                ("All files", "*.*")
            ],
            title="Save Inventory Report"
        )
        
        # If user cancels, return without saving
        if not filename:
            return
        
        try:
            # Format data based on selected format
            if ext == "csv":
                # CSV format
                with open(filename, 'w', newline='') as file:
                    file.write("Product ID,Name,Price,Stock,Value\n")
                    
                    for product in self.inventory_data:
                        product_id = str(product['product_id'])
                        name = product['name'].replace(',', ' ')  # Remove commas to avoid CSV issues
                        price = f"${float(product['price']):.2f}"
                        stock = str(product['stock'])
                        value = f"${float(product['price']) * product['stock']:.2f}"
                        
                        file.write(f"{product_id},{name},{price},{stock},{value}\n")
            else:
                # Text format with better tabular structure
                with open(filename, 'w') as file:
                    file.write("INVENTORY REPORT\n")
                    file.write("=" * 80 + "\n\n")
                    
                    # Write summary
                    total_products = len(self.inventory_data)
                    total_value = sum(float(product['price']) * product['stock'] for product in self.inventory_data)
                    out_of_stock = sum(1 for product in self.inventory_data if product['stock'] == 0)
                    low_stock = sum(1 for product in self.inventory_data if 0 < product['stock'] <= 10)
                    
                    file.write(f"Total Products: {total_products}\n")
                    file.write(f"Total Inventory Value: ${total_value:.2f}\n")
                    file.write(f"Out of Stock Items: {out_of_stock}\n")
                    file.write(f"Low Stock Items: {low_stock}\n\n")
                    
                    # Write header
                    file.write(f"{'ID':<8}{'Name':<30}{'Price':<10}{'Stock':<8}{'Value':<12}\n")
                    file.write("-" * 80 + "\n")
                    
                    # Write data rows
                    for product in self.inventory_data:
                        product_id = str(product['product_id'])
                        name = product['name']
                        if len(name) > 27:
                            name = name[:24] + "..."
                        price = f"${float(product['price']):.2f}"
                        stock = str(product['stock'])
                        value = f"${float(product['price']) * product['stock']:.2f}"
                        
                        file.write(f"{product_id:<8}{name:<30}{price:<10}{stock:<8}{value:<12}\n")
            
            # Show success message
            messagebox.showinfo("Success", f"Report saved to:\n{os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {str(e)}")

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
        self.user_data = self.fetch_user_data(user_type, activity_type, from_date)
        
        if not self.user_data:
            # Clear the table
            for item in self.user_table.get_children():
                self.user_table.delete(item)
                
            self.user_summary_label.configure(text="No user data found for the selected criteria.")
            self.user_download_btn.configure(state="disabled")
            self.preview_user_graph_btn.configure(state="disabled")
            
            # Clear any existing graph
            for widget in self.user_graph_frame.winfo_children():
                widget.destroy()
            self.user_graph_message = ctk.CTkLabel(self.user_graph_frame, text="No data available for visualization",
                                                font=("Arial", 14), text_color="gray")
            self.user_graph_message.pack(expand=True)
            return
        
        # Format data for preview and download
        self.user_report_data = self.format_user_data(self.user_data, report_format)
        
        # Update the table view
        for item in self.user_table.get_children():
            self.user_table.delete(item)
            
        # Add user data to the table with proper formatting
        for user in self.user_data:
            user_id = user['user_id']
            name = f"{user['first_name']} {user['last_name']}"
            email = user.get("email", user["username"]) or ""
            role = user["role"].capitalize()
            created = user["created_at"].strftime("%Y-%m-%d") if user["created_at"] else "N/A"
            
            # Calculate orders stats
            orders_count = len(user.get("orders", []))
            total_spent = sum(float(order["total_amount"]) for order in user.get("orders", []))
            spent_str = f"${total_spent:.2f}"
            
            # Insert with tag based on role for conditional formatting
            self.user_table.insert("", "end", 
                                values=(user_id, name, email, role, created, orders_count, spent_str),
                                tags=(role.lower(),))
        
        # Update summary
        total_users = len(self.user_data)
        admin_count = sum(1 for user in self.user_data if user["role"] == "admin")
        customer_count = sum(1 for user in self.user_data if user["role"] == "user")
        total_orders = sum(len(user.get("orders", [])) for user in self.user_data)
        total_spent = sum(sum(float(order["total_amount"]) for order in user.get("orders", [])) for user in self.user_data)
        
        summary_text = f"Total Users: {total_users} | "
        summary_text += f"Admins: {admin_count} | Regular Users: {customer_count} | "
        summary_text += f"Total Orders: {total_orders} | Total Spent: ${total_spent:.2f}"
        
        self.user_summary_label.configure(text=summary_text)
        
        # Enable download and preview buttons
        self.user_download_btn.configure(state="normal")
        self.preview_user_graph_btn.configure(state="normal")
        
        # Show success message
        messagebox.showinfo("Report Generated", "User activity report has been generated successfully. You can now preview the graph or download the report.")

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
        """Format user data for display and download with proper tabular formatting"""
        if format_type == "csv":
            # CSV format (unchanged)
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
            # Determine column widths based on actual data
            id_width = max(8, max(len(str(user['user_id'])) for user in user_data) + 2)
            
            # Find max lengths but cap them
            name_width = min(25, max(len(f"{user['first_name']} {user['last_name']}") for user in user_data) + 2)
            
            email_width = min(30, max(len(user.get("email", user["username"] or "")) for user in user_data) + 2)
            role_width = max(8, max(len(user["role"]) for user in user_data) + 2)
            
            created_width = 12  # "YYYY-MM-DD" format
            orders_width = 10
            spent_width = 15  # "$XXXX.XX" format
            
            # Create the header for the table
            report = "USER ACTIVITY REPORT\n"
            separator_length = id_width + name_width + email_width + role_width + created_width + orders_width + spent_width + 7
            report += "=" * separator_length + "\n\n"
            
            # Summary
            total_users = len(user_data)
            admin_count = sum(1 for user in user_data if user["role"] == "admin")
            customer_count = sum(1 for user in user_data if user["role"] == "user")
            
            report += f"Total Users: {total_users}\n"
            report += f"Administrators: {admin_count}\n"
            report += f"Regular Users: {customer_count}\n\n"
            
            # Table header with column titles
            report += "User ID".ljust(id_width) + "Name".ljust(name_width) + "Email".ljust(email_width)
            report += "Role".ljust(role_width) + "Created".ljust(created_width)
            report += "Orders".ljust(orders_width) + "Total Spent\n"
            
            # Separator line
            report += "-" * separator_length + "\n"
            
            # Table rows with properly aligned columns
            for user in user_data:
                user_id = str(user['user_id'])
                
                name = f"{user['first_name']} {user['last_name']}"
                if len(name) > name_width - 2:
                    name = name[:name_width - 5] + "..."
                
                email = user.get("email", user["username"] or "")
                if len(email) > email_width - 2:
                    email = email[:email_width - 5] + "..."
                    
                role = user["role"]
                created = user["created_at"].strftime("%Y-%m-%d") if user["created_at"] else "N/A"
                
                # Order information
                orders_count = str(len(user.get("orders", [])))
                total_spent = sum(float(order["total_amount"]) for order in user.get("orders", []))
                spent_str = f"${total_spent:.2f}"
                
                # Format each row with proper spacing
                row = user_id.ljust(id_width) + name.ljust(name_width) + email.ljust(email_width)
                row += role.ljust(role_width) + created.ljust(created_width)
                row += orders_count.ljust(orders_width) + spent_str
                report += row + "\n"
            
            return report

    def download_user_report(self):
        """Download user report to file in reports folder"""
        if not self.user_report_data:
            messagebox.showwarning("No Data", "Please generate a report first.")
            return
        
        # Determine file extension
        ext = "csv" if self.user_format_var.get() == "csv" else "txt"
        
        # Create reports folder
        reports_path = self.ensure_reports_folder()
        
        # Generate default filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"user_report_{timestamp}.{ext}"
        default_path = os.path.join(reports_path, default_filename)
        
        # Ask user to confirm or change filename
        filename = filedialog.asksaveasfilename(
            initialdir=reports_path,
            initialfile=default_filename,
            defaultextension=f".{ext}",
            filetypes=[
                (f"{ext.upper()} files", f"*.{ext}"),
                ("All files", "*.*")
            ],
            title="Save User Report"
        )
        
        # If user cancels, use default path
        if not filename:
            filename = default_path
        
        # Save the file
        try:
            with open(filename, 'w', newline='') as file:
                file.write(self.user_report_data)
            
            messagebox.showinfo("Success", f"Report saved to {os.path.basename(filename)}")
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
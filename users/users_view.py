import sys
import os
# Add parent directory to path so we can import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
import subprocess
import datetime

from users.users_nav import UserNavigation
from config_db import connect_db
from utils_file import read_login_file, write_login_file

class UserApp:
    def __init__(self, root, username=None):
        self.root = root
        self.username = username
        self.root.title("SuperMarket Dashboard")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        
        # Current user info
        self.current_user = {
            "user_id": None,
            "username": None,
            "first_name": None,
            "last_name": None,
            "role": None
        }
        
        # Global dictionaries to track cart items and their UI elements
        self.cart_items = {}
        self.cart_item_frames = {}
        self.total_amount = 0
        
        # If username is provided, try to authenticate
        if username:
            if not self.get_user_info(username):
                messagebox.showerror("Authentication Error", "User not found. Please login again.")
                self.root.destroy()
                subprocess.run(["python", os.path.join(os.path.dirname(os.path.dirname(__file__)), "login_signup.py")])
                return
        else:
            # Try to read from file
            username_from_file, _ = read_login_file()
            if username_from_file:
                if not self.get_user_info(username_from_file):
                    messagebox.showerror("Authentication Error", "User not found. Please login again.")
                    self.root.destroy()
                    subprocess.run(["python", os.path.join(os.path.dirname(os.path.dirname(__file__)), "login_signup.py")])
                    return
            else:
                messagebox.showerror("Authentication Error", "User not found. Please login again.")
                self.root.destroy()
                subprocess.run(["python", os.path.join(os.path.dirname(os.path.dirname(__file__)), "login_signup.py")])
                return
        
        # Setup UI
        self.setup_main_ui()
        
        # Show home view by default
        self.show_home_view()
    
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
                
                # Save user info to file for other scripts to use
                write_login_file(user["username"], user["role"])
                
                return True
            
            return False
        except Exception as err:
            print(f"Database Error in get_user_info: {err}")
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def setup_main_ui(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#f3f4f6", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)
        
        # Add navigation sidebar
        self.nav = UserNavigationExtended(self.main_frame, self)
        
        # User info in sidebar
        if self.current_user["first_name"]:
            user_info = f"{self.current_user['first_name']} {self.current_user['last_name']}"
            user_label = ctk.CTkLabel(self.nav.sidebar, text=f"Welcome, {user_info}", 
                                    font=("Arial", 14), text_color="white")
            user_label.pack(pady=(0, 20))
        
        # Content area - Make the content scrollable
        self.content_scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="white", corner_radius=15)
        self.content_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.header_label = ctk.CTkLabel(self.content_scroll, text="Welcome to the SuperMarket",
                                  font=("Arial", 24, "bold"), text_color="black")
        self.header_label.pack(anchor="w", padx=30, pady=(10, 20))
        
        # Create the different sections
        self.create_sections()
    
    def create_sections(self):
        # Available Items Section
        self.items_section = ctk.CTkFrame(self.content_scroll, fg_color="white")
        
        # Checkout Section
        self.checkout_section = ctk.CTkFrame(self.content_scroll, fg_color="white")
        
        # Previous Orders Section
        self.orders_section = ctk.CTkFrame(self.content_scroll, fg_color="white")
        
        # Set up each section content
        self.setup_items_section()
        self.setup_checkout_section()
        self.setup_orders_section()
    
    def setup_items_section(self):
        items_label = ctk.CTkLabel(self.items_section, text="Available Items", 
                                  font=("Arial", 18, "bold"), text_color="black")
        items_label.pack(anchor="w", pady=(0, 20))
        
        # Search bar with clear functionality
        search_frame = ctk.CTkFrame(self.items_section, fg_color="white")
        search_frame.pack(fill="x", pady=(0, 10))
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search products...", 
                                   font=("Arial", 14), height=40, width=300)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        search_button = ctk.CTkButton(search_frame, text="Search", 
                                     fg_color="#2563eb", hover_color="#1d4ed8", 
                                     font=("Arial", 14), height=40, width=100,
                                     command=self.handle_search)
        search_button.pack(side="left", padx=(0, 10))
        
        # Clear search button
        self.clear_search_button = ctk.CTkButton(search_frame, text="Clear", 
                                         fg_color="#ef4444", hover_color="#dc2626", 
                                         font=("Arial", 14), height=40, width=100,
                                         command=self.clear_search)
        self.clear_search_button.pack(side="left")
        # Initially hide the clear button
        self.clear_search_button.pack_forget()
        
        # Products container with scrolling
        self.products_container = ctk.CTkFrame(self.items_section, fg_color="#f3f4f6", corner_radius=15)
        self.products_container.pack(fill="x", pady=10)
        
        # Grid layout for products with scrolling
        self.products_frame = ctk.CTkFrame(self.products_container, fg_color="#f3f4f6")
        self.products_frame.pack(fill="x", padx=20, pady=20)
    
    def setup_checkout_section(self):
        checkout_label = ctk.CTkLabel(self.checkout_section, text="Checkout", 
                                     font=("Arial", 18, "bold"), text_color="black")
        checkout_label.pack(anchor="w", pady=(10, 15))
        
        # Create a frame to hold cart items
        self.cart_container = ctk.CTkFrame(self.checkout_section, fg_color="#f3f4f6", corner_radius=10)
        self.cart_container.pack(fill="x", pady=(0, 10))
        
        # Label when cart is empty
        self.empty_cart_label = ctk.CTkLabel(self.cart_container, text="Your cart is empty", 
                                          font=("Arial", 14), text_color="gray")
        self.empty_cart_label.pack(pady=20)
        
        # Cart total label
        self.total_label = ctk.CTkLabel(self.checkout_section, text="Total: $0.00", 
                                 font=("Arial", 16, "bold"), text_color="black")
        self.total_label.pack(anchor="e", padx=20, pady=(0, 10))
        
        # Checkout button
        self.checkout_btn = ctk.CTkButton(self.checkout_section, text="Proceed to Checkout", 
                                    fg_color="#16a34a", hover_color="#15803d", 
                                    font=("Arial", 14), height=35, width=200,
                                    state="disabled", command=self.proceed_to_checkout)
        self.checkout_btn.pack(anchor="w", pady=(0, 10))
    
    def setup_orders_section(self):
        orders_label = ctk.CTkLabel(self.orders_section, text="Previous Orders", 
                                   font=("Arial", 18, "bold"), text_color="black")
        orders_label.pack(anchor="w", pady=(10, 15))
        
        # Orders container
        self.orders_container = ctk.CTkFrame(self.orders_section, fg_color="#f3f4f6", corner_radius=15)
        self.orders_container.pack(fill="x", pady=5)
    
    def show_home_view(self):
        # Hide all sections first
        self.items_section.pack_forget()
        self.checkout_section.pack_forget()
        self.orders_section.pack_forget()
        
        # Show home sections
        self.items_section.pack(fill="x", padx=30, pady=10)
        self.checkout_section.pack(fill="x", padx=30, pady=10)
        self.orders_section.pack(fill="x", padx=30, pady=(10, 30))
        
        # Update header
        self.header_label.configure(text="Welcome to the SuperMarket")
        
        # Refresh data
        self.refresh_products_display()
        self.fetch_user_cart()
        self.refresh_previous_orders()
        
        # Reset search
        self.search_entry.delete(0, ctk.END)
        self.clear_search_button.pack_forget()
    
    def show_cart_view(self):
        # Hide all sections first
        self.items_section.pack_forget()
        self.orders_section.pack_forget()
        
        # Show cart section only
        self.checkout_section.pack(fill="x", padx=30, pady=10)
        
        # Update header
        self.header_label.configure(text="Your Shopping Cart")
        
        # Refresh cart
        self.fetch_user_cart()
    
    def show_orders_view(self):
        # Hide all sections first
        self.items_section.pack_forget()
        self.checkout_section.pack_forget()
        
        # Show orders section only
        self.orders_section.pack(fill="x", padx=30, pady=10)
        
        # Update header
        self.header_label.configure(text="Your Previous Orders")
        
        # Refresh orders
        self.refresh_previous_orders()
    
    def clear_search(self):
        self.search_entry.delete(0, ctk.END)
        self.refresh_products_display()
        self.clear_search_button.pack_forget()
    
    def refresh_products_display(self, search_query=None):
        # Clear existing products
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        
        # Get products (filtered if search query provided)
        if search_query:
            products = self.search_products(search_query)
            # Show clear button when search is active
            self.clear_search_button.pack(side="left")
        else:
            products = self.fetch_products()
            # Hide clear button when no search is active
            self.clear_search_button.pack_forget()
        
        # If no products found, display message
        if not products:
            no_products_label = ctk.CTkLabel(self.products_frame, text="No products available", 
                                          font=("Arial", 16), text_color="gray")
            no_products_label.pack(pady=30)
        else:
            # Create a frame for grid layout
            grid_frame = ctk.CTkFrame(self.products_frame, fg_color="#f3f4f6")
            grid_frame.pack(fill="both", expand=True)
            
            # Calculate how many products per row based on window width
            # We'll use 3 products per row as default
            products_per_row = 3
            
            # Layout products in a grid
            for i, product in enumerate(products):
                row = i // products_per_row
                col = i % products_per_row
                
                # Create a white card with shadow effect
                item_card = ctk.CTkFrame(grid_frame, fg_color="white", corner_radius=10)
                item_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                
                # Add some padding inside the card
                inner_card = ctk.CTkFrame(item_card, fg_color="white", corner_radius=10)
                inner_card.pack(padx=20, pady=20, fill="both", expand=True)
                
                # Try to load image
                try:
                    if product["image"] and os.path.exists(product["image"]):
                        img = ctk.CTkImage(light_image=Image.open(product["image"]), size=(150, 150))
                        img_label = ctk.CTkLabel(inner_card, image=img, text="")
                        img_label.pack(pady=10)
                    else:
                        # Use emoji based on product name
                        emoji = "🍎"  # default
                        if "apple" in product["name"].lower():
                            emoji = "🍎"
                        elif "banana" in product["name"].lower():
                            emoji = "🍌"
                        elif "broccoli" in product["name"].lower():
                            emoji = "🥦"
                        
                        ctk.CTkLabel(inner_card, text=emoji, font=("Arial", 72)).pack(pady=10)
                except Exception as e:
                    print(f"Error loading image for {product['name']}: {e}")
                    ctk.CTkLabel(inner_card, text="🍎", font=("Arial", 72)).pack(pady=10)
                
                # Product details
                ctk.CTkLabel(inner_card, text=product["name"], 
                           font=("Arial", 16, "bold"), text_color="black").pack(pady=(5, 0))
                
                ctk.CTkLabel(inner_card, text=product["price"], 
                           font=("Arial", 16), text_color="black").pack(pady=(0, 10))
                
                # Quantity selector frame
                quantity_frame = ctk.CTkFrame(inner_card, fg_color="white")
                quantity_frame.pack(pady=(0, 10))
                
                # Decrease quantity button
                decrease_btn = ctk.CTkButton(
                    quantity_frame, text="-", width=30, height=30,
                    fg_color="#d1d5db", hover_color="#9ca3af", text_color="black",
                    command=lambda qv=f"quantity_{product['id']}": self.decrease_quantity(qv)
                )
                decrease_btn.pack(side="left", padx=(0, 5))
                
                # Quantity variable and display
                quantity_var = ctk.StringVar(value="1")
                quantity_label = ctk.CTkLabel(
                    quantity_frame, textvariable=quantity_var,
                    width=30, font=("Arial", 14, "bold")
                )
                quantity_label.pack(side="left", padx=5)
                
                # Set a tag to identify this quantity variable
                quantity_var_id = f"quantity_{product['id']}"
                setattr(self, quantity_var_id, quantity_var)
                
                # Increase quantity button
                increase_btn = ctk.CTkButton(
                    quantity_frame, text="+", width=30, height=30,
                    fg_color="#d1d5db", hover_color="#9ca3af", text_color="black",
                    command=lambda qv=quantity_var_id: self.increase_quantity(qv)
                )
                increase_btn.pack(side="left", padx=(5, 0))
                
                # Add to Cart button
                add_cart_btn = ctk.CTkButton(
                    inner_card, text="Add to Cart", 
                    fg_color="#2563eb", hover_color="#1d4ed8", 
                    font=("Arial", 14), height=35,
                    command=lambda id=product["id"], name=product["name"], 
                                  price=product["price"], raw_price=product["raw_price"],
                                  qv=quantity_var_id: 
                           self.add_to_cart(id, name, price, raw_price, qv)
                )
                add_cart_btn.pack(pady=5)
            
            # Configure grid column weights to make them equal width
            for i in range(products_per_row):
                grid_frame.columnconfigure(i, weight=1)
    
    def increase_quantity(self, quantity_var_id):
        var = getattr(self, quantity_var_id)
        current_val = int(var.get())
        var.set(str(current_val + 1))
    
    def decrease_quantity(self, quantity_var_id):
        var = getattr(self, quantity_var_id)
        current_val = int(var.get())
        if current_val > 1:
            var.set(str(current_val - 1))
    
    def fetch_products(self):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT product_id, name, price, image_path, stock FROM Products WHERE stock > 0")
            products_db = cursor.fetchall()
            
            # Format products for display
            products = []
            for product in products_db:
                price_formatted = f"${float(product['price']):.2f}"
                products.append({
                    "id": product["product_id"],
                    "name": product["name"],
                    "price": price_formatted,
                    "raw_price": float(product["price"]),
                    "image": product["image_path"] if product["image_path"] else None,
                    "stock": product["stock"]
                })
            
            return products
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def search_products(self, search_query):
        """Search products by name"""
        if not search_query:
            return self.fetch_products()
        
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Use LIKE for partial matching
            cursor.execute(
                "SELECT product_id, name, price, image_path, stock FROM Products WHERE stock > 0 AND name LIKE %s",
                (f"%{search_query}%",)
            )
            products_db = cursor.fetchall()
            
            # Format products for display
            products = []
            for product in products_db:
                price_formatted = f"${float(product['price']):.2f}"
                products.append({
                    "id": product["product_id"],
                    "name": product["name"],
                    "price": price_formatted,
                    "raw_price": float(product["price"]),
                    "image": product["image_path"] if product["image_path"] else None,
                    "stock": product["stock"]
                })
            
            return products
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def handle_search(self):
        search_query = self.search_entry.get().strip()
        self.refresh_products_display(search_query)
    
    def fetch_user_cart(self):
        if not self.current_user["user_id"]:
            return
        
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Check if user has an active cart
            cursor.execute(
                "SELECT cart_id FROM Carts WHERE user_id = %s AND status = 'active'",
                (self.current_user["user_id"],)
            )
            
            cart = cursor.fetchone()
            
            if cart:
                # Fetch cart items
                cursor.execute(
                    """
                    SELECT ci.cart_item_id, p.product_id, p.name, p.price, ci.quantity 
                    FROM CartItems ci
                    JOIN Products p ON ci.product_id = p.product_id
                    WHERE ci.cart_id = %s
                    """,
                    (cart["cart_id"],)
                )
                
                cart_items_db = cursor.fetchall()
                
                # Clear existing cart display
                self.empty_cart_label.pack_forget()
                for frame_info in self.cart_item_frames.values():
                    frame_info["frame"].destroy()
                
                self.cart_items.clear()
                self.cart_item_frames.clear()
                
                # If no items, show empty cart message
                if not cart_items_db:
                    self.empty_cart_label.pack(pady=20)
                    self.update_cart_total()
                    return
                
                # Add items to cart
                for item in cart_items_db:
                    price_str = f"${float(item['price']):.2f}"
                    self.cart_items[item["name"]] = {
                        "name": item["name"],
                        "price": price_str,
                        "raw_price": float(item["price"]),
                        "quantity": item["quantity"],
                        "product_id": item["product_id"],
                        "cart_item_id": item["cart_item_id"]
                    }
                    
                    # Create visual representation
                    self.create_cart_item_display(item["name"], price_str, item["quantity"], item["product_id"])
                
                self.update_cart_total()
            else:
                # No active cart, show empty cart
                self.empty_cart_label.pack(pady=20)
                self.update_cart_total()
            
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_active_cart_id(self):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Check if user has an active cart
            cursor.execute(
                "SELECT cart_id FROM Carts WHERE user_id = %s AND status = 'active'",
                (self.current_user["user_id"],)
            )
            
            cart = cursor.fetchone()
            
            if cart:
                return cart["cart_id"]
            else:
                # Create a new cart
                cursor.execute(
                    "INSERT INTO Carts (user_id, created_at, status) VALUES (%s, %s, %s)",
                    (self.current_user["user_id"], datetime.datetime.now(), "active")
                )
                
                connection.commit()
                
                # Get the new cart ID
                cursor.execute(
                    "SELECT LAST_INSERT_ID() as cart_id"
                )
                
                new_cart = cursor.fetchone()
                return new_cart["cart_id"]
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def add_to_cart(self, product_id, product_name, product_price, raw_price, quantity_var_id):
        # Get the quantity from the quantity variable
        quantity_var = getattr(self, quantity_var_id)
        quantity = int(quantity_var.get())
        
        # Hide the empty cart message if it's the first item
        if not self.cart_items:
            self.empty_cart_label.pack_forget()
        
        # Database operations
        if self.current_user["user_id"]:
            try:
                connection = connect_db()
                cursor = connection.cursor(dictionary=True)
                
                # Get or create active cart
                cart_id = self.get_active_cart_id()
                
                if not cart_id:
                    messagebox.showerror("Error", "Could not create a cart. Please try again.")
                    return
                
                # Check if item already exists in cart
                cursor.execute(
                    "SELECT cart_item_id, quantity FROM CartItems WHERE cart_id = %s AND product_id = %s",
                    (cart_id, product_id)
                )
                
                existing_item = cursor.fetchone()
                
                if existing_item:
                    # Update quantity
                    new_quantity = existing_item["quantity"] + quantity
                    cursor.execute(
                        "UPDATE CartItems SET quantity = %s WHERE cart_item_id = %s",
                        (new_quantity, existing_item["cart_item_id"])
                    )
                    
                    # Also update in our local cart
                    if product_name in self.cart_items:
                        self.cart_items[product_name]["quantity"] = new_quantity
                        self.cart_items[product_name]["cart_item_id"] = existing_item["cart_item_id"]
                        quantity_label = self.cart_item_frames[product_name]["quantity_label"]
                        quantity_label.configure(text=f"Qty: {new_quantity}")
                    else:
                        # This would be an unusual state, let's fetch the cart again to sync
                        self.fetch_user_cart()
                else:
                    # Check product stock before adding
                    cursor.execute(
                        "SELECT stock FROM Products WHERE product_id = %s",
                        (product_id,)
                    )
                    
                    product = cursor.fetchone()
                    if not product or product["stock"] < quantity:
                        available = product["stock"] if product else 0
                        messagebox.showwarning("Stock Limit", 
                                               f"Cannot add {quantity} of {product_name}. Only {available} available.")
                        return
                    
                    # Add new item to cart
                    cursor.execute(
                        "INSERT INTO CartItems (cart_id, product_id, quantity) VALUES (%s, %s, %s)",
                        (cart_id, product_id, quantity)
                    )
                    
                    # Get the inserted item's ID
                    cursor.execute(
                        "SELECT LAST_INSERT_ID() as cart_item_id"
                    )
                    
                    result = cursor.fetchone()
                    cart_item_id = result["cart_item_id"]
                    
                    # Add to local cart
                    self.cart_items[product_name] = {
                        "name": product_name,
                        "price": product_price,
                        "raw_price": raw_price,
                        "quantity": quantity,
                        "product_id": product_id,
                        "cart_item_id": cart_item_id
                    }
                    
                    # Create UI element
                    self.create_cart_item_display(product_name, product_price, quantity, product_id)
                
                # Commit changes
                connection.commit()
                
            except Exception as err:
                messagebox.showerror("Database Error", str(err))
                return
            finally:
                if connection and connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            # No user logged in, display warning
            messagebox.showwarning("Login Required", "Please log in to add items to your cart.")
            return
        
        # Reset quantity selector to 1
        quantity_var.set("1")
        
        # Update total
        self.update_cart_total()
        
        # Confirmation message
        messagebox.showinfo("Added to Cart", f"{quantity} x {product_name} has been added to your cart!")
    
    def update_cart_item_quantity(self, product_name, product_id, new_quantity):
        if new_quantity <= 0:
            # If quantity is 0 or negative, remove the item
            self.remove_from_cart(product_name)
            return
        
        # Update in database
        if self.current_user["user_id"] and product_name in self.cart_items:
            try:
                connection = connect_db()
                cursor = connection.cursor()
                
                # Check available stock
                cursor.execute(
                    "SELECT stock FROM Products WHERE product_id = %s",
                    (product_id,)
                )
                product = cursor.fetchone()
                
                if not product or product[0] < new_quantity:
                    available = product[0] if product else 0
                    messagebox.showwarning("Stock Limit", 
                                          f"Cannot update to {new_quantity}. Only {available} available.")
                    return False
                
                # Get cart_item_id
                cart_item_id = self.cart_items[product_name].get("cart_item_id")
                
                if cart_item_id:
                    cursor.execute(
                        "UPDATE CartItems SET quantity = %s WHERE cart_item_id = %s",
                        (new_quantity, cart_item_id)
                    )
                    connection.commit()
                    
                    # Update local cart item
                    self.cart_items[product_name]["quantity"] = new_quantity
                    
                    # Update UI
                    if product_name in self.cart_item_frames:
                        self.cart_item_frames[product_name]["quantity_label"].configure(
                            text=f"Qty: {new_quantity}"
                        )
                    
                    # Update total
                    self.update_cart_total()
                    
                return True
            except Exception as err:
                messagebox.showerror("Database Error", str(err))
                return False
            finally:
                if connection and connection.is_connected():
                    cursor.close()
                    connection.close()
                    
        return False

    
    def proceed_to_checkout(self):
        if not self.current_user["user_id"]:
            messagebox.showwarning("Login Required", "Please login to checkout.")
            return
        
        if not self.cart_items:
            messagebox.showinfo("Empty Cart", "Your cart is empty.")
            return
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Get the active cart
            cart_id = self.get_active_cart_id()
            
            if not cart_id:
                messagebox.showerror("Error", "Could not find your cart. Please try again.")
                return
            
            # Calculate total amount directly from the database
            cursor.execute(
                """
                SELECT SUM(p.price * ci.quantity) as total
                FROM CartItems ci
                JOIN Products p ON ci.product_id = p.product_id
                WHERE ci.cart_id = %s
                """,
                (cart_id,)
            )
            result = cursor.fetchone()
            total_amount = result[0] if result[0] else 0
            
            # Update cart status to 'completed'
            cursor.execute(
                "UPDATE Carts SET status = 'completed' WHERE cart_id = %s",
                (cart_id,)
            )
            
            # Create an order - ensure cart_id is properly stored
            cursor.execute(
                """
                INSERT INTO Orders (user_id, cart_id, order_date, total_amount, status) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                (self.current_user["user_id"], cart_id, datetime.datetime.now(), total_amount, "completed")
            )
            
            # Get the order ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            order_id = cursor.fetchone()[0]
            
            # Update product inventory (reduce stock)
            cursor.execute(
                """
                UPDATE Products p
                JOIN CartItems ci ON p.product_id = ci.product_id
                SET p.stock = p.stock - ci.quantity
                WHERE ci.cart_id = %s
                """,
                (cart_id,)
            )
            
            connection.commit()
            
            messagebox.showinfo("Success", f"Your order #{order_id} has been placed successfully!")
            
            # Clear cart display
            self.empty_cart_label.pack(pady=20)
            for frame_info in self.cart_item_frames.values():
                frame_info["frame"].destroy()
            
            self.cart_items.clear()
            self.cart_item_frames.clear()
            self.update_cart_total()
            
            # Refresh orders display
            self.refresh_previous_orders()
            
        except Exception as err:
            print(f"Error completing purchase: {err}")
            messagebox.showerror("Database Error", str(err))
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def fetch_previous_orders(self):
        if not self.current_user["user_id"]:
            return []
        
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT order_id, order_date, total_amount, status
                FROM Orders
                WHERE user_id = %s
                ORDER BY order_date DESC
                LIMIT 5
                """,
                (self.current_user["user_id"],)
            )
            
            return cursor.fetchall()
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def refresh_previous_orders(self):
        # Clear existing orders
        for widget in self.orders_container.winfo_children():
            widget.destroy()
        
        # Fetch and display orders
        orders = self.fetch_previous_orders()
        
        if not orders:
            no_orders_label = ctk.CTkLabel(self.orders_container, text="No previous orders", 
                                         font=("Arial", 14), text_color="gray")
            no_orders_label.pack(pady=20)
            return
        
        for order in orders:
            order_row = ctk.CTkFrame(self.orders_container, fg_color="white")
            order_row.pack(fill="x", padx=20, pady=5)
            
            # Format the date
            order_date = order["order_date"].strftime("%Y-%m-%d")
            
            # Order name (left-aligned)
            order_text = f"Order #{order['order_id']}"
            ctk.CTkLabel(order_row, text=order_text, 
                       font=("Arial", 16), text_color="black").pack(side="left", padx=15, pady=10)
            
            # Price (right-aligned)
            price_text = f"${float(order['total_amount']):.2f}"
            ctk.CTkLabel(order_row, text=price_text, 
                       font=("Arial", 16, "bold"), text_color="black").pack(side="right", padx=15, pady=10)
            
            # View button
            view_btn = ctk.CTkButton(order_row, text="View", 
                                   fg_color="#2563eb", hover_color="#1d4ed8", 
                                   font=("Arial", 12), width=80, height=30,
                                   command=lambda order_id=order['order_id']: self.view_order_details(order_id))
            view_btn.pack(side="right", padx=10, pady=10)
    
    def view_order_details(self, order_id):
        # Make sure current user info is saved to file
        write_login_file(self.current_user["username"], self.current_user["role"])
        
        # Launch the order details window
        self.root.withdraw()  # Hide current window
        subprocess.run(["python", os.path.join(os.path.dirname(__file__), "order_details.py"), str(order_id), self.current_user["username"]])
        self.root.deiconify()  # Show window again when order details is closed
    
    def logout(self):
        # Remove the user file when logging out
        if os.path.exists("current_user.txt"):
            os.remove("current_user.txt")
        
        self.root.destroy()
        subprocess.run(["python", os.path.join(os.path.dirname(os.path.dirname(__file__)), "login_signup.py")])

class UserNavigationExtended(UserNavigation):
    def __init__(self, parent_frame, user_app):
        self.user_app = user_app
        super().__init__(parent_frame)
    
    def navigate_to(self, destination):
        if destination == "Home":
            self.user_app.show_home_view()
        elif destination == "Cart":
            self.user_app.show_cart_view()
        elif destination == "Previous Orders":
            self.user_app.show_orders_view()
        elif destination == "Logout":
            self.user_app.logout()

# Run the user app if this file is executed directly
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    
    # Check if username was provided from command line
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        # Try to read from file
        username, _ = read_login_file()
        if not username:
            # No user info available
            messagebox.showerror("Authentication Error", "User not found. Please login again.")
            root.destroy()
            subprocess.run(["python", os.path.join(os.path.dirname(os.path.dirname(__file__)), "login_signup.py")])
            sys.exit(1)
    
    app = UserApp(root, username)
    root.mainloop()
    
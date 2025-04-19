import sys
import os
# Add parent directory to path so we can import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from tkinter import messagebox
import subprocess

from config import connect_db
from utils import setup_environment

# Set environment variables
setup_environment()

class OrderDetailsApp:
    def __init__(self, root, order_id, username):
        self.root = root
        self.order_id = order_id
        self.username = username
        self.root.title(f"SuperMarket - Order #{order_id} Details")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Current user info
        self.current_user = {
            "user_id": None,
            "username": None,
            "first_name": None,
            "last_name": None,
            "role": None
        }
        
        # Authenticate user
        if not self.get_user_info(username):
            messagebox.showerror("Authentication Error", "User not found. Please login again.")
            self.root.destroy()
            return
        
        self.setup_ui()
        self.display_order_details()
    
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
                return True
            
            return False
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def setup_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#f3f4f6", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="#2563eb", corner_radius=0, height=60)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        
        # Title
        title_label = ctk.CTkLabel(header_frame, text=f"Order #{self.order_id} Details", 
                                  font=("Arial", 18, "bold"), text_color="white")
        title_label.pack(side="left", padx=20, pady=10)
        
        # Back button
        back_btn = ctk.CTkButton(header_frame, text="Back", 
                               fg_color="transparent", hover_color="#1d4ed8", 
                               text_color="white", font=("Arial", 14), width=100,
                               command=self.return_to_home)
        back_btn.pack(side="right", padx=20, pady=10)
        
        # Content area
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=15)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create scrollable container for order details
        self.details_scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="white")
        self.details_scroll.pack(fill="both", expand=True, padx=20, pady=20)
    
    def get_status_color(self, status):
        """Return appropriate color based on order status"""
        status = status.lower()
        if status == "completed":
            return "#10b981"  # Green
        elif status == "pending":
            return "#f59e0b"  # Amber
        elif status == "cancelled":
            return "#ef4444"  # Red
        else:
            return "#6b7280"  # Gray
    
    def fetch_order_details(self):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # First, get basic order information
            cursor.execute("""
                SELECT o.order_id, o.order_date, o.total_amount, o.status, c.cart_id
                FROM Orders o
                JOIN Carts c ON o.cart_id = c.cart_id
                WHERE o.order_id = %s AND o.user_id = %s
                """, (self.order_id, self.current_user["user_id"]))
            
            order = cursor.fetchone()
            
            if not order:
                return None, []
            
            cart_id = order["cart_id"]
            
            # Now, get the items in this cart
            cursor.execute("""
                SELECT ci.quantity, p.name, p.price
                FROM CartItems ci
                JOIN Products p ON ci.product_id = p.product_id
                WHERE ci.cart_id = %s
                """, (cart_id,))
            
            items = cursor.fetchall()
            
            return order, items
        except Exception as err:
            messagebox.showerror("Database Error", str(err))
            return None, []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def display_order_details(self):
        # Fetch order details
        order, items = self.fetch_order_details()
        
        if not order:
            error_label = ctk.CTkLabel(self.details_scroll, text="Order not found or access denied",
                                     font=("Arial", 16), text_color="gray")
            error_label.pack(pady=20)
            return
        
        # Order header with improved design
        order_header = ctk.CTkFrame(self.details_scroll, fg_color="white", corner_radius=10)
        order_header.pack(fill="x", padx=20, pady=10)
        
        # Format the date
        order_date = order["order_date"].strftime("%B %d, %Y at %I:%M %p")
        
        # Order title and ID in a row
        title_row = ctk.CTkFrame(order_header, fg_color="transparent")
        title_row.pack(fill="x", padx=20, pady=(15, 5))
        
        order_title = ctk.CTkLabel(title_row, text=f"Order #{order['order_id']}",
                                  font=("Arial", 20, "bold"), text_color="#1e40af")
        order_title.pack(side="left")
        
        # Status badge
        status_color = self.get_status_color(order["status"])
        status_badge = ctk.CTkFrame(title_row, fg_color=status_color, corner_radius=15, height=30)
        status_badge.pack(side="right", padx=5)
        
        status_text = ctk.CTkLabel(status_badge, text=order["status"].capitalize(),
                                  font=("Arial", 12, "bold"), text_color="white")
        status_text.pack(padx=10, pady=5)
        
        # Order date with icon
        date_frame = ctk.CTkFrame(order_header, fg_color="transparent")
        date_frame.pack(fill="x", padx=20, pady=(0, 5))
        
        date_label = ctk.CTkLabel(date_frame, text=f"📅 {order_date}",
                                font=("Arial", 14), text_color="#4b5563")
        date_label.pack(anchor="w")
        
        # Total amount with icon
        total_frame = ctk.CTkFrame(order_header, fg_color="transparent")
        total_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        total_label = ctk.CTkLabel(total_frame, text=f"💰 Total: ${float(order['total_amount']):.2f}",
                                  font=("Arial", 16, "bold"), text_color="#1e40af")
        total_label.pack(anchor="w")
        
        # Divider
        divider = ctk.CTkFrame(order_header, height=1, fg_color="#e5e7eb")
        divider.pack(fill="x", padx=20, pady=(0, 15))
        
        # Items container
        if not items:
            no_items_label = ctk.CTkLabel(self.details_scroll, text="No items found in this order",
                                        font=("Arial", 16), text_color="gray")
            no_items_label.pack(pady=20)
            return
        
        items_frame = ctk.CTkFrame(self.details_scroll, fg_color="white", corner_radius=10)
        items_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Items header
        items_header = ctk.CTkLabel(items_frame, text="Order Items",
                                  font=("Arial", 18, "bold"), text_color="#1e40af")
        items_header.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Table header with improved design
        header_frame = ctk.CTkFrame(items_frame, fg_color="#f3f4f6", corner_radius=5)
        header_frame.pack(fill="x", padx=20, pady=(5, 0))
        
        # Header columns with better spacing
        ctk.CTkLabel(header_frame, text="Item", font=("Arial", 14, "bold"), text_color="#4b5563").pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(header_frame, text="Price", font=("Arial", 14, "bold"), text_color="#4b5563").pack(side="left", expand=True, pady=10)
        ctk.CTkLabel(header_frame, text="Quantity", font=("Arial", 14, "bold"), text_color="#4b5563").pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(header_frame, text="Subtotal", font=("Arial", 14, "bold"), text_color="#4b5563").pack(side="right", padx=20, pady=10)
        
        # Item rows with alternating colors
        for i, item in enumerate(items):
            # Alternate row colors
            row_color = "white" if i % 2 == 0 else "#f9fafb"
            
            item_row = ctk.CTkFrame(items_frame, fg_color=row_color)
            item_row.pack(fill="x", padx=20, pady=2)
            
            price = float(item["price"])
            quantity = item["quantity"]
            subtotal = price * quantity
            
            ctk.CTkLabel(item_row, text=item["name"], font=("Arial", 14), text_color="#1f2937").pack(side="left", padx=20, pady=10)
            ctk.CTkLabel(item_row, text=f"${price:.2f}", font=("Arial", 14), text_color="#4b5563").pack(side="left", expand=True, pady=10)
            ctk.CTkLabel(item_row, text=str(quantity), font=("Arial", 14), text_color="#4b5563").pack(side="left", padx=20, pady=10)
            ctk.CTkLabel(item_row, text=f"${subtotal:.2f}", font=("Arial", 14, "bold"), text_color="#1e40af").pack(side="right", padx=20, pady=10)
        
        # Summary section
        summary_frame = ctk.CTkFrame(items_frame, fg_color="#f3f4f6", corner_radius=5)
        summary_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        # Subtotal
        subtotal_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        subtotal_row.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(subtotal_row, text="Subtotal:", font=("Arial", 14), text_color="#4b5563").pack(side="left")
        ctk.CTkLabel(subtotal_row, text=f"${float(order['total_amount']):.2f}", font=("Arial", 14), text_color="#4b5563").pack(side="right")
        
        # Total with divider
        divider2 = ctk.CTkFrame(summary_frame, height=1, fg_color="#d1d5db")
        divider2.pack(fill="x", padx=20, pady=5)
        
        total_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        total_row.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(total_row, text="Total:", font=("Arial", 16, "bold"), text_color="#1e40af").pack(side="left")
        ctk.CTkLabel(total_row, text=f"${float(order['total_amount']):.2f}", font=("Arial", 16, "bold"), text_color="#1e40af").pack(side="right")
    
    def return_to_home(self):
        self.root.destroy()

# Run the app if this file is executed directly
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python order_details.py <order_id> <username>")
        sys.exit(1)
    
    order_id = sys.argv[1]
    username = sys.argv[2]
    
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    app = OrderDetailsApp(root, order_id, username)
    root.mainloop()
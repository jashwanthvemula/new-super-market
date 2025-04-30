import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import mysql.connector
import hashlib
import os
import subprocess
import re
import sys

from config_db import connect_db
from utils_file import hash_password, check_password_strength, write_login_file

# Set environment variables


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SuperMarket - Login")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)  # Set minimum window size
        
        self.setup_ui()
        self.root.bind("<Configure>", self.adjust_layout)
        
        # Initial layout adjustment
        self.root.update_idletasks()
        self.adjust_layout()
    
    def setup_ui(self):
        # Main Frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=10)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.9)
        
        # Left Side (Signup Form)
        self.left_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=0)
        self.left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        
        # Create a scrollable frame for the signup form
        self.scrollable_frame = ctk.CTkScrollableFrame(self.left_frame, fg_color="white", corner_radius=0)
        self.scrollable_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
        
        # SuperMarket Title
        self.title_label = ctk.CTkLabel(self.scrollable_frame, text="SuperMarket", 
                                    font=("Arial", 28, "bold"), text_color="#2563eb")
        self.title_label.pack(anchor="w", pady=(5, 0))
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(self.scrollable_frame, text="Manage your shopping experience\nseamlessly.", 
                                        font=("Arial", 14), text_color="gray")
        self.subtitle_label.pack(anchor="w", pady=(5, 20))
        
        # Create Account Header
        self.account_header = ctk.CTkLabel(self.scrollable_frame, text="Create your account", 
                                        font=("Arial", 18, "bold"), text_color="black")
        self.account_header.pack(anchor="w", pady=(10, 0))
        
        # Signup Instruction
        self.signup_instruction = ctk.CTkLabel(self.scrollable_frame, text="Fill in the details below to sign up.", 
                                            font=("Arial", 14), text_color="gray")
        self.signup_instruction.pack(anchor="w", pady=(5, 20))
        
        # First Name Entry
        self.first_name_label = ctk.CTkLabel(self.scrollable_frame, text="First Name", font=("Arial", 14), text_color="gray")
        self.first_name_label.pack(anchor="w", pady=(0, 5))
        self.first_name_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                        border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.first_name_entry.pack(fill="x", pady=(0, 15))
        
        # Last Name Entry
        self.last_name_label = ctk.CTkLabel(self.scrollable_frame, text="Last Name", font=("Arial", 14), text_color="gray")
        self.last_name_label.pack(anchor="w", pady=(0, 5))
        self.last_name_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                        border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.last_name_entry.pack(fill="x", pady=(0, 15))
        
        # Email Entry
        self.email_label = ctk.CTkLabel(self.scrollable_frame, text="Email", font=("Arial", 14), text_color="gray")
        self.email_label.pack(anchor="w", pady=(0, 5))
        self.email_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                    border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.email_entry.pack(fill="x", pady=(0, 15))
        
        # Secret Key Entry
        self.secret_label = ctk.CTkLabel(self.scrollable_frame, text="Secret Key", font=("Arial", 14), text_color="gray")
        self.secret_label.pack(anchor="w", pady=(0, 5))
        self.secret_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                    border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.secret_entry.pack(fill="x", pady=(0, 15))
        
        # Password Entry
        self.password_label = ctk.CTkLabel(self.scrollable_frame, text="Password", font=("Arial", 14), text_color="gray")
        self.password_label.pack(anchor="w", pady=(0, 5))
        self.password_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                        border_color="#e5e7eb", border_width=1, corner_radius=5, show="*")
        self.password_entry.pack(fill="x", pady=(0, 5))
        self.password_entry.bind("<KeyRelease>", self.on_password_change)
        
        # Password Strength Label
        self.password_strength_label = ctk.CTkLabel(self.scrollable_frame, text="", font=("Arial", 12), text_color="gray")
        self.password_strength_label.pack(anchor="w", pady=(5, 15))
        
        # Sign Up Button
        self.signup_btn = ctk.CTkButton(self.scrollable_frame, text="Sign Up", font=("Arial", 14, "bold"), 
                                    fg_color="#2563eb", hover_color="#1d4ed8",
                                    height=40, corner_radius=5, command=self.register_user)
        self.signup_btn.pack(fill="x", pady=(10, 20))
        
        # Bottom options frame - contains login link
        self.bottom_options_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.bottom_options_frame.pack(fill="x", pady=(0, 10))
        
        # Login Text
        self.login_frame = ctk.CTkFrame(self.bottom_options_frame, fg_color="transparent")
        self.login_frame.pack(fill="x")
        
        self.login_label = ctk.CTkLabel(self.login_frame, text="Already have an account?", 
                                    font=("Arial", 14), text_color="gray")
        self.login_label.pack(side="left", padx=(0, 5))
        
        self.login_link = ctk.CTkLabel(self.login_frame, text="Login", 
                                    font=("Arial", 14, "bold"), text_color="#2563eb", cursor="hand2")
        self.login_link.pack(side="left")
        self.login_link.bind("<Button-1>", lambda e: self.open_login())
        
        # Right Side (Image)
        self.right_frame = ctk.CTkFrame(self.main_frame, fg_color="#EBF3FF", corner_radius=0)
        self.right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        
        # Create a centered frame for the image
        self.image_container = ctk.CTkFrame(self.right_frame, fg_color="#EBF3FF", corner_radius=5, width=252, height=252)
        self.image_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Load and display the shopping cart image with transparency
        image_path = "images/shopping.png"
        try:
            # Create the CTkImage with transparency support
            self.img = ctk.CTkImage(light_image=Image.open(image_path), 
                                dark_image=Image.open(image_path),
                                size=(252, 252))
            
            # Create a label with transparent background
            self.image_label = ctk.CTkLabel(self.image_container, image=self.img, text="", bg_color="transparent")
            self.image_label.pack(fill="both", expand=True)
            
        except Exception as e:
            print(f"Error loading image: {e}")
            self.error_label = ctk.CTkLabel(self.image_container, text="🛒", font=("Arial", 72), text_color="#2563eb")
            self.error_label.pack(pady=50)
    
    def adjust_layout(self, event=None):
        """Adjust layout based on window size"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Adjust main frame
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", 
                            relwidth=min(0.95, 1200/width) if width > 800 else 0.98, 
                            relheight=min(0.9, 900/height) if height > 600 else 0.98)
        
        # If window is narrow, stack the frames vertically
        if width < 1000:
            self.left_frame.place(relx=0, rely=0, relwidth=1, relheight=0.65)
            self.right_frame.place(relx=0, rely=0.65, relwidth=1, relheight=0.35)
            self.scrollable_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
            
            # Adjust image size
            img_scale = min(1.0, width/1000)
            if self.img:
                self.img.configure(size=(int(252 * img_scale), int(252 * img_scale)))
        else:
            # Side by side layout for wider windows
            self.left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
            self.right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
            self.scrollable_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
            
            # Reset image size
            if self.img:
                self.img.configure(size=(252, 252))
    def on_password_change(self, event=None):
        password = self.password_entry.get()
        score, message = check_password_strength(password)
        
        # Set color based on strength
        if score == 0:
            color = "#f87171"  # Red
        elif score <= 2:
            color = "#fbbf24"  # Yellow
        elif score <= 4:
            color = "#34d399"  # Green
        else:
            color = "#2563eb"  # Blue
            
        self.password_strength_label.configure(text=message, text_color=color)
    
    def toggle_password_visibility(self):
        current_show_value = self.password_entry.cget("show")
        if current_show_value == "":  # Currently showing password
            self.password_entry.configure(show="*")
            self.password_toggle_btn.configure(text="👁️")  # Open eye when password is hidden
        else:  # Currently hiding password
            self.password_entry.configure(show="")
            self.password_toggle_btn.configure(text="👁️‍🗨️")  # Eye with speech bubble to indicate visible
    
    def login_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Input Error", "All fields are required.")
            return

        hashed_password = hash_password(password)

        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT first_name, last_name, role, status FROM Users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            user = cursor.fetchone()

            if user:
                first_name, last_name, role, status = user
                
                # Check if user account is active
                if status != "active":
                    messagebox.showerror("Account Disabled", "Your account has been disabled. Please contact an administrator.")
                    return
                    
                messagebox.showinfo("Success", f"Welcome {first_name} {last_name} ({role})!")
                
                # Save login info for other scripts
                write_login_file(username, role)
                
                # Launch appropriate view based on user role
                self.root.destroy()
                if role.lower() == "admin":
                    subprocess.run(["python", "admin/admin_view.py", username])
                else:
                    subprocess.run(["python", "users/users_view.py", username])
            else:
                messagebox.showerror("Error", "Invalid Username or Password")
                
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def open_signup(self):
        self.root.destroy()
        subprocess.run(["python", "login_signup.py", "signup"])
    
    def open_forgot_password(self):
        self.root.destroy()
        subprocess.run(["python", "users/forgot_password.py"])


class SignupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SuperMarket - Sign Up")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)
        
        self.img = None
        self.setup_ui()
        
        self.root.bind("<Configure>", self.adjust_layout)
        
        self.root.update_idletasks()
        self.adjust_layout()
    
    def setup_ui(self):
        # Main Frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=10)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.9)
        
        # Left Side (Signup Form)
        self.left_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=0)
        self.left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        
        # Create a scrollable frame for the signup form
        self.scrollable_frame = ctk.CTkScrollableFrame(self.left_frame, fg_color="white", corner_radius=0)
        self.scrollable_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
        
        # SuperMarket Title
        self.title_label = ctk.CTkLabel(self.scrollable_frame, text="SuperMarket", 
                                      font=("Arial", 28, "bold"), text_color="#2563eb")
        self.title_label.pack(anchor="w", pady=(5, 0))
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(self.scrollable_frame, text="Manage your shopping experience\nseamlessly.", 
                                         font=("Arial", 14), text_color="gray")
        self.subtitle_label.pack(anchor="w", pady=(5, 20))
        
        # Create Account Header
        self.account_header = ctk.CTkLabel(self.scrollable_frame, text="Create your account", 
                                        font=("Arial", 18, "bold"), text_color="black")
        self.account_header.pack(anchor="w", pady=(10, 0))
        
        # Signup Instruction
        self.signup_instruction = ctk.CTkLabel(self.scrollable_frame, text="Fill in the details below to sign up.", 
                                            font=("Arial", 14), text_color="gray")
        self.signup_instruction.pack(anchor="w", pady=(5, 20))
        
        # First Name Entry
        self.first_name_label = ctk.CTkLabel(self.scrollable_frame, text="First Name", font=("Arial", 14), text_color="gray")
        self.first_name_label.pack(anchor="w", pady=(0, 5))
        self.first_name_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                        border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.first_name_entry.pack(fill="x", pady=(0, 15))
        
        # Last Name Entry
        self.last_name_label = ctk.CTkLabel(self.scrollable_frame, text="Last Name", font=("Arial", 14), text_color="gray")
        self.last_name_label.pack(anchor="w", pady=(0, 5))
        self.last_name_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                        border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.last_name_entry.pack(fill="x", pady=(0, 15))
        
        # Email Entry
        self.email_label = ctk.CTkLabel(self.scrollable_frame, text="Email", font=("Arial", 14), text_color="gray")
        self.email_label.pack(anchor="w", pady=(0, 5))
        self.email_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                    border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.email_entry.pack(fill="x", pady=(0, 15))
        
        # Secret Key Entry
        self.secret_label = ctk.CTkLabel(self.scrollable_frame, text="Secret Key", font=("Arial", 14), text_color="gray")
        self.secret_label.pack(anchor="w", pady=(0, 5))
        self.secret_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                    border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.secret_entry.pack(fill="x", pady=(0, 15))
        
        # Password Entry
        self.password_label = ctk.CTkLabel(self.scrollable_frame, text="Password", font=("Arial", 14), text_color="gray")
        self.password_label.pack(anchor="w", pady=(0, 5))
        self.password_entry = ctk.CTkEntry(self.scrollable_frame, font=("Arial", 14), height=40,
                                        border_color="#e5e7eb", border_width=1, corner_radius=5, show="*")
        self.password_entry.pack(fill="x", pady=(0, 5))
        self.password_entry.bind("<KeyRelease>", self.on_password_change)
        
        # Password Strength Label
        self.password_strength_label = ctk.CTkLabel(self.scrollable_frame, text="", font=("Arial", 12), text_color="gray")
        self.password_strength_label.pack(anchor="w", pady=(5, 15))
        
        # Sign Up Button
        self.signup_btn = ctk.CTkButton(self.scrollable_frame, text="Sign Up", font=("Arial", 14, "bold"), 
                                      fg_color="#2563eb", hover_color="#1d4ed8",
                                      height=40, corner_radius=5, command=self.register_user)
        self.signup_btn.pack(fill="x", pady=(10, 20))
        
        # Bottom options frame - contains login link
        self.bottom_options_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.bottom_options_frame.pack(fill="x", pady=(0, 10))
        
        # Login Text
        self.login_frame = ctk.CTkFrame(self.bottom_options_frame, fg_color="transparent")
        self.login_frame.pack(fill="x")
        
        self.login_label = ctk.CTkLabel(self.login_frame, text="Already have an account?", 
                                       font=("Arial", 14), text_color="gray")
        self.login_label.pack(side="left", padx=(0, 5))
        
        self.login_link = ctk.CTkLabel(self.login_frame, text="Login", 
                                      font=("Arial", 14, "bold"), text_color="#2563eb", cursor="hand2")
        self.login_link.pack(side="left")
        self.login_link.bind("<Button-1>", lambda e: self.open_login())
        
        # Right Side (Image)
        self.right_frame = ctk.CTkFrame(self.main_frame, fg_color="#EBF3FF", corner_radius=0)
        self.right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        
        # Create a centered frame for the image
        self.image_container = ctk.CTkFrame(self.right_frame, fg_color="#EBF3FF", corner_radius=5, width=252, height=252)
        self.image_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Load and display the shopping cart image with transparency
        image_path = "images/shopping.png"
        try:
            # Create the CTkImage with transparency support
            self.img = ctk.CTkImage(light_image=Image.open(image_path), 
                                   dark_image=Image.open(image_path),
                                   size=(252, 252))
            
            # Create a label with transparent background
            self.image_label = ctk.CTkLabel(self.image_container, image=self.img, text="", bg_color="transparent")
            self.image_label.pack(fill="both", expand=True)
            
        except Exception as e:
            print(f"Error loading image: {e}")
            self.error_label = ctk.CTkLabel(self.image_container, text="🛒", font=("Arial", 72), text_color="#2563eb")
            self.error_label.pack(pady=50)
    
    def adjust_layout(self, event=None):
        """Adjust layout based on window size"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Adjust main frame
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", 
                            relwidth=min(0.95, 1200/width) if width > 800 else 0.98, 
                            relheight=min(0.9, 900/height) if height > 600 else 0.98)
        
        # If window is narrow, stack the frames vertically
        if width < 1000:
            self.left_frame.place(relx=0, rely=0, relwidth=1, relheight=0.65)
            self.right_frame.place(relx=0, rely=0.65, relwidth=1, relheight=0.35)
            self.scrollable_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
            
            # Adjust image size
            img_scale = min(1.0, width/1000)
            if self.img:
                self.img.configure(size=(int(252 * img_scale), int(252 * img_scale)))
        else:
            # Side by side layout for wider windows
            self.left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
            self.right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
            self.scrollable_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
            
            # Reset image size
            if self.img:
                self.img.configure(size=(252, 252))
    
    def on_password_change(self, event=None):
        password = self.password_entry.get()
        score, message = check_password_strength(password)
        
        # Set color based on strength
        if score == 0:
            color = "#f87171"  # Red
        elif score <= 2:
            color = "#fbbf24"  # Yellow
        elif score <= 4:
            color = "#34d399"  # Green
        else:
            color = "#2563eb"  # Blue
            
        self.password_strength_label.configure(text=message, text_color=color)
    
    def register_user(self):
        first_name = self.first_name_entry.get()
        last_name = self.last_name_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()
        secret_key = self.secret_entry.get()

        if not first_name or not last_name or not email or not password or not secret_key:
            messagebox.showwarning("Input Error", "All fields are required.")
            return

        # Check password strength before registration
        strength, _ = check_password_strength(password)
        if strength <= 2:
            messagebox.showwarning("Weak Password", "Please choose a stronger password.")
            return
            
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return

        hashed_password = hash_password(password)

        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Use email as username
            username = email
            cursor.execute(
                "INSERT INTO Users (first_name, last_name, username, email, password, role, secret_key) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (first_name, last_name, username, email, hashed_password, "user", secret_key)
            )
            
            connection.commit()
            messagebox.showinfo("Success", "User registered successfully!")
            
            # Clear the input fields
            self.first_name_entry.delete(0, ctk.END)
            self.last_name_entry.delete(0, ctk.END)
            self.email_entry.delete(0, ctk.END)
            self.password_entry.delete(0, ctk.END)
            self.secret_entry.delete(0, ctk.END)
            
            # Redirect to login page
            self.open_login()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def open_login(self):
        self.root.destroy()
        subprocess.run(["python", "login_signup.py"])

# Run the app
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    
    # Check if we should show signup instead of login
    if len(sys.argv) > 1 and sys.argv[1] == "signup":
        app = SignupApp(root)
    else:
        app = LoginApp(root)
        
    root.mainloop()
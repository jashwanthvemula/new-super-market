import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import mysql.connector
import hashlib
import os
import subprocess
import re
import sys

from config import connect_db
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
        
        # Left Side (Login Form)
        self.left_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=0)
        self.left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        
        # Create a form container for better alignment
        self.form_container = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.form_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)
        
        # SuperMarket Title
        self.title_label = ctk.CTkLabel(self.form_container, text="SuperMarket", 
                                      font=("Arial", 28, "bold"), text_color="#2563eb")
        self.title_label.pack(anchor="w", pady=(0, 5))
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(self.form_container, text="Manage your shopping experience seamlessly.", 
                                         font=("Arial", 14), text_color="gray")
        self.subtitle_label.pack(anchor="w", pady=(0, 30))
        
        # Login Details Header
        self.login_header = ctk.CTkLabel(self.form_container, text="Enter your login details", 
                                       font=("Arial", 18, "bold"), text_color="black")
        self.login_header.pack(anchor="w", pady=(0, 5))
        
        # Login Instruction
        self.login_instruction = ctk.CTkLabel(self.form_container, text="Enter the registered credentials used while signing up", 
                                           font=("Arial", 14), text_color="gray")
        self.login_instruction.pack(anchor="w", pady=(0, 30))
        
        # Username Label
        self.username_label = ctk.CTkLabel(self.form_container, text="Username", font=("Arial", 14), text_color="gray")
        self.username_label.pack(anchor="w", pady=(0, 5))
        
        # Username Entry
        self.username_entry = ctk.CTkEntry(self.form_container, font=("Arial", 14), height=40, 
                                         border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.username_entry.pack(fill="x", pady=(0, 15))
        
        # Password Label
        self.password_label = ctk.CTkLabel(self.form_container, text="Password", font=("Arial", 14), text_color="gray")
        self.password_label.pack(anchor="w", pady=(0, 5))
        
        # Create a frame to hold password entry field and toggle button
        self.password_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        self.password_frame.pack(fill="x", pady=(0, 5))
        
        # Password Entry
        self.password_entry = ctk.CTkEntry(self.password_frame, font=("Arial", 14), height=40, 
                                         border_color="#e5e7eb", border_width=1, corner_radius=5, show="*")
        self.password_entry.pack(side="left", fill="x", expand=True)
        
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
        
        # Bind password entry to check strength on key release
        self.password_entry.bind("<KeyRelease>", lambda e: self.on_password_change())
        
        # Password Strength Label (hidden initially)
        self.password_strength_label = ctk.CTkLabel(self.form_container, text="", font=("Arial", 12))
        # This will be packed/unpacked dynamically based on password input
        
        # Login Button
        self.login_btn = ctk.CTkButton(self.form_container, text="Login", font=("Arial", 14, "bold"), 
                                     fg_color="#2563eb", hover_color="#1d4ed8",
                                     height=40, corner_radius=5, command=self.login_user)
        self.login_btn.pack(fill="x", pady=(10, 20))
        
        # Bottom options frame - contains both signup and forgot password
        self.bottom_options_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        self.bottom_options_frame.pack(fill="x")
        
        # Sign Up Text
        self.signup_frame = ctk.CTkFrame(self.bottom_options_frame, fg_color="transparent")
        self.signup_frame.pack(fill="x", pady=(5, 5))
        
        self.signup_label = ctk.CTkLabel(self.signup_frame, text="Don't have an account?", 
                                       font=("Arial", 14), text_color="gray")
        self.signup_label.pack(side="left", padx=(0, 5))
        
        self.signup_link = ctk.CTkLabel(self.signup_frame, text="Sign Up", 
                                      font=("Arial", 14, "bold"), text_color="#2563eb", cursor="hand2")
        self.signup_link.pack(side="left")
        self.signup_link.bind("<Button-1>", lambda e: self.open_signup())
        
        # Forgot Password
        self.forgot_pwd_label = ctk.CTkLabel(self.bottom_options_frame, text="Forgot Password?", 
                                         font=("Arial", 14), text_color="#2563eb", cursor="hand2")
        self.forgot_pwd_label.pack(anchor="w", pady=(0, 5))
        self.forgot_pwd_label.bind("<Button-1>", lambda e: self.open_forgot_password())
        
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
    
    def adjust_layout(self, event=None):
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Update main frame
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", 
                         relwidth=min(0.95, 1400/width) if width > 800 else 0.98, 
                         relheight=min(0.9, 900/height) if height > 600 else 0.98)
        
        # Adjust layout based on screen size
        if width < 1200:
            # Stack vertically on smaller screens
            self.left_frame.place(relx=0.5, rely=0, relwidth=1, relheight=0.5, anchor="n")
            self.right_frame.place(relx=0.5, rely=1, relwidth=1, relheight=0.5, anchor="s")
            
            # Adjust form container
            self.form_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
            
            # Adjust image size for vertical layout
            if hasattr(self, 'img'):
                self.img.configure(size=(int(width*0.3), int(width*0.3)))
            
            # For very small screens, adjust font sizes and spacings
            if width < 900:
                self.title_label.configure(font=("Arial", 24, "bold"))
                self.subtitle_label.configure(font=("Arial", 12))
                self.login_header.configure(font=("Arial", 16, "bold"))
                self.login_instruction.configure(font=("Arial", 12))
                # Reduce vertical spacing
                self.title_label.pack(anchor="w", pady=(0, 3))
                self.subtitle_label.pack(anchor="w", pady=(0, 15))
                self.login_header.pack(anchor="w", pady=(0, 3))
                self.login_instruction.pack(anchor="w", pady=(0, 15))
            else:
                # Reset to original values for larger screens
                self.title_label.configure(font=("Arial", 28, "bold"))
                self.subtitle_label.configure(font=("Arial", 14))
                self.login_header.configure(font=("Arial", 18, "bold"))
                self.login_instruction.configure(font=("Arial", 14))
                # Reset spacing
                self.title_label.pack(anchor="w", pady=(0, 5))
                self.subtitle_label.pack(anchor="w", pady=(0, 30))
                self.login_header.pack(anchor="w", pady=(0, 5))
                self.login_instruction.pack(anchor="w", pady=(0, 30))
                
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
            
        # Ensure that bottom elements (signup and forgot password) are visible
        # This needs to be done after the above layout adjustments
        
        # Get current form container dimensions
        form_width = self.form_container.winfo_width()
        form_height = self.form_container.winfo_height()
        
        # Calculate content height by summing up all widgets' heights and spacing
        # This is an approximation
        content_height = sum([w.winfo_reqheight() for w in self.form_container.winfo_children() if hasattr(w, 'winfo_reqheight')])
        
        # If content might overflow, adjust the layout to make it more compact
        if content_height > form_height * 0.9:  # If content takes more than 90% of available height
            # Make elements more compact
            self.login_btn.pack(fill="x", pady=(5, 10))  # Reduce padding around login button
            self.signup_frame.pack(fill="x", pady=(5, 0))  # Reduce padding above signup frame
            
            # Ensure forgot password is visible
            self.forgot_pwd_label.pack(anchor="w", pady=(3, 0))
        else:
            # Normal spacing
            self.login_btn.pack(fill="x", pady=(10, 20))
            self.signup_frame.pack(fill="x", pady=(10, 0))
            self.forgot_pwd_label.pack(anchor="w", pady=(5, 0))
    
    def on_password_change(self):
        password = self.password_entry.get()
        score, message = check_password_strength(password)
        
        # Update strength label
        if password:
            if score == 0:
                color = "#ef4444"  # Red
            elif score <= 2:
                color = "#f59e0b"  # Orange
            elif score <= 3:
                color = "#3b82f6"  # Blue
            else:
                color = "#10b981"  # Green
                
            self.password_strength_label.configure(text=message, text_color=color)
            self.password_strength_label.pack(anchor="w", pady=(5, 10))
        else:
            self.password_strength_label.pack_forget()
    
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
                "SELECT first_name, last_name, role FROM Users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            user = cursor.fetchone()

            if user:
                first_name, last_name, role = user
                
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
        self.root.geometry("1500x1000")  # Starting size
        self.root.minsize(700, 800)  # Minimum window size
        
        self.img = None  # Store image reference
        self.setup_ui()
        
        # Bind resize event to adjust layout
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
        
        # SuperMarket Title
        self.title_label = ctk.CTkLabel(self.left_frame, text="SuperMarket", 
                                      font=("Arial", 28, "bold"), text_color="#2563eb")
        self.title_label.place(relx=0.1, rely=0.1)
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(self.left_frame, text="Manage your shopping experience\nseamlessly.", 
                                         font=("Arial", 14), text_color="gray")
        self.subtitle_label.place(relx=0.1, rely=0.17)
        
        # Create Account Header
        self.account_header = ctk.CTkLabel(self.left_frame, text="Create your account", 
                                        font=("Arial", 18, "bold"), text_color="black")
        self.account_header.place(relx=0.1, rely=0.3)
        
        # Signup Instruction
        self.signup_instruction = ctk.CTkLabel(self.left_frame, text="Fill in the details below to sign up.", 
                                            font=("Arial", 14), text_color="gray")
        self.signup_instruction.place(relx=0.1, rely=0.37)
        
        # First Name Label
        self.first_name_label = ctk.CTkLabel(self.left_frame, text="First Name", font=("Arial", 14), text_color="gray")
        self.first_name_label.place(relx=0.5, rely=0.30)
        
        # First Name Entry
        self.first_name_entry = ctk.CTkEntry(self.left_frame, font=("Arial", 14), height=40, width=300, 
                                          border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.first_name_entry.place(relx=0.1, rely=0.48)
        
        # Last Name Label
        self.last_name_label = ctk.CTkLabel(self.left_frame, text="Last Name", font=("Arial", 14), text_color="gray")
        self.last_name_label.place(relx=0.1, rely=0.54)
        
        # Last Name Entry
        self.last_name_entry = ctk.CTkEntry(self.left_frame, font=("Arial", 14), height=40, width=300, 
                                         border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.last_name_entry.place(relx=0.1, rely=0.58)
        
        # Email Label
        self.email_label = ctk.CTkLabel(self.left_frame, text="Email", font=("Arial", 14), text_color="gray")
        self.email_label.place(relx=0.1, rely=0.64)
        
        # Email Entry
        self.email_entry = ctk.CTkEntry(self.left_frame, font=("Arial", 14), height=40, width=300, 
                                      border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.email_entry.place(relx=0.1, rely=0.68)
        
        # Secret Key Label
        self.secret_key_label = ctk.CTkLabel(self.left_frame, text="Secret Key", font=("Arial", 14), text_color="gray")
        self.secret_key_label.place(relx=0.1, rely=0.74)
        
        # Secret Key Entry
        self.secret_entry = ctk.CTkEntry(self.left_frame, font=("Arial", 14), height=40, width=300, 
                                      border_color="#e5e7eb", border_width=1, corner_radius=5)
        self.secret_entry.place(relx=0.1, rely=0.78)
        
        # Password Label
        self.password_label = ctk.CTkLabel(self.left_frame, text="Password", font=("Arial", 14), text_color="gray")
        self.password_label.place(relx=0.1, rely=0.84)
        
        # Password Entry
        self.password_entry = ctk.CTkEntry(self.left_frame, font=("Arial", 14), height=40, width=300, 
                                         border_color="#e5e7eb", border_width=1, corner_radius=5, show="*")
        self.password_entry.place(relx=0.1, rely=0.88)
        self.password_entry.bind("<KeyRelease>", self.on_password_change)
        
        # Password Strength Label
        self.password_strength_label = ctk.CTkLabel(self.left_frame, text="", font=("Arial", 12), text_color="gray")
        self.password_strength_label.place(relx=0.1, rely=0.92)
        
        # Sign Up Button
        self.signup_btn = ctk.CTkButton(self.left_frame, text="Sign Up", font=("Arial", 14, "bold"), 
                                      fg_color="#2563eb", hover_color="#1d4ed8",
                                      height=40, width=300, corner_radius=5, command=self.register_user)
        self.signup_btn.place(relx=0.1, rely=0.94)
        
        # Already have an account text
        self.login_label = ctk.CTkLabel(self.left_frame, text="Already have an account? Login", 
                                      font=("Arial", 14), text_color="#2563eb", cursor="hand2")
        self.login_label.place(relx=0.1, rely=0.98)
        self.login_label.bind("<Button-1>", lambda e: self.open_login())
        
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
                            relheight=min(0.9, 900/height) if height > 700 else 0.98)
        
        # If window is narrow, stack the frames vertically
        if width < 1000:
            self.left_frame.place(relx=0, rely=0, relwidth=1, relheight=0.65)
            self.right_frame.place(relx=0, rely=0.65, relwidth=1, relheight=0.35)
            
            # Adjust form elements for narrower width
            form_width = min(300, width * 0.8)
            form_relx = 0.5
            form_rely_start = 0.12
            form_rely_step = 0.09
            anchor = "center"
            
            # Adjust image size
            img_scale = min(1.0, width/1000)
            if self.img:
                self.img.configure(size=(int(252 * img_scale), int(252 * img_scale)))
            
        else:
            # Side by side layout for wider windows
            self.left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
            self.right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
            
            form_width = min(300, (width * 0.5) * 0.8)
            form_relx = 0.1
            form_rely_start = 0.1
            form_rely_step = 0.06
            anchor = "w"
            
            # Reset image size
            if self.img:
                self.img.configure(size=(252, 252))
        
        # Adjust form elements
        self.title_label.place(relx=form_relx, rely=form_rely_start, anchor=anchor)
        self.subtitle_label.place(relx=form_relx, rely=form_rely_start + form_rely_step, anchor=anchor)
        self.account_header.place(relx=form_relx, rely=form_rely_start + form_rely_step * 3, anchor=anchor)
        self.signup_instruction.place(relx=form_relx, rely=form_rely_start + form_rely_step * 4, anchor=anchor)
        
        # Adjust all field positions based on the new layout
        field_rely = form_rely_start + form_rely_step * 5
        for field in [
            (self.first_name_label, self.first_name_entry),
            (self.last_name_label, self.last_name_entry),
            (self.email_label, self.email_entry),
            (self.secret_key_label, self.secret_entry),
            (self.password_label, self.password_entry)
        ]:
            label, entry = field
            label.place(relx=form_relx, rely=field_rely, anchor=anchor)
            entry.place(relx=form_relx, rely=field_rely + form_rely_step*0.6, anchor=anchor)
            entry.configure(width=form_width)
            field_rely += form_rely_step * 1.8
        
        # Place password strength label
        self.password_strength_label.place(relx=form_relx, rely=field_rely - form_rely_step, anchor=anchor)
        
        # Place buttons at the bottom
        self.signup_btn.place(relx=form_relx, rely=field_rely + form_rely_step*0.4, anchor=anchor)
        self.signup_btn.configure(width=form_width)
        self.login_label.place(relx=form_relx, rely=field_rely + form_rely_step*1.2, anchor=anchor)
        
        # Adjust image container
        if width < 1000:
            self.image_container.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.image_container.place(relx=0.5, rely=0.5, anchor="center")
    
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
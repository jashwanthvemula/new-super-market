import customtkinter as ctk
from PIL import Image
import os

class AdminNavigation:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.setup_sidebar()
        
    def setup_sidebar(self):
        # Sidebar (Navigation Menu)
        self.sidebar = ctk.CTkFrame(self.parent, width=250, height=700, corner_radius=0, fg_color="#2563eb")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)  # Prevent the frame from shrinking
        
        # Logo/Icon at the top
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(30, 0))
        
        # Try to load the logo if available
        try:
            image_path = os.path.join("images", "shopping.png")
            logo_img = ctk.CTkImage(light_image=Image.open(image_path), 
                                   dark_image=Image.open(image_path),
                                   size=(80, 80))
            
            logo_label = ctk.CTkLabel(logo_frame, image=logo_img, text="")
            logo_label.pack()
        except Exception as e:
            print(f"Error loading logo image: {e}")
            # Use an emoji as a fallback
            logo_label = ctk.CTkLabel(logo_frame, text="🛒", font=("Arial", 48), text_color="white")
            logo_label.pack()
        
        # Sidebar Title
        title_label = ctk.CTkLabel(self.sidebar, text="Admin Panel", font=("Arial", 24, "bold"), text_color="white")
        title_label.pack(pady=(15, 30))
        
        # Divider
        divider = ctk.CTkFrame(self.sidebar, height=1, width=200, fg_color="#4b72d9")
        divider.pack(pady=10)
        
        # Navigation section title
        nav_label = ctk.CTkLabel(self.sidebar, text="NAVIGATION", font=("Arial", 12), text_color="#b0c4ea")
        nav_label.pack(anchor="w", padx=25, pady=(20, 10))
        
        # Menu items with icons (using emoji as icons)
        menu_items = [
            ("🏷️ Manage Inventory", "Manage Inventory"),
            ("👥 Manage Users", "Manage Users"),
            ("📊 Generate Report", "Generate Report"),
            ("🚪 Logout", "Logout")
        ]
        
        for icon_text, command_text in menu_items:
            btn = ctk.CTkButton(self.sidebar, text=icon_text, fg_color="transparent", 
                            text_color="white", font=("Arial", 16),
                            anchor="w", height=40,
                            corner_radius=0, hover_color="#1d4ed8",
                            command=lambda cmd=command_text: self.navigate_to(cmd))
            btn.pack(fill="x", pady=5, padx=10)
        
        # Version information at bottom
        version_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        version_frame.pack(side="bottom", pady=20)
        
        version_label = ctk.CTkLabel(version_frame, text="SuperMarket v1.0", font=("Arial", 12), text_color="#b0c4ea")
        version_label.pack()
    
    def navigate_to(self, destination):
        # This method will be overridden in the admin_view.py file
        pass
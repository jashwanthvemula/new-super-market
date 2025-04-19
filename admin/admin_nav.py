import customtkinter as ctk

class AdminNavigation:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.setup_sidebar()
        
    def setup_sidebar(self):
        # Sidebar (Navigation Menu)
        self.sidebar = ctk.CTkFrame(self.parent, width=250, height=700, corner_radius=0, fg_color="#2563eb")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)  # Prevent the frame from shrinking
        
        # Sidebar Title
        title_label = ctk.CTkLabel(self.sidebar, text="Admin Panel", font=("Arial", 24, "bold"), text_color="white")
        title_label.pack(pady=(40, 30))
        
        # Sidebar Buttons
        menu_items = ["Manage Inventory", "Manage Users", "Generate Report", "Logout"]
        
        for item in menu_items:
            btn = ctk.CTkButton(self.sidebar, text=item, fg_color="transparent", 
                            text_color="white", font=("Arial", 16),
                            anchor="w", height=40,
                            corner_radius=0, hover_color="#1d4ed8",
                            command=lambda i=item: self.navigate_to(i))
            btn.pack(fill="x", pady=5, padx=10)
    
    def navigate_to(self, destination):
        # This method will be overridden in the admin_view.py file
        pass
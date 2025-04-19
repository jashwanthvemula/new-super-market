import mysql.connector
from tkinter import messagebox

# Database configuration
# DB_CONFIG = {
#     "host": "141.209.241.57",
#     "user": "kshat1m",
#     "password": "mypass",
#     "database": "BIS698W1700_GRP2"
# }
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "new_password",
    "database": "supermarket123",
   
}

def connect_db():
    """Create a connection to the database"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None
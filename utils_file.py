import hashlib
import os
import re
from tkinter import messagebox

# User session management
def write_login_file(username, role="user"):
    """Write login info to a temporary file for other scripts to use"""
    try:
        with open("current_user.txt", "w") as f:
            f.write(f"{username}\n{role}")
        return True
    except Exception as e:
        print(f"Error writing login file: {e}")
        return False

def read_login_file():
    """Read login info from temporary file"""
    try:
        if os.path.exists("current_user.txt"):
            with open("current_user.txt", "r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    return lines[0].strip(), lines[1].strip()
        return None, None
    except Exception as e:
        print(f"Error reading login file: {e}")
        return None, None

# Password utilities
def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password_strength(password):
    """Check password strength and return a score and feedback"""
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Too short (min 8 characters)")
    
    # Complexity checks
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Add uppercase letters")
        
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Add lowercase letters")
        
    if re.search(r'[0-9]', password):
        score += 1
    else:
        feedback.append("Add numbers")
        
    if re.search(r'[^A-Za-z0-9]', password):
        score += 1
    else:
        feedback.append("Add special characters")
    
    # Determine message based on score
    if score == 0:
        return score, "Very weak password"
    elif score <= 2:
        return score, "Weak password: " + ", ".join(feedback[:2])
    elif score == 3:
        return score, "Moderate password"
    elif score == 4:
        return score, "Strong password"
    else:
        return score, "Very strong password"

# Environment setup

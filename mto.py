import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import hashlib
import os
import tempfile
import webbrowser
import subprocess
import spacy
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from itertools import cycle

class MTO:
    def __init__(self, master):
        self.master = master
        master.title("MTO Tool")

        # Creating a notebook for multiple pages
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=1, fill="both")

        # This is the Login/Register page
        self.create_login_page()

        # Here I am initialising the database
        self.conn = sqlite3.connect("user_data.db")
        self.create_table()

        # This is a temporary directory for storing CV files
        self.temp_dir = tempfile.mkdtemp()

    def create_table(self):
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    age INTEGER,
                    interests TEXT,
                    cv_path TEXT
                )
            ''')
            self.conn.commit()

    def create_login_page(self):
        login_frame = ttk.Frame(self.notebook)
        self.notebook.add(login_frame, text="Login/Register")

        self.label = tk.Label(login_frame, text="Welcome to MTO Tool!")
        self.label.pack()

        # This is the login section
        self.username_label = tk.Label(login_frame, text="Username:")
        self.username_label.pack()
        self.username_entry = tk.Entry(login_frame)
        self.username_entry.pack()

        self.password_label = tk.Label(login_frame, text="Password:")
        self.password_label.pack()
        self.password_entry = tk.Entry(login_frame, show="*")  # Show '*' for password
        self.password_entry.pack()

        self.login_button = tk.Button(login_frame, text="Login", command=self.login)
        self.login_button.pack()

        # This is the register section
        self.new_username_label = tk.Label(login_frame, text="New Username:")
        self.new_username_label.pack()
        self.new_username_entry = tk.Entry(login_frame)
        self.new_username_entry.pack()

        self.new_password_label = tk.Label(login_frame, text="New Password:")
        self.new_password_label.pack()
        self.new_password_entry = tk.Entry(login_frame, show="*")  # Show '*' for password
        self.new_password_entry.pack()

        self.age_label = tk.Label(login_frame, text="Age:")
        self.age_label.pack()
        self.age_entry = tk.Entry(login_frame)
        self.age_entry.pack()

        # This is a dropdown menu for users interests
        self.interests_label = tk.Label(login_frame, text="Interests:")
        self.interests_label.pack()
        interests_options = ["Programming", "Data Science", "Software Engineering", "Accounting", "Other"]
        self.selected_interest = tk.StringVar(login_frame)
        self.selected_interest.set(interests_options[0])
        self.interests_dropdown = tk.OptionMenu(login_frame, self.selected_interest, *interests_options)
        self.interests_dropdown.pack()

        self.register_button = tk.Button(login_frame, text="Register", command=self.register_profile)
        self.register_button.pack()

        

        
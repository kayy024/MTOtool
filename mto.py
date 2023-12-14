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

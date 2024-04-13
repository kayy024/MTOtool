import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import hashlib
import os
import tempfile
import webbrowser
import subprocess
import spacy
import csv
import PyPDF2
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

        #Here I am loading the spaCy model
        self.nlp = spacy.load("en_core_web_sm")

        # Flag to track whether additional pages have been created after login
        self.pages_created = False

        # Store the current username
        self.current_username = None

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

        # This is the CV page where users can add their file
    def create_upload_cv_page(self):
        upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(upload_frame, text="Upload CV")

        upload_label = tk.Label(upload_frame, text="Upload your CV:")
        upload_label.pack()

        upload_button = tk.Button(upload_frame, text="Choose File", command=self.choose_file)
        upload_button.pack()

        update_button = tk.Button(upload_frame, text="Update CV", command=self.update_cv)
        update_button.pack()

        delete_button = tk.Button(upload_frame, text="Delete CV", command=self.delete_cv)
        delete_button.pack()

        view_button = tk.Button(upload_frame, text="View CV", command=self.view_cv)
        view_button.pack()

        logout_button = tk.Button(upload_frame, text="Logout", command=self.logout)
        logout_button.pack()

        # This is to allow users to upload a PDF of their CV
    def choose_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
        if file_path:
            messagebox.showinfo("File Selected", f"Selected File: {file_path}")
            self.save_cv_path(file_path)

        # This is to allow users save their CV
    def save_cv_path(self, cv_path):
        username = self.current_username
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET cv_path=? WHERE username=?", (cv_path, username))
        self.conn.commit()

        # This is to allow users to update their CV
    def update_cv(self):
        username = self.current_username
        cursor = self.conn.cursor()
        cursor.execute("SELECT cv_path FROM users WHERE username=?", (username,))
        result = cursor.fetchone()

        if result is not None:
            current_cv_path = result[0]

            if current_cv_path:
                if os.path.exists(current_cv_path):
                    os.remove(current_cv_path)

                new_cv_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
                if new_cv_path:
                    messagebox.showinfo("File Updated", f"Updated CV: {new_cv_path}")
                    self.save_cv_path(new_cv_path)
            else:
                messagebox.showinfo("No CV", "No CV to update.")
        else:
            messagebox.showinfo("No CV", "No CV to update.")

        # This is to allow users to delete their CV
    def delete_cv(self):
        username = self.current_username
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET cv_path=NULL WHERE username=?", (username,))
        self.conn.commit()
        messagebox.showinfo("CV Deleted", "CV path successfully removed from the database.")

        # This is to allow users view their uploaded CV
    def view_cv(self):
        username = self.current_username
        cursor = self.conn.cursor()
        cursor.execute("SELECT cv_path FROM users WHERE username=?", (username,))
        result = cursor.fetchone()

        if result is not None:
            current_cv_path = result[0]

            if current_cv_path:
                try:
                    subprocess.run(["open", current_cv_path], check=True)  
                except subprocess.CalledProcessError as e:
                    print(f"Error opening PDF: {e}")
            else:
                messagebox.showinfo("No CV", "No CV to view.")
        else:
            messagebox.showinfo("No CV", "No CV to view.")

    def load_job_keywords(self):
        job_keywords = {}

        with open('jobs.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                job_id = row['jobs_id']
                keywords = [kw.strip() for kw in row[' keywords'].split(',')]
                job_keywords[job_id] = keywords

        return job_keywords

    def extract_keywords_from_pdf(self, pdf_path):
        if pdf_path is None or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "CV file not found.")
            return []
        
        keywords = set()

        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                doc = self.nlp(text)

                for token in doc:
                    if not token.is_stop and not token.is_punct:
                        keywords.add(token.text.lower())

        return list(keywords)

    def match_jobs_to_keywords(self, cv_keywords):
        jobs_keywords = self.load_job_keywords()

        matching_jobs = []
        for job_id, job_keywords in jobs_keywords.items():
            # Combine user CV keywords and job keywords into documents
            documents = [", ".join(cv_keywords), ", ".join(job_keywords)]

            # Convert documents to vectors
            count_vectorizer = CountVectorizer()
            sparse_matrix = count_vectorizer.fit_transform(documents)

            # Calculate cosine similarity between user CV and job keywords
            cosine_sim = cosine_similarity(sparse_matrix, sparse_matrix)

            # Get similarity score between user CV and job keywords
            similarity_score = cosine_sim[0][1]

            # If similarity score is above a certain threshold, consider it a matching job
            if similarity_score > 0.5:  # Adjust the threshold as needed
                matching_jobs.append(job_id)

        return matching_jobs 

    def display_matching_jobs(self, matching_frame, matching_jobs):
        jobs_label = tk.Label(matching_frame, text="Matching Jobs:")
        jobs_label.pack()

        find_jobs_button = tk.Button(matching_frame, text="Find Jobs Now", command=self.find_jobs)
        find_jobs_button.pack()

        for job_id in matching_jobs:
            job_url = self.get_job_url(job_id)
            job_label_text = f"{job_id} - {job_url}"

            job_label = tk.Label(matching_frame, text=job_label_text, fg="blue", cursor="hand2")
            job_label.bind("<Button-1>", lambda event, url=job_url: self.open_url(event, url))
            job_label.pack()

    def find_jobs(self):
        # Get the current user's CV path
        cv_path = self.get_current_cv_path()

        print(f"CV Path: {cv_path}")

        if not cv_path or not os.path.exists(cv_path):
            messagebox.showinfo("No CV", "No valid CV found.")
            return

        print("CV exists and is valid.")

        # Extract keywords from the user's CV
        cv_keywords = self.extract_keywords_from_pdf(cv_path)

        print(f"Extracted Keywords: {cv_keywords}")

        # Match jobs based on keywords
        matching_jobs = self.match_jobs_to_keywords(cv_keywords)

        # Display the matching jobs
        matching_frame = self.notebook.winfo_children()[2]
        self.display_matching_jobs(matching_frame, matching_jobs)

            # This page which will match users to jobs
    def create_matching_page(self):
        matching_frame = ttk.Frame(self.notebook)
        self.notebook.add(matching_frame, text="Matching")

        matching_label = tk.Label(matching_frame, text="Matching in progress...")
        matching_label.pack()

        # Get the current user's CV path
        cv_path = self.get_current_cv_path()
        if cv_path:
            # Extract keywords from the user's CV
            cv_keywords = self.extract_keywords_from_pdf(cv_path)

            # Now you can use cv_keywords to match with job requirements
            matching_jobs = self.match_jobs_to_keywords(cv_keywords)

            # Display the matching jobs
            self.display_matching_jobs(matching_frame, matching_jobs)
        else:
            messagebox.showinfo("No CV", "No CV to match.")

        logout_button = tk.Button(matching_frame, text="Logout", command=self.logout)
        logout_button.pack()

        # This is a chatbot page
    def create_chatbot_page(self):
        chatbot_frame = ttk.Frame(self.notebook)
        self.notebook.add(chatbot_frame, text="Chatbot")

        chatbot_label = tk.Label(chatbot_frame, text="Chatbot interface will be here.")
        chatbot_label.pack()

        logout_button = tk.Button(chatbot_frame, text="Logout", command=self.logout)
        logout_button.pack()

    def create_logout_page(self):
        logout_frame = ttk.Frame(self.notebook)
        self.notebook.add(logout_frame, text="Logout")

        logout_button = tk.Button(logout_frame, text="Logout", command=self.logout)
        logout_button.pack()


    def logout(self):
        # Remove all pages except the login/register page
        for page in self.notebook.winfo_children()[1:]:
            self.notebook.forget(page)

        # Clears the username and password entry fields
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
    
        self.pages_created = False
        
        # Return to the login/register page
        self.notebook.select(0)

    def login(self):
        # Get user input
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Hash the entered password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Authenticate user
        if self.authenticate(username, hashed_password):
            messagebox.showinfo("Login", "Login successful!")
            # Store the current username
            self.current_username = username
            self.create_pages_after_login()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def authenticate(self, username, hashed_password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        return cursor.fetchone() is not None
    
    def register_profile(self):
        # This allows the tool to get user input
        new_username = self.new_username_entry.get()
        new_password = self.new_password_entry.get()
        age = self.age_entry.get()
        selected_interest = self.selected_interest.get()

        # This validates the input
        if not new_username or not new_password:
            messagebox.showerror("Error", "Username and password are required.")
            return

        # This hashes the password before storing
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

        # This is to get the CV file path
        cv_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
        
        # This is to test user registration
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (username, password, age, interests, cv_path) VALUES (?, ?, ?, ?, ?)",
               (new_username, hashed_password, age, selected_interest, cv_path if cv_path else None))
        self.conn.commit()

        messagebox.showinfo("Registration", "Registration successful!")
        self.create_pages_after_login()

    def create_pages_after_login(self):
        # After a successful login or registration, the gui will create the additional pages
        if not self.pages_created:
            self.create_upload_cv_page()
            self.create_matching_page()
            self.create_chatbot_page()
            self.create_logout_page()
            # Set the flag to True after creating the pages
            self.pages_created = True
        # This redirects users to the CV page as soon as they are logged in
        self.notebook.select(1)

    def get_current_cv_path(self):
        username = self.current_username
        cursor = self.conn.cursor()
        cursor.execute("SELECT cv_path FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else ""

if __name__ == "__main__":
    root = tk.Tk()
    app = MTO(root)
    root.mainloop()

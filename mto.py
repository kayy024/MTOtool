# Importing the necessary libraries and modules for the MTO tool.
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
import tkinter.scrolledtext as scrolledtext
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity 


class MTO:
    def __init__(self, master):
        self.master = master
        master.title("MTO Tool")

        # Creating a notebook for multiple pages.
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=1, fill="both")

        # This is the Login/Register page.
        self.create_login_page()

        # Here I am initialising the database.
        self.conn = sqlite3.connect("user_data.db")
        self.create_table()

        # This is a temporary directory for storing CV files.
        self.temp_dir = tempfile.mkdtemp()

        #Here I am loading the spaCy model.
        self.nlp = spacy.load("en_core_web_sm")

        # A flag to track whether additional pages have been created after login.
        self.pages_created = False

        # This is to store the current username.
        self.current_username = None

        # Storing the predetermined responses for the chatbot.
        self.chatbot_responses = {
        "hello": "Hi there! How can I assist you today?",
        "job matching": "To find matching jobs, please go to the 'Matching' page and click 'Find Jobs Now'.",
        "update CV": "You can update your CV on the 'Upload CV' page by clicking 'Update CV'.",
        "help": "How can I assist you? You can ask about job matching, updating your CV, or anything related to MTOx.",
        "bye": "Goodbye! Feel free to reach out if you need further assistance.",
        "find me a job": "Sure! To find you a job, I'll need to know more about your skills and experience. Have you uploaded your CV yet?",
        "what industries are hiring": "Several industries are actively hiring, including technology, healthcare, finance, and e-commerce. What industry are you interested in?",
        "what skills are in demand": "Skills such as programming languages (Python, Java, etc.), data analysis, project management, and communication skills are often in high demand. Do you have any of these skills?",
        "what job opportunities match my skills": "To find job opportunities that match your skills, I can analyze your CV keywords and suggest relevant positions. Would you like me to do that?",
        }

# Here, the method creates a table called 'users' in the database and stores user information.
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

        # This is the login section.
        self.username_label = tk.Label(login_frame, text="Username:")
        self.username_label.pack()
        self.username_entry = tk.Entry(login_frame)
        self.username_entry.pack()

        self.password_label = tk.Label(login_frame, text="Password:")
        self.password_label.pack()
        self.password_entry = tk.Entry(login_frame, show="*")  # For security, asterisks '*' are shown for password
        self.password_entry.pack()

        self.login_button = tk.Button(login_frame, text="Login", command=self.login)
        self.login_button.pack()

        # This is the register section.
        self.new_username_label = tk.Label(login_frame, text="New Username:")
        self.new_username_label.pack()
        self.new_username_entry = tk.Entry(login_frame)
        self.new_username_entry.pack()

        self.new_password_label = tk.Label(login_frame, text="New Password:")
        self.new_password_label.pack()
        self.new_password_entry = tk.Entry(login_frame, show="*")
        self.new_password_entry.pack()

        self.age_label = tk.Label(login_frame, text="Age:")
        self.age_label.pack()
        self.age_entry = tk.Entry(login_frame)
        self.age_entry.pack()

        # This is a dropdown menu for users interests.
        self.interests_label = tk.Label(login_frame, text="Interests:")
        self.interests_label.pack()
        interests_options = ["Programming", "Data Science", "Software Engineering", "Accounting", "Other"]
        self.selected_interest = tk.StringVar(login_frame)
        self.selected_interest.set(interests_options[0])
        self.interests_dropdown = tk.OptionMenu(login_frame, self.selected_interest, *interests_options)
        self.interests_dropdown.pack()

        self.register_button = tk.Button(login_frame, text="Register", command=self.register_profile)
        self.register_button.pack()

        # This is the CV page where users can add their file (PDF), update it, delete it or view it.
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

        # This is to allow users to upload a PDF file of their CV.
    def choose_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
        if file_path:
            messagebox.showinfo("File Selected", f"Selected File: {file_path}")
            self.save_cv_path(file_path)

        # This is to allow users save their CV.
    def save_cv_path(self, cv_path):
        username = self.current_username
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET cv_path=? WHERE username=?", (cv_path, username))
        self.conn.commit()

        # This is to allow users to update their CV.
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

        # This is to allow users to delete their CV.
    def delete_cv(self):
        username = self.current_username
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET cv_path=NULL WHERE username=?", (username,))
        self.conn.commit()
        messagebox.showinfo("CV Deleted", "CV path successfully removed from the database.")

        # This is to allow users view their uploaded CV.
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

        # This method reads the jobs keywords from the jobs.csv file, parses them and stores them in a dictionary so that it can be analysed and processed later.
    def load_job_keywords(self):
        job_keywords = {}

        # This opens the jobs.csv file for reading and creates a CSV reader object.
        with open('jobs.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            # This goes over each row in the CSV file, extracts the job ID from the column, extracts and processes the keywords from the keyword column and stores them in a list
            for row in reader:
                job_id = row['jobs_id']
                keywords = [kw.strip() for kw in row[' keywords'].split(',')]
                job_keywords[job_id] = keywords

        print(f"Loaded Job Keywords: {job_keywords}")

        return job_keywords

        # This method extracts the keywords from the users CV using PyPDF2 and spaCy for NLP processing.
    def extract_keywords_from_pdf(self, pdf_path):
        # Check if the PDF file path is valid. If the file is not found, an error message will be displayed.
        if pdf_path is None or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "CV file not found.")
            return []
        
        # Here, I am initialising an empty set to store the extracted keywords
        keywords = set()

        # Here, the PDF file opens in binary read mode, reads the file (pdfreader object)
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            # Goes through each page in the PDF, gets the page object for the current page, extracts content and processes the extracted text using spaCy's NLP pipeline.
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                doc = self.nlp(text)

            # Here, it goes over each token in the processed text, checks if the token is not a stop word or punctuation and add the lowercase text of the token to the keywords set.
                for token in doc:
                    if not token.is_stop and not token.is_punct:
                        keywords.add(token.text.lower())

        return list(keywords)

    def match_jobs_to_keywords(self, cv_keywords):
        # This loads job keywords from the database.
        jobs_keywords = self.load_job_keywords()

        # This initalises a dictionary where matching jobs will be stored.
        matching_jobs = {}

        for job_id, job_keywords in jobs_keywords.items():
            # This combines the user CV keywords and job keywords into documents.
            documents = [", ".join(cv_keywords), ", ".join(job_keywords)]

            # This then converts documents to vectors using CountVectorizer.
            count_vectorizer = CountVectorizer()
            sparse_matrix = count_vectorizer.fit_transform(documents)

            # This is to calculate cosine similarity between the users CV and job keywords.
            cosine_sim = cosine_similarity(sparse_matrix)

            # This gets the similarity score between the users CV and job keywords.
            similarity_score = cosine_sim[0][1]

            # This prints the job ID and similarity score for debugging
            print(f"Job ID: {job_id}")
            # print(f"User CV Keywords: {cv_keywords}")
            # print(f"Job Keywords: {job_keywords}")
            print(f"Similarity Score: {similarity_score}")

            # Here, if the similarity score is above a certain threshold, then it should be considered a matching job
            if similarity_score > 0.1:  # The threshold can be adjusted as needed, for now I have put 0.1
                matching_jobs[job_id] = similarity_score

        return matching_jobs

        # This is for the GUI of the job matching page.
    def display_matching_jobs(self, matching_frame, matching_jobs):
        jobs_label = tk.Label(matching_frame, text="Matching Jobs:")
        jobs_label.pack()

        for job_id, _ in matching_jobs.items():
            job_name = self.get_job_name(job_id)
            if job_name:
                job_label_text = f"{job_name}"
                job_label = tk.Label(matching_frame, text=job_label_text, fg="blue", cursor="hand2")
                job_label.bind("<Button-1>", lambda event, id=job_id: self.show_job_details(event, id))
                job_label.pack()

        # This checks to see if the "Find Jobs Now" button exists already, if not then it adds it.
        find_jobs_buttons = matching_frame.winfo_children()
        find_jobs_button_exists = any(isinstance(child, tk.Button) and child["text"] == "Find Jobs Now" for child in find_jobs_buttons)

        if not find_jobs_button_exists:
            find_jobs_button = tk.Button(matching_frame, text="Find Jobs Now", command=self.find_jobs)
            find_jobs_button.pack()

    def get_job_name(self, job_id):
        # This opens the jobs.csv file for reading and creates a csv object.
        with open('jobs.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            # This goes over each row in the csv file, and checks if jobs_id in the current row matches the given job_id. 
            for row in reader:
                if row['jobs_id'] == job_id:
                    return row['jobs_id']
        return None

    def find_jobs(self):
        matching_frame = None
        # Here it goes through notebook children to find the Matching tab.
        for child in self.notebook.winfo_children():
            # If the matching tab is found, assign matching_frame to the current child and exit loop.
            if self.notebook.tab(child)['text'] == "Matching":
                matching_frame = child
                break
            # The matching_frame now contains the frame for displaying matching jobs.

        if matching_frame:
            # This gets the current user's CV path.
            cv_path = self.get_current_cv_path()

            if not cv_path or not os.path.exists(cv_path):
                messagebox.showinfo("No CV", "No valid CV found.")
                return

            # Here, keywords are extracted from the user's CV.
            cv_keywords = self.extract_keywords_from_pdf(cv_path)
            print(f"Extracted Keywords: {cv_keywords}")

            # The jobs are matched based on keywords.
            matching_jobs = self.match_jobs_to_keywords(cv_keywords)

            # This is a print out of the matching jobs for debugging.
            print("Matching Jobs:", matching_jobs)

            # This is to display the matching jobs and inform the user if no matching jobs are found or the page isn't found.
            if matching_jobs:
                self.display_matching_jobs(matching_frame, matching_jobs)
            else:
                messagebox.showinfo("No Matching Jobs", "No jobs matching your CV were found.")
        else:
            messagebox.showinfo("Page Not Found", "Matching page not found.")

            # This page which will match users to jobs.
    def create_matching_page(self):
        matching_frame = ttk.Frame(self.notebook)
        self.notebook.add(matching_frame, text="Matching")
        self.notebook.pack(expand=1, fill="both") 

        matching_label = tk.Label(matching_frame, text="Click below to see matching jobs.")
        matching_label.pack()

        find_jobs_button = tk.Button(matching_frame, text="Find Jobs Now", command=self.find_and_display_jobs)
        find_jobs_button.pack()

        logout_button = tk.Button(matching_frame, text="Logout", command=self.logout)
        logout_button.pack()

    def find_and_display_jobs(self):
        matching_frame = None
        for child in self.notebook.winfo_children():
            if self.notebook.tab(child)['text'] == "Matching":
                matching_frame = child
                break

        if matching_frame:
            # This gets the current user's CV path.
            cv_path = self.get_current_cv_path()

            if not cv_path or not os.path.exists(cv_path):
                messagebox.showinfo("No CV", "No valid CV found.")
                return

            # This extract keywords from the user's CV and matches jobs based on keywords.
            cv_keywords = self.extract_keywords_from_pdf(cv_path)
            print(f"Extracted Keywords: {cv_keywords}")

            matching_jobs = self.match_jobs_to_keywords(cv_keywords)

            # This prints out the matching jobs for debugging.
            print("Matching Jobs:", matching_jobs)

            # Below is a display for the matching jobs.
            if matching_jobs:
                # Below clears existing labels in the frame.
                for child in matching_frame.winfo_children():
                    child.destroy()
                self.display_matching_jobs(matching_frame, matching_jobs)
            else:
                messagebox.showinfo("No Matching Jobs", "No jobs matching your CV were found.")
        else:
            messagebox.showinfo("Page Not Found", "Matching page not found.")

    def show_job_details(self, event, job_id):
        # This retrieves the URL associated with the job ID and opens it in the default web browser.
        job_url = self.get_job_url(job_id)

        if job_url:
            webbrowser.open_new(job_url)
        else:
            messagebox.showwarning("Job Details", "Not found. Please try again later.")

    def get_job_url(self, job_id):
        #  Dictionary mapping job titles to their corresponding URLs.
         job_urls = {
            "Summer Analyst": "https://www.linkedin.com/jobs/view/3907451744",
            "Corporate Finance Specialist": "https://www.linkedin.com/jobs/view/3900527088",
            "Cloud Engineer (Summer)": "https://www.linkedin.com/jobs/view/3902610321",
            "Undergraduate Data Scientists Industrial Placement": "https://www.gradcracker.com/hub/839/ipsos-jarmany/work-placement-internship/59959/junior-analyst-university-industrial-placement",
            "Data Science Graduate": "https://www.linkedin.com/jobs/view/3905877045",
            "Technical Web Analyst": "https://www.linkedin.com/jobs/view/3907579224",
            "Business Analyst": "https://www.linkedin.com/jobs/view/3906000258",
            "Junior Business Analyst": "https://www.linkedin.com/jobs/view/3888080805",
            "2024 Information Technology Summer Internship Programme": "https://www.linkedin.com/jobs/view/3839793758",
            "Software Engineer Intern": "https://www.linkedin.com/jobs/view/3879272174",
            "Graduate Software Engineer": "https://www.linkedin.com/jobs/view/3892353241",
            "Software Engineer Intern": "https://www.linkedin.com/jobs/view/3881620345",
            "Software Development Engineer (Summer) ": "https://www.linkedin.com/jobs/view/3911961620",
            "Junior Financial Accountant": "https://www.linkedin.com/jobs/view/3838045425",
            "Assistant Accountant": "https://www.linkedin.com/jobs/view/3907783530",
            "Data Science Researcher": "https://www.linkedin.com/jobs/view/3902598941",
         }
         return job_urls.get(job_id, None)
    
        # This is a chatbot page
    def create_chatbot_page(self):
        chatbot_frame = ttk.Frame(self.notebook)
        self.notebook.add(chatbot_frame, text="Chatbot")

        # This creates a scrolled text widget to display chat messages.
        self.chat_display = scrolledtext.ScrolledText(chatbot_frame, wrap=tk.WORD, width=40, height=20)
        self.chat_display.pack(expand=True, fill="both")

        # This creates an entry widget for user input and creates button to send messages to the chatbot.
        self.chat_entry = tk.Entry(chatbot_frame)
        self.chat_entry.pack(fill="x")

        send_button = tk.Button(chatbot_frame, text="Send", command=self.send_message)
        send_button.pack()

        logout_button = tk.Button(chatbot_frame, text="Logout", command=self.logout)
        logout_button.pack()
    
    def send_message(self):
        # This gets the message entered by the user from the chat entry and converts it to lowercase.
        message = self.chat_entry.get().lower()  
        self.chat_entry.delete(0, tk.END)  

        # This gets the response to the user's message from the chatbot_responses dictionary.
        response = self.chatbot_responses.get(message, "I'm sorry, I didn't understand that.")

        # This displays the user's message and the chatbots response in the chat display.
        self.chat_display.insert(tk.END, "You: " + message + "\n")
        self.chat_display.insert(tk.END, "MTO: " + response + "\n")
        self.chat_display.see(tk.END)


        # This is a logout page
    def create_logout_page(self):
        logout_frame = ttk.Frame(self.notebook)
        self.notebook.add(logout_frame, text="Logout")

        logout_button = tk.Button(logout_frame, text="Logout", command=self.logout)
        logout_button.pack()


    def logout(self):
        # Removes all the pages except for the login and register page once user is logged out.
        for page in self.notebook.winfo_children()[1:]:
            self.notebook.forget(page)

        # This clears the username and password entry fields.
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
    
        self.pages_created = False
        
        # This returns to the login/register page.
        self.notebook.select(0)

    def login(self):
        # This gets the user input.
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Here, the entered password is hashed.
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # This authenticates the user.
        if self.authenticate(username, hashed_password):
            messagebox.showinfo("Login", "Login successful!")
            # Store the current username
            self.current_username = username
            self.create_pages_after_login()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

        # This authenticates the user by executing a SQL query to check if the provided username and hashed password match any records in the database.
    def authenticate(self, username, hashed_password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        return cursor.fetchone() is not None
    
        # This is to register the user when they create a profile.
    def register_profile(self):
        # This allows the tool to get user input and validates the input.
        new_username = self.new_username_entry.get()
        new_password = self.new_password_entry.get()
        age = self.age_entry.get()
        selected_interest = self.selected_interest.get()

        if not new_username or not new_password:
            messagebox.showerror("Error", "Username and password are required.")
            return

        # This hashes the password before storing.
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

        # This is to get the CV file path and test user registration.
        cv_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
        
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (username, password, age, interests, cv_path) VALUES (?, ?, ?, ?, ?)",
            (new_username, hashed_password, age, selected_interest, cv_path if cv_path else None))
        self.conn.commit()

        messagebox.showinfo("Registration", "Registration successful!") 
        self.create_pages_after_login()

    def create_pages_after_login(self):
        # After a successful login or registration, the gui will create the additional pages.
        if not self.pages_created:
            self.create_upload_cv_page()
            self.create_matching_page()
            self.create_chatbot_page()
            self.create_logout_page()
            # This sets the flag to True after creating the pages.
            self.pages_created = True
        # This redirects users to the CV page as soon as they are logged in.
        self.notebook.select(1)

    def get_current_cv_path(self):
        # This gets the username of the current user and executes a SQL query to retrieve the CV path for the current user from the database.
        username = self.current_username
        cursor = self.conn.cursor()
        cursor.execute("SELECT cv_path FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else ""

    # This is the entry point of the application by creating a Tkinter root window.
if __name__ == "__main__":
    root = tk.Tk()
    app = MTO(root)
    root.mainloop()

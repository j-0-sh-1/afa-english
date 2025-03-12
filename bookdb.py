import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pymongo import MongoClient

# MongoDB connection setup
#MONGO_URI = ("mongodb+srv://joshuailangovansamuel:HHXm1xKAsKxZtQ6I@"
#             "cluster0.pbvcd.mongodb.net/fuel_records?retryWrites=true&w=majority&appName=Cluster0")

import os
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://joshuailangovansamuel:<default_password>@cluster0.pbvcd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

client = MongoClient(MONGO_URI)
db = client["afa-english"]  # Database name
collection = db["assignment"]  # Collection name

# Helper functions to load data from MongoDB
def load_books():
    books = list(collection.find({"type": "book"}))
    for book in books:
        book.pop("_id", None)  # Remove MongoDB's _id field for pandas
    return pd.DataFrame(books) if books else pd.DataFrame(columns=["Title", "Author", "Start_Date", "End_Date", "Total_Pages", "Pages_Read", "Hours_Spent"])

def load_words():
    words = list(collection.find({"type": "word"}))
    for word in words:
        word.pop("_id", None)
    return pd.DataFrame(words) if words else pd.DataFrame(columns=["Word", "Meaning"])

def load_notes():
    notes = list(collection.find({"type": "note"}))
    for note in notes:
        note.pop("_id", None)
    return pd.DataFrame(notes) if notes else pd.DataFrame(columns=["Date", "Book_Title", "Note"])

# Load initial data
books_df = load_books()
words_df = load_words()
notes_df = load_notes()

# Streamlit App
st.title("Student Reading Tracker")

# Sidebar Navigation
menu = ["Add Book", "New Words", "Note Making", "Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Add Book":
    st.subheader("Add a New Book")
    with st.form(key="book_form"):
        title = st.text_input("Book Title")
        author = st.text_input("Author Name")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        total_pages = st.number_input("Total Pages", min_value=1)
        pages_read = st.number_input("Pages Read So Far", min_value=0, max_value=total_pages)
        hours_spent = st.number_input("Hours Spent", min_value=0.0)
        submit = st.form_submit_button("Add Book")
        
        if submit:
            new_book = {
                "type": "book",
                "Title": title,
                "Author": author,
                "Start_Date": start_date.isoformat(),
                "End_Date": end_date.isoformat(),
                "Total_Pages": total_pages,
                "Pages_Read": pages_read,
                "Hours_Spent": hours_spent
            }
            collection.insert_one(new_book)
            books_df = load_books()  # Refresh data
            st.success("Book added successfully!")

elif choice == "New Words":
    st.subheader("Learn New Words")
    word = st.text_input("Enter a New Word")
    if word:
        meaning = st.text_input(f"Meaning of '{word}'")
        if st.button("Save Word"):
            new_word = {
                "type": "word",
                "Word": word,
                "Meaning": meaning
            }
            collection.insert_one(new_word)
            words_df = load_words()  # Refresh data
            st.success(f"'{word}' added with meaning!")
    st.write("Learned Words:", words_df)

elif choice == "Note Making":
    st.subheader("Daily Reading Notes")
    with st.form(key="note_form"):
        date = st.date_input("Date", value=datetime.today())
        book_title = st.selectbox("Book Title", books_df["Title"].tolist())
        note = st.text_area("What did you read today?")
        submit = st.form_submit_button("Save Note")
        
        if submit:
            new_note = {
                "type": "note",
                "Date": date.isoformat(),
                "Book_Title": book_title,
                "Note": note
            }
            collection.insert_one(new_note)
            notes_df = load_notes()  # Refresh data
            st.success("Note saved!")
    st.write("Your Notes:", notes_df)

elif choice == "Dashboard":
    st.subheader("Reading Progress Dashboard")
    total_books = len(books_df)
    total_pages = books_df["Pages_Read"].sum()
    total_words = len(words_df)
    total_hours = books_df["Hours_Spent"].sum()
    presentations = st.number_input("Presentations Submitted", min_value=0, value=0)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Books Read", total_books)
    col2.metric("Pages Finished", int(total_pages))
    col3.metric("New Words", total_words)
    col4.metric("Hours Spent", round(total_hours, 2))
    col5.metric("Presentations", presentations)
    
    today_pages = st.number_input("Pages read today", min_value=0)
    daily_goal = 300
    if today_pages < daily_goal:
        st.warning(f"Alert: You need to read {daily_goal - today_pages} more pages today!")
    
    # Convert Start_Date to datetime for filtering
    books_df["Start_Date"] = pd.to_datetime(books_df["Start_Date"])
    week_ago = datetime.today() - timedelta(days=7)
    month_ago = datetime.today() - timedelta(days=30)
    
    weekly_books = books_df[books_df["Start_Date"] >= week_ago]
    monthly_books = books_df[books_df["Start_Date"] >= month_ago]
    
    st.write("Weekly Progress:")
    st.write(f"Books: {len(weekly_books)}, Pages: {weekly_books['Pages_Read'].sum()}")
    st.write("Monthly Progress:")
    st.write(f"Books: {len(monthly_books)}, Pages: {monthly_books['Pages_Read'].sum()}")
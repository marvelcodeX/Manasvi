
import os
import uuid
import datetime
import sqlite3
import requests
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, session, jsonify
import openai
import pandas as pd
import plotly.express as px
import io
import base64
from functools import wraps
from rag_utils import load_knowledge_base, query_knowledge

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")

# API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Load knowledge base once
kb_data = load_knowledge_base("knowledge_base.txt")

DATABASE = "manasvi.db"

# ------------------ DB Init ------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS mood_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    mood TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    role TEXT,
                    content TEXT,
                    conversation_id TEXT
                )""")
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ------------------ Mood Functions ------------------
def save_mood(mood):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO mood_logs (date, mood) VALUES (?, ?)", (str(datetime.date.today()), mood))
    conn.commit()
    conn.close()

def get_moods_df():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT * FROM mood_logs", conn)
    conn.close()
    return df

def plot_mood_graph(df):
    if df.empty:
        return None
    fig = px.histogram(df, x="date", color="mood", title="Mood Over Time")
    img_bytes = fig.to_image(format="png")
    encoded = base64.b64encode(img_bytes).decode()
    return f"data:image/png;base64,{encoded}"

# ------------------ Chat History ------------------
def save_message(role, content, conversation_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (date, role, content, conversation_id) VALUES (?, ?, ?, ?)",
                (str(datetime.date.today()), role, content, conversation_id))
    conn.commit()
    conn.close()

def get_chat_history(conversation_id, limit=10):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT role, content FROM chat_history WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
                (conversation_id, limit * 2))
    rows = c.fetchall()
    conn.close()
    chat_messages = list(reversed([{"role": role, "content": content} for role, content in rows]))

    system_message = {
        "role": "system",
        "content": (
            "Namaste, I’m Manasvi — your empathetic mental health assistant from India, here to support you with kindness, understanding, and culturally rooted care every step of the way."
        )
    }
    return [system_message] + chat_messages

def get_all_conversations():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        SELECT conversation_id, MIN(date) as start_date
        FROM chat_history
        GROUP BY conversation_id
        ORDER BY MAX(id) DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

# ------------------ Groq Integration ------------------
def create_prompt(user_input, kb_snippet):
    return f"""You are Manasvi, a supportive and culturally aware Indian wellness chatbot.
Respond to the user's input with empathy and suggest relevant Indian wellness practices.

Relevant knowledge:
{kb_snippet}

User Input: {user_input}
Chatbot Response:"""

def get_groq_response_with_history(kb_snippet=None, user_input=None, conversation_id=None):
    messages = get_chat_history(conversation_id, limit=5)
    if user_input and kb_snippet:
        prompt = create_prompt(user_input, kb_snippet)
        messages.append({"role": "user", "content": prompt})
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7,
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Groq Error] {e}")
        return "Sorry, there was an error reaching the chatbot service."

# ------------------ Decorators ------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------ ROUTES ------------------

# Home (redirects based on login status)
@app.route("/")
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username = ?", (username,))
            row = c.fetchone()
            conn.close()

            if row and row[0] == password:
                session['user'] = username
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials")
        except sqlite3.Error as e:
            flash(f"Database error: {e}")

    return render_template('login.html')

# Signup (protected)
@app.route('/signup', methods=['GET', 'POST'])
# @login_required  <-- REMOVE THIS LINE
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Account created! Please log in.")
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.")
        finally:
            conn.close()

        return redirect(url_for('login'))
    return render_template('signup.html')
# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Dashboard / Main Chat UI
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    init_db()
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    conversation_id = session['conversation_id']

    user_input = ""
    response = ""
    kb_snippet = ""
    mood_graph = None

    if request.method == "POST":
        mode = request.form.get("mode")

        if "save_mood" in request.form:
            mood = request.form.get("mood")
            if mood:
                save_mood(mood)
                flash("Mood saved successfully!", "success")

        if mode == "Text":
            user_input = request.form.get("user_input_text", "").strip()
        elif mode == "Voice":
            user_input = request.form.get("user_input", "").strip()

        if user_input:
            kb_snippet = query_knowledge(user_input, kb_data)
            save_message("user", user_input, conversation_id)
            response = get_groq_response_with_history(kb_snippet, user_input, conversation_id)
            save_message("assistant", response, conversation_id)

    df = get_moods_df()
    mood_graph = plot_mood_graph(df)
    chat_history = get_chat_history(conversation_id, limit=10)
    conversations = get_all_conversations()

    return render_template(
        "index.html",
        user_input=user_input,
        response=response,
        mood_graph=mood_graph,
        kb_snippet=kb_snippet,
        chat_history=chat_history,
        conversations=conversations,
        current_cid=conversation_id
    )

# Start New Chat
@app.route("/new_chat")
@login_required
def new_chat():
    session['conversation_id'] = str(uuid.uuid4())
    flash("Started a new chat!", "success")
    return redirect(url_for("dashboard"))

# Load Previous Chat
@app.route("/chat/<cid>")
@login_required
def load_chat(cid):
    session['conversation_id'] = cid
    return redirect(url_for("dashboard"))

# Mood Tracker Page
@app.route('/mood-tracker')
@login_required
def mood_tracker():
    return render_template('mood_tracker.html')

# Ekanta Nilaya Page
@app.route('/ekanta-nilaya')
@login_required
def ekanta_nilaya():
    return render_template('ekanta_nilaya.html')

# Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# Run Server
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8000)
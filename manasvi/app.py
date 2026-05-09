import sqlite3
import uuid
from functools import wraps

from flask import Flask, current_app, flash, jsonify, redirect, render_template, request, session, url_for

from .config import Config
from .db import (
    authenticate_user,
    create_user,
    get_chat_history,
    get_conversations,
    get_moods,
    get_user_by_id,
    init_db,
    save_message,
    save_mood,
)
from .rag import KnowledgeBase
from .services import get_chatbot_response


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    init_db(app.config["DATABASE_PATH"])
    app.knowledge_base = KnowledgeBase(
        app.config["KNOWLEDGE_BASE_PATH"],
        enable_vector=app.config["ENABLE_VECTOR_RAG"],
    )

    register_routes(app)
    return app


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(current_app.config["DATABASE_PATH"], user_id)


def register_routes(app):
    @app.route("/")
    def home():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip().lower()
            password = request.form.get("password", "")
            user = authenticate_user(app.config["DATABASE_PATH"], username, password)
            if user:
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["conversation_id"] = str(uuid.uuid4())
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.", "error")
        return render_template("auth.html", mode="login")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form.get("username", "").strip().lower()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm", "")

            if len(username) < 3:
                flash("Username must be at least 3 characters.", "error")
            elif len(password) < 8:
                flash("Password must be at least 8 characters.", "error")
            elif password != confirm:
                flash("Passwords do not match.", "error")
            else:
                try:
                    create_user(app.config["DATABASE_PATH"], username, email, password)
                    user = authenticate_user(app.config["DATABASE_PATH"], username, password)
                    session.clear()
                    session["user_id"] = user["id"]
                    session["username"] = user["username"]
                    session["conversation_id"] = str(uuid.uuid4())
                    flash("Account created.", "success")
                    return redirect(url_for("dashboard"))
                except sqlite3.IntegrityError:
                    flash("That username is already taken.", "error")

        return render_template("auth.html", mode="signup")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/dashboard", methods=["GET", "POST"])
    @login_required
    def dashboard():
        user = current_user()
        session.setdefault("conversation_id", str(uuid.uuid4()))
        conversation_id = session["conversation_id"]

        if request.method == "POST":
            user_input = request.form.get("message", "").strip()
            if user_input:
                history = get_chat_history(app.config["DATABASE_PATH"], user["id"], conversation_id, limit=10)
                kb_snippet = app.knowledge_base.query(user_input)
                save_message(app.config["DATABASE_PATH"], user["id"], conversation_id, "user", user_input)
                response = get_chatbot_response(app.config, history, user_input, kb_snippet)
                save_message(app.config["DATABASE_PATH"], user["id"], conversation_id, "assistant", response)
                return redirect(url_for("dashboard"))

        return render_template(
            "dashboard.html",
            user=user,
            active_page="chat",
            conversations=get_conversations(app.config["DATABASE_PATH"], user["id"]),
            current_cid=conversation_id,
            chat_history=get_chat_history(app.config["DATABASE_PATH"], user["id"], conversation_id, limit=30),
            kb_ready=app.knowledge_base.ready,
        )

    @app.route("/new-chat")
    @app.route("/new_chat")
    @login_required
    def new_chat():
        session["conversation_id"] = str(uuid.uuid4())
        return redirect(url_for("dashboard"))

    @app.route("/chat/<conversation_id>")
    @login_required
    def load_chat(conversation_id):
        session["conversation_id"] = conversation_id
        return redirect(url_for("dashboard"))

    @app.route("/mood-tracker")
    @login_required
    def mood_tracker():
        user = current_user()
        return render_template(
            "mood_tracker.html",
            user=user,
            active_page="mood",
            conversations=get_conversations(app.config["DATABASE_PATH"], user["id"]),
            current_cid=session.get("conversation_id"),
        )

    @app.route("/api/moods", methods=["GET", "POST"])
    @login_required
    def moods_api():
        user = current_user()
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            mood = data.get("mood", "").strip()
            note = data.get("note", "").strip()
            if not mood:
                return jsonify({"error": "Mood is required."}), 400
            save_mood(app.config["DATABASE_PATH"], user["id"], mood, note)
            return jsonify({"status": "ok"})

        return jsonify(get_moods(app.config["DATABASE_PATH"], user["id"], limit=30))

    @app.route("/ekanta-nilaya")
    @login_required
    def ekanta_nilaya():
        user = current_user()
        return render_template(
            "ekanta_nilaya.html",
            user=user,
            active_page="ekanta",
            conversations=get_conversations(app.config["DATABASE_PATH"], user["id"]),
            current_cid=session.get("conversation_id"),
        )

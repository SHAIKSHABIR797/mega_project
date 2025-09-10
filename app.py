from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "your_very_secret_key_here"

# ------------------------
# Mail configuration
# ------------------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "shaikshabir967@gmail.com"  # replace
app.config["MAIL_PASSWORD"] = "youdzmmhlzrmfqdf"     # replace
app.config["MAIL_DEFAULT_SENDER"] = "your_email@gmail.com"

mail = Mail(app)

# ------------------------
# Database connection
# ------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="student_app"
    )

# ------------------------
# Home
# ------------------------
@app.route("/")
def home():
    return redirect(url_for("login"))

# ------------------------
# Register
# ------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if len(username) < 3 or len(password) < 6:
            flash("Username min 3 chars & password min 6 chars", "danger")
            return redirect(url_for("register"))

        if "@" not in email or "." not in email:
            flash("Enter a valid email address.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                        (username, email, hashed_password)
                    )
                    conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except mysql.connector.Error as err:
            if err.errno == 1062:
                flash("Username or Email already taken.", "danger")
            else:
                flash(f"Database error: {err}", "danger")

    return render_template("register.html")

# ------------------------
# Login
# ------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        try:
            with get_db_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                    user = cursor.fetchone()
        except:
            flash("Database error", "danger")
            return redirect(url_for("login"))

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome, {user['username']} 🎉", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

# ------------------------
# Dashboard
# ------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, event_name, event_type, event_date, event_time, registration_type 
                    FROM events WHERE user_id = %s ORDER BY event_date DESC
                """, (session["user_id"],))
                user_events = cursor.fetchall()
    except:
        user_events = []

    events = ["Cricket", "Volleyball", "Kabaddi", "Dance"]
    return render_template("dashboard.html", username=session["username"], events=events, user_events=user_events)

# ------------------------
# Register / Edit Event
# ------------------------
@app.route("/register_event", methods=["GET", "POST"])
def register_event():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    event_name = request.args.get("event", "").strip()
    event_id = request.args.get("event_id")
    event = None

    # Edit mode
    if event_id:
        try:
            with get_db_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT * FROM events WHERE id=%s AND user_id=%s",
                        (event_id, session["user_id"])
                    )
                    event = cursor.fetchone()
        except:
            flash("Database error", "danger")

    if request.method == "POST":
        event_type = request.form.get("event_type", "").strip()
        event_date = request.form.get("event_date", "").strip()
        event_time = request.form.get("event_time", "").strip()
        registration_type = request.form.get("registration_type", "Individual")

        if not event_type or not event_date or not event_time:
            flash("Fill all fields.", "danger")
            return redirect(request.url)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    if event:  # Update
                        cursor.execute("""
                            UPDATE events
                            SET event_type=%s, event_date=%s, event_time=%s, registration_type=%s
                            WHERE id=%s AND user_id=%s
                        """, (event_type, event_date, event_time, registration_type, event["id"], session["user_id"]))
                        flash("Event updated successfully!", "success")
                    else:  # Insert
                        cursor.execute("""
                            INSERT INTO events (user_id, event_name, event_type, event_date, event_time, registration_type)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (session["user_id"], event_name, event_type, event_date, event_time, registration_type))
                        flash("Event registered successfully!", "success")
                    conn.commit()
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Database error: {e}", "danger")

    return render_template("register_event.html", event=event, event_name=event_name)

# ------------------------
# Edit Event button redirect
# ------------------------
@app.route("/edit_event/<int:event_id>", methods=["GET"])
def edit_event(event_id):
    return redirect(url_for("register_event", event_id=event_id))

# ------------------------
# Delete Event
# ------------------------
@app.route("/delete_event/<int:event_id>", methods=["POST"])
def delete_event(event_id):
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM events WHERE id=%s AND user_id=%s", (event_id, session["user_id"]))
                conn.commit()
        flash("Event deleted successfully!", "info")
    except:
        flash("Database error.", "danger")
    return redirect(url_for("dashboard"))

# ------------------------
# Logout
# ------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# ------------------------
if __name__ == "__main__":
    app.run(debug=True)

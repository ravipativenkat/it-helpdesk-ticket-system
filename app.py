from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

DB_NAME = "helpdesk.db"

app = Flask(__name__)
app.secret_key = "replace_with_any_random_secret_key"  # for sessions

# --- Simple hard-coded users for demo (DO NOT USE IN REAL PROD) ---
USERS = {
    "admin": "admin123",
    "support": "support123"
}

def get_connection():
    return sqlite3.connect(DB_NAME)


# ---------- PUBLIC: RAISE TICKET ----------
@app.route("/")
def new_ticket():
    return render_template("new_ticket.html")


@app.route("/submit", methods=["POST"])
def submit_ticket():
    name = request.form["name"]
    email = request.form["email"]
    department = request.form["department"]
    category = request.form["category"]
    priority = request.form["priority"]
    description = request.form["description"]

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tickets (name, email, department, category, priority, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, department, category, priority, description))
    conn.commit()
    conn.close()

    return redirect(url_for("ticket_submitted"))


@app.route("/submitted")
def ticket_submitted():
    return render_template("submitted.html")


# ---------- ADMIN LOGIN / LOGOUT ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("list_tickets"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("user", None)
    return redirect(url_for("admin_login"))


# ---------- ADMIN: VIEW / UPDATE TICKETS ----------
def require_login():
    if "user" not in session:
        return False
    return True


@app.route("/tickets")
def list_tickets():
    if not require_login():
        return redirect(url_for("admin_login"))

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, department, category, priority, status, created_at
        FROM tickets
        ORDER BY created_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return render_template("tickets.html", tickets=rows, user=session.get("user"))


@app.route("/update_status", methods=["POST"])
def update_status():
    if not require_login():
        return redirect(url_for("admin_login"))

    ticket_id = request.form["ticket_id"]
    new_status = request.form["status"]

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
    conn.commit()
    conn.close()

    return redirect(url_for("list_tickets"))


if __name__ == "__main__":
    app.run(debug=True)

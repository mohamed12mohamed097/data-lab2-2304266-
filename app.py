import os
import bcrypt
import pymysql
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
    )


@app.route("/")
def home():
    return "Flask is working"


@app.route("/dbtest")
def dbtest():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM users")
            row = cur.fetchone()
        return f"Connected to MySQL. Users in table: {row['n']}"
    finally:
        conn.close()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", errors={}, form={})

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    # same rules as the JavaScript
    errors = {}
    if name == "":
        errors["name"] = "Name is required"
    if email == "":
        errors["email"] = "Email is required"
    if password == "":
        errors["password"] = "Password is required"
    if confirm == "":
        errors["confirm_password"] = "Confirm password is required"
    elif password != "" and password != confirm:
        errors["confirm_password"] = "Passwords do not match"

    if errors:
        return render_template("register.html", errors=errors, form=request.form)

    # hash the password (never store the password itself)
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                (email, name, password_hash),
            )
            new_id = cur.lastrowid
        conn.commit()
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        if e.args[0] == 1062:  # duplicate email (UNIQUE)
            errors["email"] = "Email Already Exists"
            return render_template("register.html", errors=errors, form=request.form)
        raise
    finally:
        conn.close()

    # log the user in, then redirect so refresh does not resend the form
    session["user_id"] = new_id
    session["name"] = name
    return redirect("/todos")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", errors={}, form={})

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    errors = {}
    if email == "":
        errors["email"] = "Email is required"
    if password == "":
        errors["password"] = "Password is required"

    if errors:
        return render_template("login.html", errors=errors, form=request.form)

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, name, password_hash FROM users WHERE email = %s",
                (email,),
            )
            user = cur.fetchone()
    finally:
        conn.close()

    # same message for unknown email and wrong password
    if user is None or not bcrypt.checkpw(
        password.encode("utf-8"), user["password_hash"].encode("utf-8")
    ):
        errors["login"] = "Invalid email or password"
        return render_template("login.html", errors=errors, form=request.form)

    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    return redirect("/todos")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def render_todos(error=None, form_title="", error_id=None):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC",
                (session["user_id"],),
            )
            items = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        "todos.html",
        items=items,
        name=session["name"],
        error=error,
        form_title=form_title,
        error_id=error_id,
    )


@app.route("/todos")
def todos():
    if "user_id" not in session:
        return redirect("/login")
    return render_todos()


@app.route("/todos/add", methods=["POST"])
def add_todo():
    if "user_id" not in session:
        return redirect("/login")

    title = request.form.get("title", "").strip()

    error = None
    if title == "":
        error = "Title is required"
    elif len(title) > 200:
        error = "Title is too long (200 characters at most)"

    if error:
        return render_todos(error=error, form_title=request.form.get("title", ""))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO todos (user_id, title) VALUES (%s, %s)",
                (session["user_id"], title),
            )
        conn.commit()
    finally:
        conn.close()

    return redirect("/todos")

def validate_title(raw):
    title = raw.strip()
    if title == "":
        return title, "Title is required"
    if len(title) > 200:
        return title, "Title is too long (200 characters at most)"
    return title, None


@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
def edit_todo(todo_id):
    if "user_id" not in session:
        return redirect("/login")

    title, error = validate_title(request.form.get("title", ""))
    if error:
        return render_todos(error=error, error_id=todo_id)

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
                (title, todo_id, session["user_id"]),
            )
        conn.commit()
    finally:
        conn.close()
    return redirect("/todos")


@app.route("/todos/<int:todo_id>/done", methods=["POST"])
def done_todo(todo_id):
    if "user_id" not in session:
        return redirect("/login")

    is_done = 1 if request.form.get("is_done") == "1" else 0

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
                (is_done, todo_id, session["user_id"]),
            )
        conn.commit()
    finally:
        conn.close()
    return redirect("/todos")


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
def delete_todo(todo_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
                (todo_id, session["user_id"]),
            )
        conn.commit()
    finally:
        conn.close()
    return redirect("/todos")

if __name__ == "__main__":
    app.run(debug=True)
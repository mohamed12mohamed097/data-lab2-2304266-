import os
import pymysql
from dotenv import load_dotenv
from flask import Flask

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


if __name__ == "__main__":
    app.run(debug=True)
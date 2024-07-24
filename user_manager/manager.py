from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import os

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY")


def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"))
    return conn


@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT au.user_id, ub.balance, ub.images_generated AS images_generated
        FROM allowed_users au
        LEFT JOIN user_balances ub ON au.user_id = ub.user_id
        ORDER BY au.user_id
    """)
    allowed_users = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', allowed_users=allowed_users)


@app.route('/allow', methods=['POST'])
def allow_user():
    user_id = request.form.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM allowed_users WHERE user_id = %s", (user_id,))
        existing_user = cur.fetchone()
        if existing_user:
            flash(f"User {user_id} is already allowed.", 'info')
        else:
            cur.execute("INSERT INTO allowed_users (user_id) VALUES (%s)", (user_id,))
            conn.commit()
            flash(f"User {user_id} has been allowed.", 'success')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('index'))


@app.route('/disable', methods=['POST'])
def disable_user():
    user_id = request.form.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM allowed_users WHERE user_id = %s", (user_id,))
        existing_user = cur.fetchone()
        if not existing_user:
            flash(f"User {user_id} is not currently allowed.", 'info')
        else:
            cur.execute("DELETE FROM allowed_users WHERE user_id = %s", (user_id,))
            conn.commit()
            flash(f"User {user_id} access revoked.", 'warning')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('index'))


@app.route('/set_balance', methods=['POST'])
def set_balance():
    user_id = request.form.get('user_id')
    balance = request.form.get('balance')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM allowed_users WHERE user_id = %s", (user_id,))
        existing_user = cur.fetchone()
        if not existing_user:
            flash(f"User {user_id} is not currently allowed.", 'info')
        else:
            cur.execute(
                """
                INSERT INTO user_balances (user_id, balance, images_generated)
                VALUES (%s, %s, 0)
                ON CONFLICT (user_id)
                DO UPDATE SET balance = EXCLUDED.balance
                """,
                (user_id, balance)
            )
            conn.commit()
            flash(f"User {user_id} balance has been set to {balance}.", 'success')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

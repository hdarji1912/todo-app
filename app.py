from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
import os
from flask_bcrypt import Bcrypt
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this')
bcrypt = Bcrypt(app)

# Database configuration driven purely by standard Environment Variables
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'port': os.environ.get('MYSQL_PORT', '3306'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DB', 'mydb')
}


def get_db_connection():
    """Create and return database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def init_db():
    """Initialize database and create tables if they don't exist"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Ensure core users system table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ensure core todos application table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    task VARCHAR(255) NOT NULL,
                    status ENUM('pending', 'completed') DEFAULT 'pending',
                    deleted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL DEFAULT NULL
                )
            """)
            
            # Ensure background event auditing table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    action VARCHAR(50) NOT NULL,
                    ip_address VARCHAR(45),
                    username_attempted VARCHAR(50),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            connection.commit()
            print("Database schemas initialized successfully!")
        except Error as e:
            print(f"Error initializing database tables: {e}")
        finally:
            cursor.close()
            connection.close()


# ─────────────────────────────────────────────
# SECURITY DECORATOR
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────
# AUDIT HELPER
# ─────────────────────────────────────────────

def log_auth_action(action, user_id=None, username_attempted=None):
    """Insert an execution tracking record into auth_logs"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            ip = request.remote_addr
            cursor.execute(
                "INSERT INTO auth_logs (user_id, action, ip_address, username_attempted) VALUES (%s, %s, %s, %s)",
                (user_id, action, ip, username_attempted)
            )
            connection.commit()
        except Error as e:
            print(f"Error writing to execution logs: {e}")
        finally:
            cursor.close()
            connection.close()


# ─────────────────────────────────────────────
# AUTHENTICATION ENGINE
# ─────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user profile"""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password_hash)
                )
                connection.commit()
                flash('Account created! Please log in.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                if 'Duplicate entry' in str(e):
                    flash('Username or email already exists.', 'error')
                else:
                    flash(f'Error creating account: {str(e)}', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed.', 'error')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate via session cookie engine"""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('login.html')

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user and bcrypt.check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    log_auth_action('login', user_id=user['id'], username_attempted=username)
                    flash(f"Welcome back, {user['username']}!", 'success')
                    return redirect(url_for('index'))
                else:
                    log_auth_action('failed', username_attempted=username)
                    flash('Invalid username or password.', 'error')
            except Error as e:
                flash(f'Error during runtime check: {str(e)}', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Clear authorization state tracking"""
    log_auth_action('logout', user_id=session.get('user_id'), username_attempted=session.get('username'))
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# CORE TASK OPERATIONS (Scoped to User ID)
# ─────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    """Display active tasks owned by current user"""
    connection = get_db_connection()
    todos = []

    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM todos WHERE user_id = %s AND deleted = FALSE ORDER BY created_at DESC",
                (session['user_id'],)
            )
            todos = cursor.fetchall()
        except Error as e:
            flash(f'Error fetching database entries: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Database connection failed', 'error')

    return render_template('index.html', todos=todos)


@app.route('/add', methods=['POST'])
@login_required
def add_todo():
    """Store item matching the current author profile link"""
    task = request.form.get('task')

    if not task:
        flash('Task cannot be empty!', 'error')
        return redirect(url_for('index'))

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO todos (task, user_id) VALUES (%s, %s)",
                (task, session['user_id'])
            )
            connection.commit()
            flash('Todo added successfully!', 'success')
        except Error as e:
            flash(f'Insertion Error: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Database connection failed', 'error')

    return redirect(url_for('index'))


@app.route('/complete/<int:todo_id>')
@login_required
def complete_todo(todo_id):
    """Mark target document record instance completed"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE todos SET status = 'completed' WHERE id = %s AND user_id = %s",
                (todo_id, session['user_id'])
            )
            connection.commit()
            flash('Todo marked as completed!', 'success')
        except Error as e:
            flash(f'State Update Failure: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Database connection failed', 'error')

    return redirect(url_for('index'))


@app.route('/rename/<int:todo_id>', methods=['POST'])
@login_required
def rename_todo(todo_id):
    """Modify content title field context value safety mapping"""
    new_task = request.form.get('new_task', '').strip()

    if not new_task:
        flash('Task name cannot be empty!', 'error')
        return redirect(url_for('index'))

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE todos SET task = %s WHERE id = %s AND user_id = %s",
                (new_task, todo_id, session['user_id'])
            )
            connection.commit()
            flash('Task renamed successfully!', 'success')
        except Error as e:
            flash(f'Mutation Error: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Database connection failed', 'error')

    return redirect(url_for('index'))


@app.route('/delete/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    """Flag row data visibility out of interface scope"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE todos SET deleted = TRUE, deleted_at = NOW() WHERE id = %s AND user_id = %s",
                (todo_id, session['user_id'])
            )
            connection.commit()
            flash('Todo deleted successfully!', 'success')
        except Error as e:
            flash(f'Deletion error status: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Database connection failed', 'error')

    return redirect(url_for('index'))


@app.route('/deleted')
@login_required
def view_deleted():
    """Access flagged record table rows list"""
    connection = get_db_connection()
    deleted_todos = []

    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM todos WHERE deleted = TRUE AND user_id = %s ORDER BY deleted_at DESC",
                (session['user_id'],)
            )
            deleted_todos = cursor.fetchall()
        except Error as e:
            flash(f'Fetch Error: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()

    return render_template('deleted.html', todos=deleted_todos)


# ─────────────────────────────────────────────
# INFRASTRUCTURE HEALTH STATUS
# ─────────────────────────────────────────────

@app.route('/health')
def health():
    """Direct status probe engine verification"""
    connection = get_db_connection()
    if connection:
        connection.close()
        return {'status': 'healthy', 'database': 'connected'}, 200
    return {'status': 'unhealthy', 'database': 'disconnected'}, 503


if __name__ == '__main__':
    init_db()  # Setup basic table layers safely on runtime launch execution
    app.run(host='0.0.0.0', port=5000, debug=True)
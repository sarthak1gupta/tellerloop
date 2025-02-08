from flask import Flask, render_template, jsonify, request, abort, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os, glob

ALLOWED_IPS = ['127.0.0.1', '192.168.1.7', '172.17.13.219']
ADMIN_USERS = ['admin1', 'admin2', 'admin3']
REGULAR_USERS = ['user1', 'user2', 'user3']
STAFF_USERS = ['staff1', 'staff2', 'staff3']

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = 'your_secret_key'  # Change this to a secure random key
CORS(app, resources={r"/": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DATABASE = 'lan_monitoring.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT NOT NULL UNIQUE,
                       password TEXT NOT NULL,
                       role TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS messages
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       sender TEXT NOT NULL,
                       receiver TEXT NOT NULL,
                       message TEXT NOT NULL,
                       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                       cp1 BOOLEAN DEFAULT 0,
                       cp2 BOOLEAN DEFAULT 0,
                       cp3 BOOLEAN DEFAULT 0,
                       cp4 BOOLEAN DEFAULT 0)''')

        # Sample users with hashed passwords
        sample_users = [
            ('admin', generate_password_hash('admin_password'), 'admin'),
            ('user1', generate_password_hash('user1_password'), 'regular'),
            ('user2', generate_password_hash('user2_password'), 'regular'),
            ('staff1', generate_password_hash('staff1_password'), 'staff'),
            ('staff2', generate_password_hash('staff2_password'), 'staff'),
            ('staff3', generate_password_hash('staff3_password'), 'staff')
        ]

        for username, hashed_password, role in sample_users:
            db.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
                       (username.strip(), hashed_password, role.strip()))
        
        db.commit()

def authenticate_user(username, password):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
    user = cur.fetchone()
    conn.close()

    if user:
        print(f"User fetched from DB: {dict(user)}")
        db_password = user['password']

        # Use `check_password_hash` to compare the entered password with the hashed password
        if check_password_hash(db_password, password):
            print(f"Authentication successful for user: {username}")
            return user['role']
        else:
            print("Password mismatch")
    else:
        print("User not found in DB")
    
    return None

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Debug statements
        print(f"Received username: {username}")
        print(f"Received password: {password}")

        user_role = authenticate_user(username, password)

        # Debug statement
        print(f"User role fetched: {user_role}")
        if user_role:
            session['user'] = username
            session['role'] = user_role
            if user_role == 'admin':
                return redirect(url_for('admin_control'))
            elif user_role == 'staff':
                return redirect(url_for('staff_monitoring'))
            else:
                return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/index')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user=session['user'])

@app.route('/admin_control')
def admin_control():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_control.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/staff_monitoring')
def staff_monitoring():
    if 'user' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    return render_template('staff.html')
  
@app.route('/api/get_client_ip')
def get_client_ip():
    return jsonify({'ip': request.remote_addr})

@app.route('/api/network_architecture')
def get_network_architecture():
    try:
        directory = os.path.dirname(__file__)
        json_files = glob.glob(os.path.join(directory, "network_architecture*.json"))
        
        if not json_files:
            return jsonify({'error': 'No architecture files found'}), 404
        
        latest_file = max(json_files, key=os.path.getmtime)
        with open(latest_file, 'r') as json_file:
            data = json.load(json_file)
        
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'Network architecture file not found'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format in network architecture file'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('send_message')
def handle_send_message(data):
    # Save message to database
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO messages 
        (sender, receiver, message, cp1, cp2, cp3, cp4) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['sender'], 
        data['receiver'], 
        data['message'], 
        data.get('cp1', False), 
        data.get('cp2', False), 
        data.get('cp3', False), 
        data.get('cp4', False)
    ))
    message_id = cur.lastrowid
    conn.commit()

    # Get the full message details to broadcast
    cur.execute('SELECT * FROM messages WHERE id = ?', (message_id,))
    message = cur.fetchone()
    conn.close()

    # Broadcast to all connected clients (including staff monitoring page)
    emit('new_message', {
        'id': message_id,
        'sender': data['sender'],
        'receiver': data['receiver'],
        'message': data['message'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'cp1': data.get('cp1', False),
        'cp2': data.get('cp2', False),
        'cp3': data.get('cp3', False),
        'cp4': data.get('cp4', False)
    }, broadcast=True)
    
@app.route('/api/logs')
def get_logs():
    node = request.args.get('node')
    if not node:
        return jsonify([])
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get logs where the node is either sender or receiver
    cur.execute('''
        SELECT sender, receiver, message, timestamp, cp1, cp2, cp3, cp4 
        FROM messages 
        WHERE sender = ? OR receiver = ?
        ORDER BY timestamp DESC
    ''', (node, node))
    
    logs = []
    for row in cur.fetchall():
        logs.append({
            'sender': row['sender'],
            'receiver': row['receiver'],
            'message': row['message'],
            'timestamp': row['timestamp'],
            'cp1': bool(row['cp1']),
            'cp2': bool(row['cp2']),
            'cp3': bool(row['cp3']),
            'cp4': bool(row['cp4'])
        })
    
    conn.close()
    return jsonify(logs)

@socketio.on('hello_packet')
def handle_hello_packet(data):
    emit('hello_packet', data, broadcast=True)

@socketio.on('hello_ack')
def handle_hello_ack(data):
    emit('hello_ack', data, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    emit('station_disconnect', {'node': session.get('username')}, broadcast=True)

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
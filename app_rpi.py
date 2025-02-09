from flask import Flask, render_template, jsonify, request, abort, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os, glob
from datetime import datetime, timezone
import threading
import time
from collections import defaultdict
import ssl

# Global variables for tracking
heartbeat_threads = {}
connected_stations = {}  # username -> ip
station_sids = {}  # username -> sid
sid_stations = {}  # sid -> username
station_heartbeats = defaultdict(float) 
HEARTBEAT_TIMEOUT = 30 

ALLOWED_IPS = ['127.0.0.1', '192.168.1.10', '172.17.13.219']
ADMIN_USERS = ['admin1', 'admin2', 'admin3']
REGULAR_USERS = ['user1', 'user2', 'user3']
STAFF_USERS = ['staff1', 'staff2', 'staff3']

# Create SSL context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.urandom(24)  # Generate a secure random key
CORS(app, resources={r"/": {"origins": "*"}})
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   async_mode='threading',
                   ssl_context=ssl_context)

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
        db.execute('''CREATE TABLE IF NOT EXISTS path_checkpoints (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      source TEXT NOT NULL,
                      destination TEXT NOT NULL,
                      path TEXT NOT NULL,
                      checkpoint_count INTEGER NOT NULL,
                      UNIQUE(source, destination))''')

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

@app.route('/api/path_checkpoints')
def get_path_checkpoints():
    source = request.args.get('source')
    destination = request.args.get('destination')
    
    if not source or not destination:
        return jsonify({'error': 'Source and destination required'}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT path, checkpoint_count
        FROM path_checkpoints 
        WHERE source = ? AND destination = ?
    ''', (source, destination))
    
    result = cur.fetchone()
    conn.close()
    
    if result:
        return jsonify({
            'path': result['path'].split(','),
            'checkpoint_count': result['checkpoint_count']
        })
    
    return jsonify({'error': 'Path not found'}), 404

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


@app.route('/api/check_ip', methods=['GET'])
def check_ip():
    user_ip = request.remote_addr
    return jsonify({'is_allowed': user_ip in ALLOWED_IPS})

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

@app.route('/api/all_logs')
def get_all_logs():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    conn = get_db()
    cur = conn.cursor()
    
    # Get all logs ordered by timestamp descending (newest first)
    cur.execute('''
        SELECT sender, receiver, message, timestamp, cp1, cp2, cp3, cp4 
        FROM messages 
        ORDER BY timestamp DESC
    ''')
    
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

@socketio.on('join')
def handle_join(data):
    username = data['username']
    ip = data['ip']
    sid = request.sid
    
    # Store station connection data
    connected_stations[username] = ip
    station_sids[username] = sid
    sid_stations[sid] = username
    
    # Send the current list of connected stations to the newly joined station
    emit('update_connected_stations', list(connected_stations.keys()))
    
    # Notify all other clients about the new connection
    emit('station_joined', {'node': username, 'ip': ip}, broadcast=True)
    
@socketio.on('hello_packet')
def handle_hello_packet(data):
    sender = data['node']
    if sender in connected_stations:
        # Broadcast hello packet to all other stations
        emit('hello_packet', data, broadcast=True, include_self=False)

@socketio.on('hello_ack')
def handle_hello_ack(data):
    sender = data['sender']
    receiver = data['receiver']
    
    if sender in connected_stations and receiver in connected_stations:
        # Forward acknowledgment to the specific receiver
        receiver_sid = station_sids.get(receiver)
        if receiver_sid:
            emit('hello_ack', data, room=receiver_sid)

@socketio.on('heartbeat')
def handle_heartbeat(data):
    username = data['node']
    timestamp = data['timestamp']
    
    if username in connected_stations:
        station_heartbeats[username] = timestamp
        # Broadcast heartbeat to all other stations
        emit('heartbeat', data, broadcast=True, include_self=False)     

def cleanup_inactive_stations():
    current_time = time.time()
    inactive_threshold = 15  # 15 seconds timeout
    
    for username, last_heartbeat in list(station_heartbeats.items()):
        if current_time - last_heartbeat > inactive_threshold:
            # Station is inactive, clean up its data
            sid = station_sids.get(username)
            if sid:
                del sid_stations[sid]
                del station_sids[username]
            del connected_stations[username]
            del station_heartbeats[username]
            
            # Notify all clients about the disconnection
            emit('station_left', {'node': username}, broadcast=True)
            emit('update_connected_stations', list(connected_stations.keys()), broadcast=True)       

@socketio.on('hello_ack')
def handle_hello_ack(data):
    emit('hello_ack', data, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    username = sid_stations.get(sid)
    
    if username:
        # Clean up all station tracking data
        if username in connected_stations:
            del connected_stations[username]
        if username in station_sids:
            del station_sids[username]
        if sid in sid_stations:
            del sid_stations[sid]
        if username in station_heartbeats:
            del station_heartbeats[username]
        
        # Notify all clients about the disconnection
        emit('station_left', {'node': username}, broadcast=True)
        
        # Send updated station list to all connected clients
        emit('update_connected_stations', list(connected_stations.keys()), broadcast=True)
    
@socketio.on('start_packet_animation')
def handle_start_animation(data):
    """Handle the start of packet animation between nodes"""
    # Validate required data
    required_fields = ['sender', 'receiver', 'message', 'messageId', 'timestamp']
    if not all(field in data for field in required_fields):
        return {'error': 'Missing required fields'}, 400
    
    # Create initial message record with no checkpoints
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO messages 
            (sender, receiver, message, timestamp, cp1, cp2, cp3, cp4) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['sender'],
            data['receiver'],
            data['message'],
            data['timestamp'],
            False,  # cp1
            False,  # cp2
            False,  # cp3
            False   # cp4
        ))
        message_id = cur.lastrowid
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {'error': 'Database error'}, 500
    finally:
        conn.close()

    # Broadcast animation start to all clients
    emit('start_packet_animation', {
        'sender': data['sender'],
        'receiver': data['receiver'],
        'messageId': message_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, broadcast=True)

@socketio.on('checkpoint_reached')
def handle_checkpoint(data):
    """Handle packet reaching a checkpoint"""
    required_fields = ['sender', 'receiver', 'checkpoint', 'messageId']
    if not all(field in data for field in required_fields):
        return {'error': 'Missing required fields'}, 400

    checkpoint_num = data['checkpoint']
    if not 1 <= checkpoint_num <= 4:
        return {'error': 'Invalid checkpoint number'}, 400

    # Update the message record with checkpoint status
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(f'''
            UPDATE messages 
            SET cp{checkpoint_num} = 1 
            WHERE id = ? AND sender = ? AND receiver = ?
        ''', (data['messageId'], data['sender'], data['receiver']))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {'error': 'Database error'}, 500
    finally:
        conn.close()

    # Broadcast checkpoint reached to all clients
    emit('checkpoint_reached', {
        'sender': data['sender'],
        'receiver': data['receiver'],
        'checkpoint': checkpoint_num,
        'messageId': data['messageId'],
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, broadcast=True)

@socketio.on('animation_complete')
def handle_animation_complete(data):
    """Handle completion of packet animation"""
    required_fields = ['sender', 'receiver', 'messageId']
    if not all(field in data for field in required_fields):
        return {'error': 'Missing required fields'}, 400

    # Verify all checkpoints were reached
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('''
            SELECT cp1, cp2, cp3, cp4 
            FROM messages 
            WHERE id = ? AND sender = ? AND receiver = ?
        ''', (data['messageId'], data['sender'], data['receiver']))
        
        result = cur.fetchone()
        if not result:
            return {'error': 'Message not found'}, 404

        # Verify all checkpoints are True
        all_checkpoints_reached = all([
            result['cp1'], result['cp2'], 
            result['cp3'], result['cp4']
        ])

        if not all_checkpoints_reached:
            print("Warning: Animation completed but not all checkpoints were reached")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {'error': 'Database error'}, 500
    finally:
        conn.close()

    # Broadcast animation completion to all clients
    emit('animation_complete', {
        'sender': data['sender'],
        'receiver': data['receiver'],
        'messageId': data['messageId'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'success': all_checkpoints_reached
    }, broadcast=True)

if __name__ == '__main__':
    init_db()
    
    # Configure SSL context
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        ssl_context.load_cert_chain('cert.pem', 'key.pem')
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5000, 
                    debug=True, 
                    ssl_context=ssl_context,
                    allow_unsafe_werkzeug=True)
    else:
        # Fallback to non-SSL for development
        print("Warning: Running without SSL. Generate certificates for production use.")
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5000, 
                    debug=True,
                    allow_unsafe_werkzeug=True)
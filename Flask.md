# Network Monitoring System
## Technical Documentation v1.0

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Technical Architecture](#2-technical-architecture)
3. [Database Architecture](#3-database-architecture)
4. [Authentication System](#4-authentication-system)
5. [Route Handlers](#5-route-handlers)
6. [WebSocket Implementation](#6-websocket-implementation)
7. [Network Communication Protocol](#7-network-communication-protocol)
8. [Security Implementation](#8-security-implementation)
9. [System Configuration](#9-system-configuration)
10. [Deployment Guidelines](#10-deployment-guidelines)
11. [Maintenance and Monitoring](#12-maintenance-and-monitoring)

## 1. System Overview

### 1.1 Purpose
The Network Monitoring System is a Flask-based web application designed to provide real-time monitoring and communication capabilities between network stations. It supports user authentication, real-time message tracking, and visualization of network packet movements.

### 1.2 Core Functionalities
- User authentication with role-based access control
- Real-time network station monitoring
- Inter-station communication with message tracking
- Packet movement visualization with checkpoint tracking
- Heartbeat-based connection monitoring
- Comprehensive logging system

### 1.3 Technology Stack
- Backend Framework: Flask
- Database: SQLite
- Real-time Communication: Flask-SocketIO
- Cross-Origin Support: Flask-CORS
- Frontend Support: Static files and templates
- Authentication: Custom SHA-256 implementation

## 2. Technical Architecture

### 2.1 Application Structure
```plaintext
root/
├── static/
├── templates/
├── database/
│   └── lan_monitoring.db
├── network_architecture*.json
└── app.py
```

### 2.2 Core Dependencies
```python
flask==2.0.1
flask-socketio==5.1.1
flask-cors==3.0.10
sqlite3
hashlib
threading
```

### 2.3 Global Variables
```python
ALLOWED_IPS = ['127.0.0.1', '192.168.1.10', '172.17.13.219']
ADMIN_USERS = ['admin1', 'admin2', 'admin3']
REGULAR_USERS = ['user1', 'user2', 'user3']
STAFF_USERS = ['staff1', 'staff2', 'staff3']
HEARTBEAT_TIMEOUT = 30
```

## 3. Database Architecture

### 3.1 Database Schema

#### 3.1.1 Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
```

#### 3.1.2 Messages Table
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cp1 BOOLEAN DEFAULT 0,
    cp2 BOOLEAN DEFAULT 0,
    cp3 BOOLEAN DEFAULT 0,
    cp4 BOOLEAN DEFAULT 0
)
```

#### 3.1.3 Path Checkpoints Table
```sql
CREATE TABLE path_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    path TEXT NOT NULL,
    checkpoint_count INTEGER NOT NULL,
    UNIQUE(source, destination)
)
```

### 3.2 Database Functions

#### 3.2.1 Database Connection
```python
def get_db():
    """
    Establishes database connection with row factory
    
    Returns:
        sqlite3.Connection: Database connection object
    
    Usage:
        conn = get_db()
        try:
            # Database operations
        finally:
            conn.close()
    """
```

#### 3.2.2 Database Initialization
```python
def init_db():
    """
    Initializes database schema and populates sample data
    
    Operations:
    1. Creates required tables if they don't exist
    2. Populates sample users with secure password hashing
    3. Handles SQLite errors with proper logging
    
    Error Handling:
        - Logs database creation errors
        - Logs user insertion errors
        - Implements proper transaction management
    """
```

## 4. Authentication System

### 4.1 Password Management

#### 4.1.1 Password Hashing
```python
def generate_password_hash(password):
    """
    Generates secure password hash using SHA-256
    
    Args:
        password (str): Plain text password
    
    Returns:
        str: Formatted hash string (sha256$salt$hash)
    
    Security Features:
        - Random 16-byte salt generation
        - SHA-256 hashing algorithm
        - Salt-hash combination
    """
```

#### 4.1.2 Password Verification
```python
def check_password_hash(stored_hash, provided_password):
    """
    Verifies provided password against stored hash
    
    Args:
        stored_hash (str): Stored password hash
        provided_password (str): Password to verify
    
    Returns:
        bool: True if password matches, False otherwise
    
    Security:
        - Constant-time comparison
        - Error handling for invalid hash formats
    """
```

### 4.2 User Authentication
```python
def authenticate_user(username, password):
    """
    Authenticates user credentials
    
    Args:
        username (str): User's username
        password (str): User's password
    
    Returns:
        str|None: User's role if authenticated, None otherwise
    
    Process:
        1. Retrieves user record from database
        2. Verifies password hash
        3. Returns user role on success
    """
```

## 5. Route Handlers

### 5.1 Authentication Routes

#### 5.1.1 Login Route
```python
@app.route('/', methods=['GET', 'POST'])
def login():
    """
    Handles user login
    
    Methods:
        GET: Returns login page
        POST: Processes login attempt
    
    Form Parameters:
        username (str): User's username
        password (str): User's password
    
    Returns:
        GET: login.html template
        POST: Redirects to appropriate dashboard or returns error
    
    Security:
        - Input validation
        - Session management
        - Role-based routing
    """
```
### 5.2 Protected Routes

#### 5.2.1 Index Route
```python
@app.route('/index')
def index():
    """
    Regular user dashboard
    
    Authentication:
        Requires valid user session
    
    Returns:
        Template: index.html with user context
        Redirect: Login page if unauthorized
    
    Template Context:
        user (str): Current username
    """
```

#### 5.2.2 Admin Control Route
```python
@app.route('/admin_control')
def admin_control():
    """
    Administrative dashboard
    
    Authentication:
        Requires valid session
        Requires admin role
    
    Returns:
        Template: admin_control.html
        Redirect: Login page if unauthorized
    
    Security:
        - Role verification
        - Session validation
    """
```

### 5.3 API Routes

#### 5.3.1 Network Architecture
```python
@app.route('/api/network_architecture')
def get_network_architecture():
    """
    Retrieves current network topology
    
    Process:
        1. Locates most recent architecture JSON file
        2. Parses and validates JSON content
        3. Returns network topology data
    
    Returns:
        JSON Response:
            success: Network architecture data
            error: Error message with appropriate status code
    
    Error Handling:
        404: No architecture files found
        500: JSON parsing error
    """
```

#### 5.3.2 Log Retrieval
```python
@app.route('/api/logs')
def get_logs():
    """
    Retrieves message logs for specific node
    
    Query Parameters:
        node (str): Station identifier
    
    Returns:
        JSON Array:
            sender (str): Message sender
            receiver (str): Message recipient
            message (str): Message content
            timestamp (str): ISO format timestamp
            cp1-cp4 (bool): Checkpoint flags
    
    Database:
        - Queries messages table
        - Filters by sender/receiver
        - Orders by timestamp descending
    """
```

## 6. WebSocket Implementation

### 6.1 Connection Management

#### 6.1.1 Station Join Handler
```python
@socketio.on('join')
def handle_join(data):
    """
    Manages new station connections
    
    Parameters:
        data (dict):
            username (str): Station identifier
            ip (str): Station IP address
    
    Operations:
        1. Records station connection details
        2. Updates connection mappings
        3. Broadcasts connection status
        4. Notifies other stations
    
    State Updates:
        - connected_stations
        - station_sids
        - sid_stations
    """
```

#### 6.1.2 Heartbeat Handler
```python
@socketio.on('heartbeat')
def handle_heartbeat(data):
    """
    Processes station heartbeat signals
    
    Parameters:
        data (dict):
            node (str): Station identifier
            timestamp (float): Current timestamp
    
    Operations:
        1. Updates station last-seen time
        2. Broadcasts heartbeat to other stations
        3. Triggers cleanup of inactive stations
    
    Timeout:
        HEARTBEAT_TIMEOUT (30 seconds)
    """
```

### 6.2 Message Handling

#### 6.2.1 Message Transmission
```python
@socketio.on('send_message')
def handle_send_message(data):
    """
    Processes inter-station messages
    
    Parameters:
        data (dict):
            sender (str): Source station
            receiver (str): Destination station
            message (str): Message content
            cp1-cp4 (bool): Checkpoint flags
    
    Database Operations:
        1. Creates message record
        2. Records timestamp
        3. Sets initial checkpoint states
    
    Broadcasting:
        - Emits to all connected clients
        - Includes message ID and timestamp
    """
```

## 7. Network Communication Protocol

### 7.1 Packet Animation System

#### 7.1.1 Animation Initialization
```python
@socketio.on('start_packet_animation')
def handle_start_animation(data):
    """
    Initiates packet movement visualization
    
    Required Fields:
        sender (str): Source station
        receiver (str): Destination station
        message (str): Packet content
        messageId (str): Unique identifier
        timestamp (str): Start time
    
    Validation:
        - Verifies required fields
        - Validates station existence
        - Checks message format
    
    Database:
        - Creates animation record
        - Initializes checkpoint states
    """
```

#### 7.1.2 Checkpoint Processing
```python
@socketio.on('checkpoint_reached')
def handle_checkpoint(data):
    """
    Tracks packet progression through network
    
    Parameters:
        sender (str): Source station
        receiver (str): Destination station
        checkpoint (int): Checkpoint number (1-4)
        messageId (str): Message identifier
    
    Validation:
        - Validates checkpoint number
        - Verifies message existence
        - Checks station permissions
    
    Database Updates:
        - Sets checkpoint flag
        - Updates timestamp
    """
```

### 7.2 Connection Monitoring

#### 7.2.1 Station Cleanup
```python
def cleanup_inactive_stations():
    """
    Removes inactive network stations
    
    Process:
        1. Checks last heartbeat timestamps
        2. Identifies inactive stations
        3. Removes connection records
        4. Updates connected station list
    
    Thresholds:
        inactive_threshold: 15 seconds
    
    Notifications:
        - Broadcasts station removal
        - Updates station lists
    """
```

## 8. Security Implementation

### 8.1 Access Control
```python
def check_ip():
    """
    Validates client IP addresses
    
    Verification:
        - Checks against ALLOWED_IPS list
        - Validates IP format
        - Logs access attempts
    
    Returns:
        JSON Response:
            is_allowed (bool): Access status
    """
```

### 8.2 Session Management
```python
# Session Configuration
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
```

## 9. System Configuration

### 9.1 Environment Variables
```python
DEBUG = True  # Development mode
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000  # Application port
DATABASE = 'lan_monitoring.db'  # Database file
```

### 9.2 CORS Configuration
```python
CORS(app, resources={r"/": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
```

## 10. Deployment Guidelines

### 10.1 Production Considerations
1. Disable debug mode
2. Configure secure session cookie
3. Implement proper logging
4. Set up database backups
5. Configure SSL/TLS
6. Implement rate limiting
7. Set up monitoring

### 10.2 Performance Optimization
1. Database connection pooling
2. WebSocket connection limits
3. Message queue implementation
4. Caching strategy
5. Load balancing configuration



## 11. Maintenance and Monitoring

### 11.1 Regular Maintenance Tasks
1. Database cleanup
2. Log rotation
3. Session cleanup
4. Security updates
5. Performance monitoring

### 11.2 Monitoring Metrics
1. Active connections
2. Message throughput
3. Database performance
4. Error rates
5. Response times

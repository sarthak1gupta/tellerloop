# LAN Monitoring System Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Technical Architecture](#technical-architecture)
3. [Frontend Components](#frontend-components)
4. [Core Functionality](#core-functionality)
5. [Network Communication](#network-communication)
6. [User Interface Elements](#user-interface-elements)
7. [Event Handling](#event-handling)
8. [Utility Functions](#utility-functions)

## 1. System Overview

The LAN Monitoring System is a web-based application designed to monitor and manage communication between different stations in a local area network. It provides real-time monitoring, message sending capabilities, and logging of communication events between stations.

### Key Features
- Real-time station status monitoring
- Inter-station messaging system
- Message delivery tracking with checkpoints
- Communication logs with timestamp recording
- Admin controls for master log viewing
- Automatic station detection and connection

## 2. Technical Architecture

### Dependencies
- Socket.IO (v4.7.2) for real-time communication
- Toastify.js (v1.12.0) for notifications
- Standard HTML5, CSS3, and JavaScript

### Network Architecture
The system uses a client-server architecture with the following components:
- WebSocket server for real-time updates
- RESTful API endpoints for data retrieval
- Browser-based client interface

## 3. Frontend Components

### 3.1 Socket Connection Management
```javascript
const socket = io();
```
Establishes the WebSocket connection for real-time communication.

### 3.2 State Management
```javascript
let currentNode = '';
let currentNodeIP = '';
let networkArchitecture = null;
let nodeIPMap = new Map();
let connectedStations = new Map();
let pendingAcknowledgments = new Set();
```

These variables maintain the application state:
- `currentNode`: Currently selected station
- `currentNodeIP`: IP address of current station
- `networkArchitecture`: Network topology configuration
- `nodeIPMap`: Mapping between station IDs and IP addresses
- `connectedStations`: Status of all network stations
- `pendingAcknowledgments`: Tracks unacknowledged hello packets

## 4. Core Functionality

### 4.1 Initialization
```javascript
document.addEventListener('DOMContentLoaded', async function() {
    // ... initialization code
});
```
Handles initial setup:
1. Loads network architecture
2. Initializes node selections
3. Attempts automatic station selection
4. Checks IP permissions for admin features

### 4.2 Station Management

#### joinRoom Function
```javascript
function joinRoom() {
    // ... station joining code
}
```
Manages station connection process:
1. Updates current node information
2. Updates UI elements
3. Emits join event to server
4. Initiates hello packet broadcast
5. Retrieves communication logs

#### autoSelectStation Function
```javascript
async function autoSelectStation() {
    // ... auto-selection code
}
```
Automatically selects appropriate station based on client IP address.

### 4.3 Communication System

#### sendMessage Function
```javascript
function sendMessage() {
    // ... message sending code
}
```
Handles message transmission:
1. Generates unique message ID
2. Validates message content
3. Initiates packet animation
4. Emits message event to server

#### broadcastHelloPacket Function
```javascript
function broadcastHelloPacket() {
    // ... hello packet code
}
```
Manages station discovery process:
1. Clears pending acknowledgments
2. Updates station statuses
3. Broadcasts hello packet
4. Sets acknowledgment timeout

## 5. Network Communication

### 5.1 Socket Event Handlers

```javascript
socket.on('connect', function() {
    // ... connection handling
});

socket.on('new_message', function(data) {
    // ... message handling
});

socket.on('acknowledgment', function(data) {
    // ... acknowledgment handling
});
```

Handles various socket events:
- Connection establishment
- Message reception
- Acknowledgment processing
- Station status updates
- Animation events

### 5.2 Logging System

```javascript
async function getLogs() {
    // ... log retrieval code
}

async function getMasterLogs() {
    // ... master log retrieval code
}
```

Manages communication logs:
1. Retrieves logs from server
2. Processes and formats timestamps
3. Updates log display
4. Handles admin-specific log features

## 6. User Interface Elements

### 6.1 UI Updates

#### updateStationsList Function
```javascript
function updateStationsList() {
    // ... station list update code
}
```
Manages the connected stations display:
1. Clears existing list
2. Creates station elements
3. Updates status indicators

#### updateReceiverDropdown Function
```javascript
function updateReceiverDropdown() {
    // ... dropdown update code
}
```
Updates message destination options:
1. Clears existing options
2. Adds connected stations
3. Disables disconnected stations

### 6.2 Progress Tracking

```javascript
function updateProgressBar(progress) {
    // ... progress update code
}

function updateCheckpoint(checkpointNum) {
    // ... checkpoint update code
}
```

Manages message delivery visualization:
1. Updates progress bar
2. Manages checkpoint indicators
3. Provides visual feedback

## 7. Event Handling

### 7.1 Animation Events
```javascript
socket.on('start_packet_animation', (data) => {
    // ... animation code
});
```
Manages packet animation:
1. Calculates animation path
2. Creates visual packet element
3. Animates movement between checkpoints
4. Emits checkpoint events

### 7.2 Error Handling
```javascript
function showNotification(message, type = 'info') {
    // ... notification code
}
```
Manages error and success notifications:
1. Displays toast notifications
2. Handles different message types
3. Provides visual feedback

## 8. Utility Functions

### 8.1 Time Formatting
```javascript
function formatTimestamp(timestamp) {
    // ... timestamp formatting code
}
```
Formats timestamps:
1. Converts to Indian locale
2. Uses IST timezone
3. Includes date and time

### 8.2 Helper Functions
```javascript
function getCheckpointStatus(log) {
    // ... status code
}

function resetCheckpoints() {
    // ... reset code
}
```
Various utility functions for:
1. Checkpoint status management
2. UI element reset
3. Data formatting

## Maintenance Notes

1. The system requires Socket.IO server implementation
2. Network architecture should be provided via API
3. IP address configuration should match network topology
4. Admin features require proper IP-based access control
5. Logging system depends on server-side storage


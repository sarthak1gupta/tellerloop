// Add this code to both pages' socket event listeners
socket.on('start_packet_animation', (data) => {
    // Start animation on staff page
    if (window.location.pathname.includes('staff')) {
        // Find the source and destination components
        const sourceComponent = networkComponents.get(`Station${parseInt(data.sender.slice(-1))}`);
        const destComponent = networkComponents.get(`Station${parseInt(data.receiver.slice(-1))}`);
        
        if (!sourceComponent || !destComponent) {
            console.error('Components not found:', data);
            return;
        }

        // Get component positions
        const startBounds = sourceComponent.getBoundingClientRect();
        const endBounds = destComponent.getBoundingClientRect();
        
        const pathInfo = {
            start: {
                x: startBounds.left + startBounds.width / 2,
                y: startBounds.top + startBounds.height / 2
            },
            end: {
                x: endBounds.left + endBounds.width / 2,
                y: endBounds.top + endBounds.height / 2
            },
            checkpoints: [
                { x: startBounds.left + startBounds.width * 0.25, y: (startBounds.top + endBounds.top) / 2 },
                { x: startBounds.left + startBounds.width * 0.5, y: (startBounds.top + endBounds.top) / 2 },
                { x: startBounds.left + startBounds.width * 0.75, y: (startBounds.top + endBounds.top) / 2 },
                { x: endBounds.left + endBounds.width * 0.25, y: (startBounds.top + endBounds.top) / 2 }
            ]
        };

        // Create and animate packet
        const packet = document.createElement('div');
        packet.classList.add('packet');
        document.getElementById('network-diagram').appendChild(packet);

        // Set initial position
        packet.style.left = `${pathInfo.start.x - 6}px`;
        packet.style.top = `${pathInfo.start.y - 6}px`;

        // Animation variables
        const totalDuration = 4000; // 4 seconds for complete animation
        const checkpointInterval = totalDuration / 4; // Time between checkpoints
        let startTime = null;

        function animate(timestamp) {
            if (!startTime) startTime = timestamp;
            const progress = (timestamp - startTime) / totalDuration;

            if (progress < 1) {
                // Calculate current position
                const currentPoint = calculateCurrentPoint(pathInfo, progress);
                packet.style.left = `${currentPoint.x - 6}px`;
                packet.style.top = `${currentPoint.y - 6}px`;

                // Check for checkpoint crossings
                const checkpointIndex = Math.floor(progress * 4);
                if (checkpointIndex >= 0 && checkpointIndex < 4) {
                    // Emit checkpoint reached event
                    socket.emit('checkpoint_reached', {
                        sender: data.sender,
                        receiver: data.receiver,
                        checkpoint: checkpointIndex + 1,
                        messageId: data.messageId
                    });
                }

                requestAnimationFrame(animate);
            } else {
                packet.remove();
                // Animation complete - emit event
                socket.emit('animation_complete', {
                    sender: data.sender,
                    receiver: data.receiver,
                    messageId: data.messageId
                });
            }
        }

        requestAnimationFrame(animate);
    }
});

// Add these functions to index.html
function sendMessage() {
    const receiver = document.getElementById('receiver-select').value;
    const message = document.getElementById('message-input').value;
    
    if (!message || !receiver) {
        showNotification('Please select a destination and enter a message', 'error');
        return;
    }

    const messageId = Date.now().toString();
    
    // Reset UI
    updateProgressBar(0);
    resetCheckpoints();

    // Emit start animation event
    socket.emit('start_packet_animation', {
        sender: currentNode,
        receiver,
        message,
        messageId,
        timestamp: new Date().toISOString()
    });
}

// Add these socket listeners to index.html
socket.on('checkpoint_reached', (data) => {
    if (data.sender === currentNode || data.receiver === currentNode) {
        const progress = data.checkpoint * 25;
        updateProgressBar(progress);
        updateCheckpoint(data.checkpoint);
    }
});

socket.on('animation_complete', (data) => {
    if (data.sender === currentNode) {
        // Complete the progress bar
        updateProgressBar(100);
        
        // Send the actual message
        socket.emit('send_message', {
            sender: currentNode,
            receiver: data.receiver,
            message: document.getElementById('message-input').value,
            ip: currentNodeIP,
            timestamp: new Date().toISOString(),
            cp1: true,
            cp2: true,
            cp3: true,
            cp4: true
        });

        // Reset the form
        document.getElementById('message-input').value = '';
        showNotification('Message sent successfully');
    }
});

// Helper function for calculating current animation point
function calculateCurrentPoint(pathInfo, progress) {
    const { start, end, checkpoints } = pathInfo;
    
    // If before first checkpoint
    if (progress < 0.25) {
        return interpolatePoints(start, checkpoints[0], progress * 4);
    }
    // Between checkpoints
    else if (progress < 0.5) {
        return interpolatePoints(checkpoints[0], checkpoints[1], (progress - 0.25) * 4);
    }
    else if (progress < 0.75) {
        return interpolatePoints(checkpoints[1], checkpoints[2], (progress - 0.5) * 4);
    }
    // After last checkpoint
    else {
        return interpolatePoints(checkpoints[2], end, (progress - 0.75) * 4);
    }
}

function interpolatePoints(start, end, progress) {
    return {
        x: start.x + (end.x - start.x) * progress,
        y: start.y + (end.y - start.y) * progress
    };
}

// Helper functions for index.html
function updateProgressBar(progress) {
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = `${progress}%`;
}

function updateCheckpoint(checkpointNum) {
    const checkbox = document.getElementById(`cp${checkpointNum}`);
    if (checkbox) {
        checkbox.checked = true;
    }
}

function resetCheckpoints() {
    for (let i = 1; i <= 4; i++) {
        const checkbox = document.getElementById(`cp${i}`);
        if (checkbox) {
            checkbox.checked = false;
        }
    }
}

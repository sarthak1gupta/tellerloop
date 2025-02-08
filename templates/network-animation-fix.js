// Get the actual path coordinates between two components
function getPathCoordinates(sourceComponent, destComponent) {
    const sourceBounds = sourceComponent.getBoundingClientRect();
    const destBounds = destComponent.getBoundingClientRect();
    
    // Get component centers relative to the network diagram
    const networkDiagram = document.getElementById('network-diagram');
    const diagramBounds = networkDiagram.getBoundingClientRect();
    
    const start = {
        x: sourceBounds.left + sourceBounds.width / 2 - diagramBounds.left,
        y: sourceBounds.top + sourceBounds.height / 2 - diagramBounds.top
    };
    
    const end = {
        x: destBounds.left + destBounds.width / 2 - diagramBounds.left,
        y: destBounds.top + destBounds.height / 2 - diagramBounds.top
    };

    // Calculate midpoint for perpendicular path
    const midX = (start.x + end.x) / 2;

    // Return the three key points for perpendicular path
    return {
        start,
        mid: { x: midX, y: start.y },
        midVert: { x: midX, y: end.y },
        end,
        checkpoints: [
            { x: start.x + (midX - start.x) * 0.33, y: start.y },
            { x: midX, y: start.y + (end.y - start.y) * 0.33 },
            { x: midX + (end.x - midX) * 0.33, y: end.y }
        ]
    };
}

// Calculate position at given progress along the path
function calculatePosition(pathPoints, progress) {
    const { start, mid, midVert, end } = pathPoints;
    
    if (progress <= 0.33) {
        // First segment (horizontal)
        const p = progress * 3;
        return {
            x: start.x + (mid.x - start.x) * p,
            y: start.y
        };
    } else if (progress <= 0.67) {
        // Second segment (vertical)
        const p = (progress - 0.33) * 3;
        return {
            x: mid.x,
            y: mid.y + (midVert.y - mid.y) * p
        };
    } else {
        // Third segment (horizontal)
        const p = (progress - 0.67) * 3;
        return {
            x: midVert.x + (end.x - midVert.x) * p,
            y: end.y
        };
    }
}

function animatePacket(pathInfo, messageData) {
    const networkDiagram = document.getElementById('network-diagram');
    const packet = document.createElement('div');
    packet.classList.add('packet');
    networkDiagram.appendChild(packet);

    // Get source and destination components
    const sourceComponent = networkComponents.get(messageData.sender);
    const destComponent = networkComponents.get(messageData.receiver);
    
    if (!sourceComponent || !destComponent) {
        console.error('Components not found:', messageData.sender, messageData.receiver);
        return;
    }

    // Get actual path coordinates
    const pathPoints = getPathCoordinates(sourceComponent, destComponent);
    
    // Animation variables
    const totalDuration = 4000; // 4 seconds
    let startTime = null;

    function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = (timestamp - startTime) / totalDuration;

        if (progress < 1) {
            const pos = calculatePosition(pathPoints, progress);
            
            // Update packet position
            packet.style.left = `${pos.x - 6}px`;
            packet.style.top = `${pos.y - 6}px`;

            // Emit checkpoint events at specific progress points
            const checkpointIndex = Math.floor(progress * 4);
            if (checkpointIndex >= 0 && checkpointIndex < 4) {
                socket.emit('checkpoint_reached', {
                    sender: messageData.sender,
                    receiver: messageData.receiver,
                    checkpoint: checkpointIndex + 1,
                    messageId: messageData.messageId
                });
            }

            requestAnimationFrame(animate);
        } else {
            packet.remove();
            socket.emit('animation_complete', {
                sender: messageData.sender,
                receiver: messageData.receiver,
                messageId: messageData.messageId
            });
        }
    }

    requestAnimationFrame(animate);
}

// Update the socket event listener
socket.on('start_packet_animation', (data) => {
    console.log('Animation started:', data);
    
    // Find the source and destination components
    const sourceComponent = networkComponents.get(data.sender);
    const destComponent = networkComponents.get(data.receiver);
    
    if (!sourceComponent || !destComponent) {
        console.error('Components not found:', data.sender, data.receiver);
        return;
    }

    animatePacket(null, data); // pathInfo is calculated inside animatePacket now
});

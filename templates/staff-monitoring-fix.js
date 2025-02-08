// Update the fetchAndRenderNetwork function to properly store components
async function fetchAndRenderNetwork() {
    try {
        const response = await fetch('/api/network_architecture');
        const data = await response.json();
        
        // Clear existing components
        networkComponents.clear();
        
        const diagram = document.getElementById('network-diagram');
        const wireSvg = document.getElementById('wire-svg');

        // Clear existing content
        diagram.innerHTML = '';
        diagram.appendChild(wireSvg);
        wireSvg.innerHTML = '';

        // Calculate optimal size
        const bounds = calculateOptimalDiagramSize(data.components);
        const containerWidth = diagram.clientWidth;
        const containerHeight = Math.max(600, bounds.height + 100);
        diagram.style.height = `${containerHeight}px`;
        wireSvg.setAttribute('width', containerWidth);
        wireSvg.setAttribute('height', containerHeight);

        // Render components and store them in the Map
        data.components.forEach(comp => {
            const coords = scaleCoordinates(comp.x, comp.y, bounds, containerWidth, containerHeight);
            coords.x = Math.max(80, Math.min(containerWidth - 80, coords.x));
            coords.y = Math.max(50, Math.min(containerHeight - 50, coords.y));

            const component = createNetworkComponent(comp, coords);
            diagram.appendChild(component);
            

            // Store component with its station ID
            const stationId = `${comp.id}`;
            networkComponents.set(stationId, component);
            console.log(`Stored component: ${stationId}`);
        });

        // Render connections
        data.connections.forEach(conn => {
            renderConnection(conn, wireSvg, bounds, containerWidth, containerHeight);
        });
        
        // Log stored components for debugging
        console.log('Network Components Map:', Array.from(networkComponents.entries()));
        
    } catch (error) {
        console.error('Error fetching network architecture:', error);
    }
}

// Update the packet animation event listener
socket.on('start_packet_animation', (data) => {
    console.log('Animation started:', data);
    console.log('Available components:', Array.from(networkComponents.keys()));
    
    // Find the source and destination components
    const sourceComponent = networkComponents.get(data.sender);
    const destComponent = networkComponents.get(data.receiver);
    
    if (!sourceComponent || !destComponent) {
        console.error('Components not found. Source:', data.sender, 'Dest:', data.receiver);
        console.log('Current components:', Array.from(networkComponents.entries()));
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
            { x: (startBounds.left + endBounds.left) / 2, y: (startBounds.top + endBounds.top) / 2 },
            { x: (startBounds.left + endBounds.left) * 0.6, y: (startBounds.top + endBounds.top) / 2 },
            { x: (startBounds.left + endBounds.left) * 0.8, y: (startBounds.top + endBounds.top) / 2 }
        ]
    };

    animatePacket(pathInfo, data);
});

function animatePacket(pathInfo, messageData) {
    const packet = document.createElement('div');
    packet.classList.add('packet');
    document.getElementById('network-diagram').appendChild(packet);

    // Set initial position
    packet.style.left = `${pathInfo.start.x - 6}px`;
    packet.style.top = `${pathInfo.start.y - 6}px`;

    // Animation variables
    const totalDuration = 4000; // 4 seconds
    const checkpointInterval = totalDuration / 4;
    let startTime = null;

    function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = (timestamp - startTime) / totalDuration;

        if (progress < 1) {
            const currentPoint = calculateCurrentPoint(pathInfo, progress);
            packet.style.left = `${currentPoint.x - 6}px`;
            packet.style.top = `${currentPoint.y - 6}px`;

            // Emit checkpoint events
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

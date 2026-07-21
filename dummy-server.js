import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 8080 });
let count = 0;

wss.on('connection', function connection(ws) {
  console.log('Client connected');
  ws.send(JSON.stringify({ type: 'update', count }));

  ws.on('message', function message(data) {
    try {
      const msg = JSON.parse(data);
      if (msg.type === 'increment') count++;
      if (msg.type === 'decrement' && count > 0) count--;
      
      // Broadcast to all clients
      wss.clients.forEach(client => {
        if (client.readyState === 1) { // WebSocket.OPEN
          client.send(JSON.stringify({ type: 'update', count }));
        }
      });
    } catch (e) {
      console.error('Invalid message', data);
    }
  });
});

// Simulate AI detecting a person every 5 seconds
setInterval(() => {
  count++;
  wss.clients.forEach(client => {
    if (client.readyState === 1) {
      client.send(JSON.stringify({ type: 'update', count }));
    }
  });
}, 5000);

console.log('Dummy WebSocket server running on ws://localhost:8080');

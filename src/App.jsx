import { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [count, setCount] = useState(0);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8080');
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'update') {
        setCount(data.count);
      }
    };

    return () => ws.close();
  }, []);

  const handleIncrement = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'increment' }));
    } else {
      setCount(c => c + 1); // fallback if disconnected
    }
  };

  const handleDecrement = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'decrement' }));
    } else {
      setCount(c => Math.max(0, c - 1)); // fallback
    }
  };

  return (
    <div className="counter-container">
      <div className="counter-badge">Live Event Status</div>
      <h1 className="counter-title">{count}</h1>
      <p style={{ color: '#666', marginTop: 0 }}>Total Visitors</p>
      
      <div className="counter-controls">
        <button className="btn-secondary" onClick={handleDecrement}>-1 (Koreksi)</button>
        <button className="btn-primary" onClick={handleIncrement}>+1 (Manual)</button>
      </div>
    </div>
  );
}

export default App;

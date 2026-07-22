const EVENT_ID = 1;
let trendChart = null;

function initChart() {
  const ctx = document.getElementById('trendChart').getContext('2d');
  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Pengunjung di Dalam',
          data: [],
          borderColor: '#FF7200',
          backgroundColor: 'rgba(255, 114, 0, 0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

async function fetchSummary() {
  try {
    const res = await fetch(`/api/events/${EVENT_ID}/summary`);
    const data = await res.json();
    updateMetrics(data);
  } catch (err) {
    console.error("Failed fetching summary:", err);
  }
}

async function fetchTrend() {
  try {
    const res = await fetch(`/api/events/${EVENT_ID}/trend`);
    const history = await res.json();
    if (trendChart) {
      trendChart.data.labels = history.map(h => new Date(h.timestamp).toLocaleTimeString());
      trendChart.data.datasets[0].data = history.map(h => h.current_inside);
      trendChart.update();
    }
  } catch (err) {
    console.error("Failed fetching trend:", err);
  }
}

function updateMetrics(summary) {
  document.getElementById('val-inside').innerText = summary.current_inside;
  document.getElementById('val-total-in').innerText = summary.total_in;
  document.getElementById('val-total-out').innerText = summary.total_out;
}

function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/events/${EVENT_ID}`;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateMetrics(data);
    fetchTrend();
  };

  ws.onclose = () => {
    setTimeout(initWebSocket, 3000);
  };
}

document.addEventListener('DOMContentLoaded', () => {
  initChart();
  fetchSummary();
  fetchTrend();
  initWebSocket();
});

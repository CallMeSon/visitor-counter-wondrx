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
          backgroundColor: 'rgba(255, 114, 0, 0.08)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointBackgroundColor: '#FF7200',
          pointRadius: 4,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            font: { family: 'Inter', weight: '600' }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          grid: { color: '#EAE5DD' }
        }
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
      trendChart.data.labels = history.map(h => new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
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

  if (summary.connected_cameras !== undefined) {
    const connCountEl = document.getElementById('connected-cam-count');
    const totalCountEl = document.getElementById('total-cam-count');
    const summaryConnEl = document.getElementById('cam-summary-connected');
    const summaryTotalEl = document.getElementById('cam-summary-total');

    if (connCountEl) connCountEl.innerText = summary.connected_cameras;
    if (totalCountEl) totalCountEl.innerText = summary.total_cameras || 7;
    if (summaryConnEl) summaryConnEl.innerText = summary.connected_cameras;
    if (summaryTotalEl) summaryTotalEl.innerText = summary.total_cameras || 7;
  }

  if (summary.cameras && summary.cameras.length > 0) {
    renderCamerasList(summary.cameras);
  }
}

function renderCamerasList(cameras) {
  const container = document.getElementById('cameras-container');
  if (!container) return;

  container.innerHTML = cameras.map(cam => {
    const isEntry = cam.role === 'entry';
    const roleTagClass = isEntry ? 'role-entry' : 'role-exit';
    const roleLabel = isEntry ? 'MASUK' : 'KELUAR';
    
    const isConnected = cam.is_connected;
    const statusClass = isConnected ? 'connected' : 'standby';
    const dotClass = isConnected ? 'dot-connected' : 'dot-standby';
    const statusText = isConnected ? 'CONNECTED' : 'STANDBY';

    return `
      <div class="camera-item">
        <div class="camera-header">
          <div class="camera-title">${cam.name}</div>
          <span class="role-tag ${roleTagClass}">${roleLabel}</span>
        </div>
        <div class="camera-meta">
          <div class="status-badge ${statusClass}">
            <span class="dot-status ${dotClass}"></span> ${statusText}
          </div>
          <div class="cam-count-val">Tercatat: <strong>${cam.count}</strong> orang</div>
        </div>
      </div>
    `;
  }).join('');
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

async function resetCounter() {
  if (!confirm("Apakah Anda yakin ingin mengosongkan/reset seluruh hitungan pengunjung?")) {
    return;
  }
  try {
    const res = await fetch(`/api/events/${EVENT_ID}/reset`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      updateMetrics(data.summary);
      fetchTrend();
    } else {
      alert("Gagal melakukan reset: " + (data.detail || "Error server"));
    }
  } catch (err) {
    console.error("Failed resetting counter:", err);
    alert("Koneksi gagal saat mencoba reset hitungan.");
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initChart();
  fetchSummary();
  fetchTrend();
  initWebSocket();
});

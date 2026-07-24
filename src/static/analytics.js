document.addEventListener("DOMContentLoaded", () => {
  fetchAnalyticsData();
});

let dailyChartInstance = null;
let hourlyChartInstance = null;

async function fetchAnalyticsData() {
  try {
    const response = await fetch("/api/events/1/analytics");
    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }
    const data = await response.json();
    renderAnalytics(data);
  } catch (error) {
    console.error("Gagal mengambil data analytics:", error);
  }
}

function renderAnalytics(data) {
  const stats = data.overall_stats || {};
  const breakdown = data.daily_breakdown || [];
  const hourly = data.hourly_distribution || [];

  // 1. Top Metrics Cards
  document.getElementById("val-total-all-days").textContent = (stats.total_visitors_all_days || 0).toLocaleString("id-ID");
  document.getElementById("val-peak-hour").textContent = stats.peak_hour_overall || "-";
  document.getElementById("val-busiest-day").textContent = stats.busiest_day || "-";
  document.getElementById("val-total-days").textContent = stats.total_days_active || breakdown.length || 0;

  // 2. Daily Breakdown Table
  const tbody = document.getElementById("daily-table-body");
  if (breakdown.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--color-muted); padding: 24px;">Belum ada data rekaman harian.</td></tr>`;
  } else {
    tbody.innerHTML = breakdown
      .map(
        (row) => `
      <tr>
        <td><strong>Hari ${row.day_number}</strong></td>
        <td>${row.date}</td>
        <td style="color: var(--color-accent-lime); font-weight: 700;">+${(row.total_in || 0).toLocaleString("id-ID")}</td>
        <td style="color: var(--color-accent-purple); font-weight: 700;">-${(row.total_out || 0).toLocaleString("id-ID")}</td>
        <td><strong>${(row.peak_inside || 0).toLocaleString("id-ID")} orang</strong></td>
      </tr>
    `
      )
      .join("");
  }

  // 3. Render Charts
  renderDailyChart(breakdown);
  renderHourlyChart(hourly);
}

function renderDailyChart(breakdown) {
  const ctx = document.getElementById("dailyBarChart").getContext("2d");

  const labels = breakdown.map((r) => `Hari ${r.day_number} (${r.date})`);
  const totalIn = breakdown.map((r) => r.total_in);
  const totalOut = breakdown.map((r) => r.total_out);

  if (dailyChartInstance) {
    dailyChartInstance.destroy();
  }

  dailyChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Total Masuk",
          data: totalIn,
          backgroundColor: "#FF7200",
          borderRadius: 8
        },
        {
          label: "Total Keluar",
          data: totalOut,
          backgroundColor: "#017187",
          borderRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: { font: { family: "Inter", weight: "600" } }
        }
      },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: "#EAE5DD" } }
      }
    }
  });
}

function renderHourlyChart(hourly) {
  const ctx = document.getElementById("hourlyLineChart").getContext("2d");

  const labels = hourly.map((h) => h.hour);
  const counts = hourly.map((h) => h.count);

  if (hourlyChartInstance) {
    hourlyChartInstance.destroy();
  }

  hourlyChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Jumlah Masuk Per Jam",
          data: counts,
          borderColor: "#FF7200",
          backgroundColor: "rgba(255, 114, 0, 0.1)",
          borderWidth: 3,
          fill: true,
          tension: 0.3,
          pointRadius: 4,
          pointBackgroundColor: "#FF7200"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: { font: { family: "Inter", weight: "600" } }
        }
      },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: "#EAE5DD" } }
      }
    }
  });
}

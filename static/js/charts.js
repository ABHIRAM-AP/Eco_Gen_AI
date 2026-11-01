/**
 * EcoGen-AI — Chart.js Visualizations Controller
 * High-definition dark-mode charts for GenAI carbon and energy intelligence
 */

// Shared dark theme Chart.js configuration defaults
Chart.defaults.color = '#9ca3af';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(17, 24, 39, 0.95)';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.12)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 8;

let chartModelEfficiencyInstance = null;
let chartDepartmentESGInstance = null;
let chartCarbonTrendInstance = null;
let chartProviderComparisonInstance = null;

/**
 * 1. Model Carbon & Compute Efficiency (Dual Axis Bar + Line)
 */
function renderModelEfficiencyChart(models) {
  const ctx = document.getElementById('chartModelEfficiency');
  if (!ctx) return;

  if (chartModelEfficiencyInstance) {
    chartModelEfficiencyInstance.destroy();
  }

  if (!models || models.length === 0) {
    models = [
      { model_name: 'gemma3:270m', avg_carbon_gco2eq: 0.00045, tokens_per_kwh: 52000 },
      { model_name: 'gemini-1.5-flash', avg_carbon_gco2eq: 0.00185, tokens_per_kwh: 38000 },
      { model_name: 'llama3:8b', avg_carbon_gco2eq: 0.00620, tokens_per_kwh: 12500 },
      { model_name: 'sdxl-turbo', avg_carbon_gco2eq: 0.02450, tokens_per_kwh: 4100 }
    ];
  }

  const labels = models.map(m => m.model_name || 'Unknown');
  const carbonVals = models.map(m => Number(m.avg_carbon_gco2eq || 0));
  const efficiencyVals = models.map(m => Number(m.tokens_per_kwh || 0));

  chartModelEfficiencyInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Avg Carbon (gCO₂eq / event)',
          data: carbonVals,
          backgroundColor: 'rgba(16, 185, 129, 0.65)',
          borderColor: '#10b981',
          borderWidth: 1.5,
          borderRadius: 6,
          yAxisID: 'y',
        },
        {
          label: 'Tokens / kWh (Efficiency)',
          data: efficiencyVals,
          type: 'line',
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.1)',
          borderWidth: 2.5,
          tension: 0.35,
          pointBackgroundColor: '#06b6d4',
          pointRadius: 4,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { boxWidth: 12, font: { size: 11 } }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { font: { size: 10 } }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: 'gCO₂eq / event', color: '#10b981', font: { size: 10 } },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { font: { size: 10 } }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'Tokens / kWh', color: '#06b6d4', font: { size: 10 } },
          grid: { drawOnChartArea: false },
          ticks: { font: { size: 10 } }
        }
      }
    }
  });
}

/**
 * 2. Department ESG Carbon Attribution (Doughnut Chart)
 */
function renderDepartmentESGChart(departments) {
  const ctx = document.getElementById('chartDepartmentESG');
  if (!ctx) return;

  if (chartDepartmentESGInstance) {
    chartDepartmentESGInstance.destroy();
  }

  if (!departments || departments.length === 0) {
    departments = [
      { department: 'Engineering', total_carbon_gco2eq: 0.015, percentage_of_total_carbon: 45.0 },
      { department: 'Research & AI', total_carbon_gco2eq: 0.010, percentage_of_total_carbon: 30.0 },
      { department: 'Product', total_carbon_gco2eq: 0.005, percentage_of_total_carbon: 15.0 },
      { department: 'Customer Support', total_carbon_gco2eq: 0.003, percentage_of_total_carbon: 10.0 }
    ];
  }

  const labels = departments.map(d => d.department || 'General');
  const values = departments.map(d => Number(d.percentage_of_total_carbon || d.total_carbon_gco2eq || 0));

  chartDepartmentESGInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          'rgba(16, 185, 129, 0.75)',
          'rgba(6, 182, 212, 0.75)',
          'rgba(139, 92, 246, 0.75)',
          'rgba(245, 158, 11, 0.75)',
          'rgba(244, 63, 94, 0.75)',
          'rgba(59, 130, 246, 0.75)',
        ],
        borderColor: '#111827',
        borderWidth: 2,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { boxWidth: 12, font: { size: 11 }, padding: 12 }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` ${context.label}: ${context.raw.toFixed(1)}% share`;
            }
          }
        }
      },
      cutout: '68%'
    }
  });
}

/**
 * 3. Regional Grid Carbon Intensity Trend (Line Chart)
 */
function renderCarbonTrendChart(trendPoints) {
  const ctx = document.getElementById('chartCarbonTrend');
  if (!ctx) return;

  if (chartCarbonTrendInstance) {
    chartCarbonTrendInstance.destroy();
  }

  let labels = [];
  let values = [];

  if (trendPoints && trendPoints.length > 0) {
    labels = trendPoints.map((p, idx) => {
      if (p.timestamp) {
        const d = new Date(p.timestamp);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      }
      return `Ev #${p.event_id || idx + 1}`;
    });
    values = trendPoints.map(p => Number(p.carbon_intensity_gco2_per_kwh || 0));
  } else {
    labels = ['T-4h', 'T-3h', 'T-2h', 'T-1h', 'Now'];
    values = [385, 360, 395, 410, 375];
  }

  chartCarbonTrendInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Grid Factor (gCO₂eq / kWh)',
        data: values,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        fill: true,
        borderWidth: 2.5,
        tension: 0.35,
        pointBackgroundColor: '#10b981',
        pointRadius: 4,
        pointHoverRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { font: { size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { font: { size: 10 } },
          title: { display: true, text: 'gCO₂eq/kWh', font: { size: 10 } }
        }
      }
    }
  });
}

/**
 * 4. Provider Comparison (Bar Chart)
 */
function renderProviderComparisonChart(providers) {
  const ctx = document.getElementById('chartProviderComparison');
  if (!ctx) return;

  if (chartProviderComparisonInstance) {
    chartProviderComparisonInstance.destroy();
  }

  if (!providers || providers.length === 0) {
    providers = [
      { provider: 'ollama', total_energy_kwh: 0.00065, total_carbon_gco2eq: 0.0012, event_count: 12 },
      { provider: 'gemini', total_energy_kwh: 0.00028, total_carbon_gco2eq: 0.0008, event_count: 5 },
      { provider: 'openai', total_energy_kwh: 0.00045, total_carbon_gco2eq: 0.0011, event_count: 3 }
    ];
  }

  const labels = providers.map(p => p.provider ? p.provider.toUpperCase() : 'OTHER');
  const energyVals = providers.map(p => Number((p.total_energy_kwh || 0) * 1000)); // in Wh for readability

  chartProviderComparisonInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Cumulative Energy (Watt-hours Wh)',
        data: energyVals,
        backgroundColor: [
          'rgba(139, 92, 246, 0.75)',
          'rgba(6, 182, 212, 0.75)',
          'rgba(16, 185, 129, 0.75)',
          'rgba(245, 158, 11, 0.75)'
        ],
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { font: { size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { font: { size: 10 } },
          title: { display: true, text: 'Energy (Wh)', font: { size: 10 } }
        }
      }
    }
  });
}

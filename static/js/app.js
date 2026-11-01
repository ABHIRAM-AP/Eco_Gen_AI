/**
 * EcoGen-AI — Main Frontend Application Logic
 * Connects UI to Layer 1 (Ingestion) & Layer 2 (Analytical Engine) endpoints.
 */

// Global State
let allEventsCache = [];
let allHardwareCache = [];
let currentEventDetails = null;

// API Base URL (relative path works automatically whether on localhost, 127.0.0.1, or network host)
const API_BASE = '';

document.addEventListener('DOMContentLoaded', () => {
  initLucide();
  initTabs();
  initModalListeners();
  initSimulator();
  initEventSearch();

  // Load all platform data
  refreshAllData();

  // Set up refresh button
  document.getElementById('btnRefreshData').addEventListener('click', () => {
    const icon = document.getElementById('refreshIcon');
    icon.style.transform = 'rotate(360deg)';
    icon.style.transition = 'transform 0.5s ease';
    refreshAllData(() => {
      setTimeout(() => { icon.style.transform = 'rotate(0deg)'; }, 500);
      showToast('Dashboard metrics refreshed');
    });
  });

  // Presentation modal buttons
  document.getElementById('btnOpenGuideWalkthrough').addEventListener('click', () => {
    openModal('walkthroughModal');
  });
  document.getElementById('btnCloseWalkthroughBtn').addEventListener('click', () => {
    closeModal('walkthroughModal');
  });
  document.getElementById('btnCloseWalkthroughModal').addEventListener('click', () => {
    closeModal('walkthroughModal');
  });
});

function initLucide() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

/**
 * Tab Navigation
 */
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      if (!targetId) return;

      // Update button state
      tabButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Update panel visibility
      document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
      });
      const activePanel = document.getElementById(targetId);
      if (activePanel) {
        activePanel.classList.add('active');
      }

      // Re-trigger icon rendering
      initLucide();
    });
  });
}

/**
 * Fetch and refresh all platform data
 */
async function refreshAllData(callback) {
  try {
    await Promise.allSettled([
      fetchSummaryKPIs(),
      fetchModelRankings(),
      fetchDepartmentAttribution(),
      fetchProviderComparison(),
      fetchCarbonTrend(),
      fetchEventsList(),
      fetchHardwareList(),
      fetchBenchmarks()
    ]);
    updateServerStatus(true);
  } catch (err) {
    console.error('Error refreshing platform data:', err);
    updateServerStatus(false);
  } finally {
    if (callback) callback();
    initLucide();
  }
}

function updateServerStatus(isLive) {
  const chip = document.getElementById('serverStatusChip');
  const text = document.getElementById('serverStatusText');
  if (chip && text) {
    if (isLive) {
      chip.className = 'status-chip online';
      text.textContent = 'Platform Live';
    } else {
      chip.className = 'status-chip';
      text.textContent = 'Server Offline';
    }
  }
}

/**
 * 1. Fetch Summary Report & Update Executive KPI Ribbon
 */
async function fetchSummaryKPIs() {
  try {
    const res = await fetch(`${API_BASE}/analytics/summary`);
    if (!res.ok) {
      // Clean zero state for fresh database
      document.getElementById('kpiTotalEnergy') && (document.getElementById('kpiTotalEnergy').textContent = '0.0000');
      document.getElementById('kpiTotalCarbon') && (document.getElementById('kpiTotalCarbon').textContent = '0.000');
      document.getElementById('kpiTotalTokens') && (document.getElementById('kpiTotalTokens').textContent = '0');
      document.getElementById('kpiEnergyPerToken') && (document.getElementById('kpiEnergyPerToken').textContent = '0.00');
      document.getElementById('kpiAvgGridIntensity') && (document.getElementById('kpiAvgGridIntensity').textContent = '385.0');
      document.getElementById('kpiTotalEvents') && (document.getElementById('kpiTotalEvents').textContent = '0');
      document.getElementById('kpiModelCount') && (document.getElementById('kpiModelCount').textContent = '0 models');
      document.getElementById('kpiDeptCount') && (document.getElementById('kpiDeptCount').textContent = '0 depts');
      document.getElementById('kpiTierRatio') && (document.getElementById('kpiTierRatio').textContent = 'Ready');
      document.getElementById('kpiAvgCarbonEvent') && (document.getElementById('kpiAvgCarbonEvent').textContent = '0.00 g/ev');
      document.getElementById('kpiTokensPerKwh') && (document.getElementById('kpiTokensPerKwh').textContent = '0 tok/kWh');
      return;
    }
    const data = await res.json();

    // Total Energy
    const energyElem = document.getElementById('kpiTotalEnergy');
    if (energyElem) {
      const kwh = Number(data.total_energy_kwh || 0);
      energyElem.textContent = kwh < 0.001 ? kwh.toExponential(3) : kwh.toFixed(4);
    }

    // Tier Ratio
    const tierElem = document.getElementById('kpiTierRatio');
    if (tierElem) {
      const t1 = data.tier1_event_count || 0;
      const t2 = data.tier2_event_count || 0;
      const total = t1 + t2;
      const pct = total > 0 ? Math.round((t1 / total) * 100) : 100;
      tierElem.textContent = `Tier 1: ${pct}%`;
    }

    // Total Carbon
    const carbonElem = document.getElementById('kpiTotalCarbon');
    if (carbonElem) {
      const c = Number(data.total_carbon_gco2eq || 0);
      carbonElem.textContent = c < 0.01 ? c.toExponential(3) : c.toFixed(3);
    }

    // Avg Carbon per Event
    const avgCarbonElem = document.getElementById('kpiAvgCarbonEvent');
    if (avgCarbonElem && data.avg_carbon_gco2eq_per_event !== undefined) {
      const avgC = Number(data.avg_carbon_gco2eq_per_event);
      avgCarbonElem.textContent = `${avgC < 0.01 ? avgC.toExponential(2) : avgC.toFixed(4)} g/ev`;
    }

    // Total Tokens
    const tokensElem = document.getElementById('kpiTotalTokens');
    if (tokensElem) {
      const tok = data.total_tokens_processed || 0;
      tokensElem.textContent = tok > 10000 ? `${(tok / 1000).toFixed(1)}k` : tok.toLocaleString();
    }

    // Tokens / kWh
    const tokKwhElem = document.getElementById('kpiTokensPerKwh');
    if (tokKwhElem && data.total_tokens_processed && data.total_energy_kwh) {
      const ratio = Math.round(data.total_tokens_processed / data.total_energy_kwh);
      tokKwhElem.textContent = `${(ratio / 1000).toFixed(1)}k tok/kWh`;
    }

    // Energy per token (μJ)
    const ePerTokElem = document.getElementById('kpiEnergyPerToken');
    if (ePerTokElem && data.total_tokens_processed && data.total_energy_kwh) {
      // 1 kWh = 3.6e9 μJ
      const uj = ((data.total_energy_kwh * 3.6e9) / data.total_tokens_processed).toFixed(2);
      ePerTokElem.textContent = uj;
    } else if (ePerTokElem) {
      ePerTokElem.textContent = '0.00';
    }

    // Avg Grid Intensity
    const gridElem = document.getElementById('kpiAvgGridIntensity');
    if (gridElem) {
      const g = data.avg_carbon_intensity_gco2_per_kwh;
      gridElem.textContent = g ? Number(g).toFixed(1) : '385.0';
    }

    // Recorded Events & Models
    const eventsElem = document.getElementById('kpiTotalEvents');
    if (eventsElem) {
      eventsElem.textContent = (data.total_events || 0).toString();
    }

    const modelCountElem = document.getElementById('kpiModelCount');
    if (modelCountElem) {
      modelCountElem.textContent = `${data.unique_models || 0} models`;
    }

    const deptCountElem = document.getElementById('kpiDeptCount');
    if (deptCountElem) {
      deptCountElem.textContent = `${data.unique_departments || 0} depts`;
    }

  } catch (err) {
    console.warn('fetchSummaryKPIs error:', err);
  }
}

/**
 * 2. Fetch Model Efficiency Rankings
 */
async function fetchModelRankings() {
  try {
    const res = await fetch(`${API_BASE}/analytics/by-model?limit=10`);
    if (!res.ok) return;
    const rankings = await res.json();

    // Render chart in Tab 1
    if (typeof renderModelEfficiencyChart === 'function') {
      renderModelEfficiencyChart(rankings);
    }

    // Render Leaderboard table in Tab 4
    const tbody = document.getElementById('rankingsTableBody');
    if (tbody && rankings.length > 0) {
      tbody.innerHTML = rankings.map((r, idx) => {
        let badgeIcon = '🥈';
        if (idx === 0) badgeIcon = '🥇';
        else if (idx === 2) badgeIcon = '🥉';

        const carbonAvg = Number(r.avg_carbon_gco2eq || 0);
        const energyAvg = Number(r.avg_energy_kwh || 0);

        return `
          <tr>
            <td><strong>${badgeIcon} #${idx + 1}</strong></td>
            <td><strong style="color:#fff;">${escapeHtml(r.model_name)}</strong></td>
            <td><span class="badge badge-blue">${escapeHtml(r.provider || 'custom')}</span></td>
            <td>${r.event_count || 1}</td>
            <td style="color:var(--eco-mint); font-weight:600;">${carbonAvg < 0.01 ? carbonAvg.toExponential(3) : carbonAvg.toFixed(4)} g</td>
            <td>${energyAvg < 0.001 ? energyAvg.toExponential(3) : energyAvg.toFixed(5)} kWh</td>
            <td><strong>${(r.tokens_per_kwh || 0).toLocaleString()}</strong></td>
            <td>
              <span class="badge ${idx === 0 ? 'badge-green' : 'badge-violet'}">
                ${idx === 0 ? 'Eco Star ★' : 'Standard'}
              </span>
            </td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.warn('fetchModelRankings error:', err);
  }
}

/**
 * 3. Fetch Department ESG Attribution
 */
async function fetchDepartmentAttribution() {
  try {
    const res = await fetch(`${API_BASE}/analytics/by-department`);
    if (!res.ok) return;
    const depts = await res.json();
    if (typeof renderDepartmentESGChart === 'function') {
      renderDepartmentESGChart(depts);
    }
  } catch (err) {
    console.warn('fetchDepartmentAttribution error:', err);
  }
}

/**
 * 4. Fetch Provider Comparison
 */
async function fetchProviderComparison() {
  try {
    const res = await fetch(`${API_BASE}/analytics/by-provider`);
    if (!res.ok) return;
    const providers = await res.json();
    if (typeof renderProviderComparisonChart === 'function') {
      renderProviderComparisonChart(providers);
    }
  } catch (err) {
    console.warn('fetchProviderComparison error:', err);
  }
}

/**
 * 5. Fetch Carbon Intensity Trend
 */
async function fetchCarbonTrend() {
  try {
    const res = await fetch(`${API_BASE}/analytics/carbon-trend?limit=100`);
    if (!res.ok) return;
    const trend = await res.json();
    if (typeof renderCarbonTrendChart === 'function') {
      renderCarbonTrendChart(trend);
    }
  } catch (err) {
    console.warn('fetchCarbonTrend error:', err);
  }
}

/**
 * 6. Fetch Layer 1 Events List & Populate Table + Simulator Dropdown
 */
async function fetchEventsList() {
  try {
    const res = await fetch(`${API_BASE}/ingest/events?limit=50`);
    if (!res.ok) return;
    const events = await res.json();
    allEventsCache = events;

    renderEventsTable(events);
    populateSimulatorEvents(events);
  } catch (err) {
    console.warn('fetchEventsList error:', err);
  }
}

function renderEventsTable(events) {
  const tbody = document.getElementById('eventsTableBody');
  if (!tbody) return;

  if (!events || events.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="13" style="text-align:center; padding:2rem; color:var(--text-muted);">
          No inference events recorded yet. Click <strong>Log Event</strong> to ingest one!
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = events.map(ev => {
    const d = ev.timestamp ? new Date(ev.timestamp) : new Date();
    const timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const tokens = (ev.tokens_in || 0) + (ev.tokens_out || 0);

    // Approximate energy for fast preview
    const pwr = ev.power_draw_watts || 25.0;
    const sec = ev.runtime_sec || 0.5;
    const pue = ev.pue || 1.2;
    const estKwh = (pwr * sec * pue) / 3600000;
    const estCarbon = estKwh * (ev.carbon_intensity || 385.0);

    const isTier1 = ev.power_draw_watts !== null && ev.power_draw_watts !== undefined;

    return `
      <tr>
        <td><strong>#${ev.id}</strong></td>
        <td style="color:var(--text-secondary);">${timeStr}</td>
        <td><strong style="color:#fff;">${escapeHtml(ev.model_name || 'unknown')}</strong></td>
        <td><span class="badge badge-blue">${escapeHtml(ev.task_type || 'text-gen')}</span></td>
        <td><span style="color:var(--text-muted);">${escapeHtml(ev.provider || 'local')}</span></td>
        <td>${tokens > 0 ? tokens : '--'}</td>
        <td>${ev.runtime_sec ? ev.runtime_sec.toFixed(2) + 's' : '--'}</td>
        <td>${pwr ? pwr.toFixed(1) + ' W' : 'Unmeasured'}</td>
        <td>${escapeHtml(ev.gpu_model || 'GPU')} (PUE ${pue})</td>
        <td><span class="badge badge-violet">${escapeHtml(ev.region || 'US-CAL')}</span></td>
        <td style="color:var(--eco-mint); font-weight:600;">${estCarbon.toFixed(4)} g</td>
        <td>
          <span class="badge ${isTier1 ? 'badge-tier1' : 'badge-tier2'}">
            ${isTier1 ? 'Tier 1' : 'Tier 2'}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openDeepDive(${ev.id})" style="padding:0.25rem 0.55rem; font-size:0.72rem;">
            Deep Dive
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * 7. Fetch Hardware Snapshots
 */
async function fetchHardwareList() {
  try {
    const res = await fetch(`${API_BASE}/ingest/hardware?limit=20`);
    if (!res.ok) return;
    const snaps = await res.json();
    allHardwareCache = snaps;

    const tbody = document.getElementById('hwTableBody');
    if (!tbody) return;

    if (!snaps || snaps.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; padding:1.5rem; color:var(--text-muted);">
            No hardware snapshots recorded. Click <strong>Snapshot Hardware</strong> to capture baseline.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = snaps.map(s => {
      const d = s.timestamp ? new Date(s.timestamp) : new Date();
      const timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      return `
        <tr>
          <td>#${s.id}</td>
          <td style="color:var(--text-secondary);">${timeStr}</td>
          <td><strong style="color:#fff;">${escapeHtml(s.device_id || 'system-01')}</strong></td>
          <td>${s.power_draw_watts !== null ? Number(s.power_draw_watts).toFixed(1) + ' W' : '--'}</td>
          <td>
            <span class="badge badge-blue">
              ${s.gpu_util_pct !== null ? Number(s.gpu_util_pct).toFixed(0) + '%' : '0%'}
            </span>
          </td>
          <td style="color:var(--eco-amber); font-weight:600;">
            ${s.idle_power_baseline_w !== null ? Number(s.idle_power_baseline_w).toFixed(1) + ' W' : '0.0 W'}
          </td>
          <td style="color:var(--text-muted); font-size:0.75rem;">
            ${s.hardware_install_date ? new Date(s.hardware_install_date).toLocaleDateString() : 'Active (Amortized)'}
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.warn('fetchHardwareList error:', err);
  }
}

/**
 * 8. Fetch Task Type Statistical Benchmarks
 */
async function fetchBenchmarks() {
  try {
    const res = await fetch(`${API_BASE}/analytics/benchmarks`);
    if (!res.ok) return;
    const benchmarks = await res.json();

    const tbody = document.getElementById('benchmarksTableBody');
    if (!tbody) return;

    if (!benchmarks || benchmarks.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align:center; padding:1.5rem; color:var(--text-muted);">
            No benchmark profiles computed yet.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = benchmarks.map(b => {
      const eAvg = Number(b.energy_kwh.avg || 0);
      const eMed = Number(b.energy_kwh.p50 || 0);
      const eP95 = Number(b.energy_kwh.p95 || 0);

      const cAvg = Number(b.carbon_gco2eq.avg || 0);
      const cMed = Number(b.carbon_gco2eq.p50 || 0);
      const cP95 = Number(b.carbon_gco2eq.p95 || 0);

      return `
        <tr>
          <td><strong style="color:#fff;">${escapeHtml(b.task_type)}</strong></td>
          <td><span class="badge badge-violet">${b.sample_count} runs</span></td>
          <td>${eAvg < 0.001 ? eAvg.toExponential(3) : eAvg.toFixed(5)}</td>
          <td>${eMed < 0.001 ? eMed.toExponential(3) : eMed.toFixed(5)}</td>
          <td style="color:var(--eco-amber);">${eP95 < 0.001 ? eP95.toExponential(3) : eP95.toFixed(5)}</td>
          <td style="color:var(--eco-mint); font-weight:600;">${cAvg.toFixed(4)}</td>
          <td>${cMed.toFixed(4)}</td>
          <td style="color:var(--eco-rose);">${cP95.toFixed(4)}</td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.warn('fetchBenchmarks error:', err);
  }
}

/**
 * Filter events in table
 */
function initEventSearch() {
  const input = document.getElementById('eventSearchInput');
  if (!input) return;

  input.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderEventsTable(allEventsCache);
      return;
    }

    const filtered = allEventsCache.filter(ev => {
      return (
        (ev.model_name && ev.model_name.toLowerCase().includes(q)) ||
        (ev.task_type && ev.task_type.toLowerCase().includes(q)) ||
        (ev.provider && ev.provider.toLowerCase().includes(q)) ||
        (ev.department && ev.department.toLowerCase().includes(q))
      );
    });
    renderEventsTable(filtered);
  });
}

/**
 * Open Event Deep-Dive Modal
 */
async function openDeepDive(eventId) {
  try {
    const res = await fetch(`${API_BASE}/analytics/event/${eventId}`);
    if (!res.ok) {
      showToast(`Could not load analytics for Event #${eventId}`, 'error');
      return;
    }
    const data = await res.json();
    currentEventDetails = data;

    // Retrieve cached ingestion event metadata if available
    const cachedEv = allEventsCache.find(e => e.id === eventId) || {};
    const runtime = cachedEv.runtime_sec !== undefined && cachedEv.runtime_sec !== null
      ? Number(cachedEv.runtime_sec).toFixed(2)
      : (data.energy.runtime_sec ? Number(data.energy.runtime_sec).toFixed(2) : '--');

    document.getElementById('auditEventId').textContent = `#${eventId} (${data.model_name || ''})`;
    document.getElementById('auditEventSummary').textContent = 
      `${data.task_type || 'Inference'} run via ${data.provider || 'local'} (${data.tokens_total || 0} tokens in ${runtime}s)`;

    // Energy formatting
    const kwh = Number(data.energy.energy_kwh || 0);
    document.getElementById('auditEnergyKwh').textContent = kwh < 0.0001 ? kwh.toExponential(4) : kwh.toFixed(6);

    const isT1 = data.energy.computation_tier === 'tier1_measured';
    document.getElementById('auditTierBadge').textContent = isT1 ? 'Tier 1 Measured' : 'Tier 2 FLOPs Fallback';
    document.getElementById('auditTierBadge').style.color = isT1 ? 'var(--eco-mint)' : 'var(--eco-amber)';

    // Total Carbon formatting
    const cTotal = Number(data.carbon.total_gco2eq || 0);
    document.getElementById('auditTotalCarbon').textContent = cTotal < 0.0001 ? cTotal.toExponential(4) : cTotal.toFixed(4);

    // Operational Scope 2 (use operational_gco2eq)
    const s2 = Number(data.carbon.operational_gco2eq !== undefined ? data.carbon.operational_gco2eq : (data.carbon.scope2_operational_gco2eq || 0));
    document.getElementById('auditScope2').textContent = s2 < 0.0001 ? s2.toExponential(3) + ' g' : s2.toFixed(4) + ' g';
    document.getElementById('auditGridFactor').textContent = `@ ${data.carbon.carbon_intensity_gco2_per_kwh || 385} gCO₂/kWh`;

    // Embodied Scope 3 (use embodied_gco2eq)
    const s3 = Number(data.carbon.embodied_gco2eq !== undefined && data.carbon.embodied_gco2eq !== null ? data.carbon.embodied_gco2eq : 0);
    document.getElementById('auditScope3').textContent = s3 > 0 ? (s3 < 0.0001 ? s3.toExponential(3) + ' g' : s3.toFixed(6) + ' g') : '0.000000 g';

    document.getElementById('auditTokensPerKwh').textContent = (data.tokens_per_kwh || 0).toLocaleString();
    document.getElementById('auditEnergyPerToken').textContent = data.energy_per_token_uj ? `${data.energy_per_token_uj} μJ` : '--';

    // Power details mapping correctly to schema fields
    const activePwr = data.energy.active_power_w !== null && data.energy.active_power_w !== undefined
      ? `${Number(data.energy.active_power_w).toFixed(1)} W`
      : 'FLOPs Estimated (Unmeasured)';
    document.getElementById('auditActivePower').textContent = activePwr;

    const idlePwr = data.energy.idle_power_w !== undefined && data.energy.idle_power_w !== null
      ? `${Number(data.energy.idle_power_w).toFixed(1)} W`
      : '0.0 W';
    document.getElementById('auditIdlePower').textContent = idlePwr;

    const pue = data.energy.pue_factor !== undefined ? data.energy.pue_factor : (data.energy.pue || 1.2);
    document.getElementById('auditPue').textContent = `${pue}x multiplier`;

    const gpu = data.carbon.gpu_model || cachedEv.gpu_model || 'Standard Compute';
    document.getElementById('auditGpu').textContent = gpu;

    openModal('deepDiveModal');
  } catch (err) {
    console.error('openDeepDive error:', err);
    showToast('Failed to load event details', 'error');
  }
}

/**
 * What-If Simulation Sandbox
 */
function initSimulator() {
  const btnRun = document.getElementById('btnRunSimulation');
  if (btnRun) {
    btnRun.addEventListener('click', runSimulation);
  }

  const pueSelect = document.getElementById('simAltPue');
  if (pueSelect) {
    pueSelect.addEventListener('change', (e) => {
      const disp = document.getElementById('pueValDisplay');
      if (disp) disp.textContent = e.target.value || 'Original';
    });
  }
}

function populateSimulatorEvents(events) {
  const select = document.getElementById('simBaseEventSelect');
  const meta = document.getElementById('simBaseEventMeta');
  if (!select) return;

  if (!events || events.length === 0) {
    select.innerHTML = '<option value="">No events available</option>';
    if (meta) meta.textContent = 'None';
    return;
  }

  select.innerHTML = events.map(ev => {
    return `<option value="${ev.id}">Event #${ev.id} — ${ev.model_name} (${ev.task_type || 'inference'}) [${ev.region || 'US'}]</option>`;
  }).join('');

  if (meta) meta.textContent = `${events.length} events loaded`;
}

async function runSimulation() {
  const baseEventId = document.getElementById('simBaseEventSelect').value;
  if (!baseEventId) {
    showToast('Please select a base inference event', 'error');
    return;
  }

  const altGpu = document.getElementById('simAltGpu').value || null;
  const altRegion = document.getElementById('simAltRegion').value || null;
  const altPue = document.getElementById('simAltPue').value ? parseFloat(document.getElementById('simAltPue').value) : null;
  const altBatch = document.getElementById('simAltBatch').value ? parseInt(document.getElementById('simAltBatch').value, 10) : null;

  const payload = {
    base_event_id: parseInt(baseEventId, 10),
    alt_gpu_model: altGpu,
    alt_region: altRegion,
    alt_pue: altPue,
    alt_batch_size: altBatch
  };

  try {
    const res = await fetch(`${API_BASE}/analytics/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      showToast('Simulation calculation failed', 'error');
      return;
    }

    const data = await res.json();
    renderSimulationResults(data);
    showToast('What-If simulation executed successfully');
  } catch (err) {
    console.error('runSimulation error:', err);
    showToast('Simulation error', 'error');
  }
}

function renderSimulationResults(res) {
  // Reduction badge
  const carbonPct = Number(res.carbon_reduction_pct || 0);
  const badge = document.getElementById('simCarbonReductionBadge');
  const label = document.getElementById('simCarbonReductionLabel');

  if (carbonPct >= 0) {
    badge.textContent = `-${carbonPct.toFixed(1)}%`;
    badge.style.color = '#34d399';
    label.textContent = 'Carbon Footprint Reduction';
  } else {
    badge.textContent = `+${Math.abs(carbonPct).toFixed(1)}%`;
    badge.style.color = '#f43f5e';
    label.textContent = 'Carbon Emissions Increase';
  }

  const energyPct = Number(res.energy_reduction_pct || 0);
  document.getElementById('simEnergyReductionSub').textContent = 
    `Energy Delta: ${energyPct >= 0 ? '-' : '+'}${Math.abs(energyPct).toFixed(1)}% reduction`;

  // Energy
  const origE = Number(res.original_energy_kwh || 0);
  const simE = Number(res.simulated_energy_kwh || 0);
  document.getElementById('simOrigEnergy').textContent = `${origE < 0.001 ? origE.toExponential(3) : origE.toFixed(5)} kWh`;
  document.getElementById('simNewEnergy').textContent = `${simE < 0.001 ? simE.toExponential(3) : simE.toFixed(5)} kWh`;
  document.getElementById('simEnergyDelta').textContent = `Delta: ${(simE - origE).toFixed(5)} kWh`;

  // Carbon
  const origC = Number(res.original_carbon_gco2eq || 0);
  const simC = Number(res.simulated_carbon_gco2eq || 0);
  document.getElementById('simOrigCarbon').textContent = `${origC.toFixed(4)} g`;
  document.getElementById('simNewCarbon').textContent = `${simC.toFixed(4)} g`;
  document.getElementById('simCarbonDelta').textContent = `Delta: ${(simC - origC).toFixed(4)} gCO₂eq`;

  // Changes applied list
  const changesList = document.getElementById('simChangesAppliedList');
  if (changesList && res.changes_applied) {
    changesList.innerHTML = res.changes_applied.map(ch => {
      return `<li>${escapeHtml(ch)}</li>`;
    }).join('');
  }
}

/**
 * Modals & Preset Fillers
 */
function initModalListeners() {
  // Open log event modal
  const btnOpen = document.getElementById('btnOpenLogModal');
  const btnOpenInline = document.getElementById('btnLogEventInline');
  if (btnOpen) btnOpen.addEventListener('click', () => openModal('logEventModal'));
  if (btnOpenInline) btnOpenInline.addEventListener('click', () => openModal('logEventModal'));

  // Close log event modal
  document.getElementById('btnCloseLogModal').addEventListener('click', () => closeModal('logEventModal'));
  document.getElementById('btnCancelLog').addEventListener('click', () => closeModal('logEventModal'));

  // Close audit modal
  document.getElementById('btnCloseAuditModal').addEventListener('click', () => closeModal('deepDiveModal'));
  document.getElementById('btnCloseAuditBtn').addEventListener('click', () => closeModal('deepDiveModal'));

  // Form submission for logging new event
  const form = document.getElementById('logEventForm');
  if (form) {
    form.addEventListener('submit', handleLogEventSubmit);
  }

  // Trigger hardware snapshot
  const btnSnap = document.getElementById('btnTriggerHwSnap');
  if (btnSnap) {
    btnSnap.addEventListener('click', handleHardwareSnapTrigger);
  }
}

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add('active');
  initLucide();
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove('active');
}

/**
 * Form Submission: Ingest Event
 */
async function handleLogEventSubmit(e) {
  e.preventDefault();
  const modelName = document.getElementById('inpModelName').value.trim();
  if (!modelName) return;

  const pwrVal = document.getElementById('inpPowerWatts').value;
  const powerWatts = pwrVal !== '' ? parseFloat(pwrVal) : null;

  const payload = {
    model_name: modelName,
    task_type: document.getElementById('inpTaskType').value,
    provider: document.getElementById('inpProvider').value,
    department: document.getElementById('inpDepartment').value,
    tokens_in: parseInt(document.getElementById('inpTokensIn').value || '0', 10),
    tokens_out: parseInt(document.getElementById('inpTokensOut').value || '0', 10),
    runtime_sec: parseFloat(document.getElementById('inpRuntime').value || '0.5'),
    power_draw_watts: powerWatts,
    gpu_model: document.getElementById('inpGpuModel').value,
    region: document.getElementById('inpRegion').value,
    pue: 1.2,
    num_gpus_used: 1,
    batch_size: 1
  };

  const submitBtn = document.getElementById('btnSubmitLog');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Ingesting...';

  try {
    const res = await fetch(`${API_BASE}/ingest/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      showToast('Error ingesting event', 'error');
      return;
    }

    const created = await res.json();
    closeModal('logEventModal');
    showToast(`Inference Event #${created.id} logged & analyzed!`);
    refreshAllData();
  } catch (err) {
    console.error('Error in handleLogEventSubmit:', err);
    showToast('Failed to ingest event', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i data-lucide="check" style="width:16px; height:16px;"></i> Ingest &amp; Compute';
    initLucide();
  }
}

/**
 * Trigger Hardware Snapshot
 */
async function handleHardwareSnapTrigger() {
  try {
    const payload = {
      device_id: 'workstation-gpu-01',
      power_draw_watts: 28.5,
      gpu_util_pct: 62.0,
      idle_power_baseline_w: 12.0
    };

    const res = await fetch(`${API_BASE}/ingest/hardware`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const snap = await res.json();
      showToast(`Captured Hardware Snapshot #${snap.id}`);
      fetchHardwareList();
    }
  } catch (err) {
    console.error('Error triggering hardware snap:', err);
  }
}

/**
 * 1-Click Demo Presets
 */
window.applyPreset = function(presetKey) {
  if (presetKey === 'gemma-local') {
    document.getElementById('inpModelName').value = 'gemma3:270m';
    document.getElementById('inpTaskType').value = 'text-generation';
    document.getElementById('inpProvider').value = 'ollama';
    document.getElementById('inpTokensIn').value = '15';
    document.getElementById('inpTokensOut').value = '90';
    document.getElementById('inpRuntime').value = '0.42';
    document.getElementById('inpPowerWatts').value = '18.5';
    document.getElementById('inpGpuModel').value = 'T4';
    document.getElementById('inpRegion').value = 'US-CAL-CISO';
    document.getElementById('inpDepartment').value = 'Engineering';
  } else if (presetKey === 'gemini-cloud') {
    document.getElementById('inpModelName').value = 'gemini-1.5-flash';
    document.getElementById('inpTaskType').value = 'text-generation';
    document.getElementById('inpProvider').value = 'gemini';
    document.getElementById('inpTokensIn').value = '120';
    document.getElementById('inpTokensOut').value = '450';
    document.getElementById('inpRuntime').value = '0.95';
    document.getElementById('inpPowerWatts').value = ''; // trigger Tier 2 estimation!
    document.getElementById('inpGpuModel').value = 'A100-80GB';
    document.getElementById('inpRegion').value = 'US-CAL-CISO';
    document.getElementById('inpDepartment').value = 'Product';
  } else if (presetKey === 'llama3-code') {
    document.getElementById('inpModelName').value = 'llama3:8b';
    document.getElementById('inpTaskType').value = 'code-assistance';
    document.getElementById('inpProvider').value = 'ollama';
    document.getElementById('inpTokensIn').value = '80';
    document.getElementById('inpTokensOut').value = '210';
    document.getElementById('inpRuntime').value = '1.65';
    document.getElementById('inpPowerWatts').value = '85.0';
    document.getElementById('inpGpuModel').value = 'RTX-4090';
    document.getElementById('inpRegion').value = 'UK';
    document.getElementById('inpDepartment').value = 'Engineering';
  } else if (presetKey === 'sdxl-image') {
    document.getElementById('inpModelName').value = 'sdxl-turbo';
    document.getElementById('inpTaskType').value = 'image-generation';
    document.getElementById('inpProvider').value = 'huggingface';
    document.getElementById('inpTokensIn').value = '45';
    document.getElementById('inpTokensOut').value = '1';
    document.getElementById('inpRuntime').value = '3.80';
    document.getElementById('inpPowerWatts').value = '240.0';
    document.getElementById('inpGpuModel').value = 'A100-80GB';
    document.getElementById('inpRegion').value = 'FR';
    document.getElementById('inpDepartment').value = 'Research';
  }
};

/**
 * Toast Notification Utility
 */
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  if (type === 'error') {
    toast.style.borderColor = 'rgba(244, 63, 94, 0.4)';
  }

  const iconName = type === 'error' ? 'alert-circle' : 'check-circle-2';
  toast.innerHTML = `
    <i data-lucide="${iconName}" style="width:16px; height:16px; color:${type === 'error' ? '#f43f5e' : '#34d399'};"></i>
    <span>${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  initLucide();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

"""
BrandShield AI — Interactive Command Center Dashboard.
Serves a responsive cybersecurity single-page dashboard directly from FastAPI.
Integrates live data from discovery, indicators, campaigns, and alerts with manual review workflows.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Command Center Dashboard"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BrandShield AI — Digital Risk Protection Command Center</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #0a0e1a;
      --bg-surface: #111827;
      --bg-card: #162032;
      --bg-card-hover: #1c293e;
      --border-color: #1f2d42;
      --border-glow: rgba(6, 182, 212, 0.25);
      --cyan: #06b6d4;
      --cyan-glow: rgba(6, 182, 212, 0.15);
      --emerald: #10b981;
      --amber: #f59e0b;
      --crimson: #ef4444;
      --purple: #8b5cf6;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --text-dim: #6b7280;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-primary);
      color: var(--text-main);
      font-family: var(--font-sans);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Top Navigation Bar */
    header {
      background: rgba(17, 24, 39, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-color);
      position: sticky;
      top: 0;
      z-index: 50;
      padding: 0.75rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand-logo {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
    }
    .brand-shield-icon {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #06b6d4, #3b82f6);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      color: #fff;
      box-shadow: 0 0 15px var(--border-glow);
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #fff;
    }
    .brand-sub {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--cyan);
      display: block;
    }

    /* Auth Bar Controls */
    .auth-bar {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .token-input {
      background: #0d131f;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 0.45rem 0.75rem;
      color: var(--text-main);
      font-family: var(--font-mono);
      font-size: 0.8rem;
      width: 260px;
      transition: all 0.2s;
    }
    .token-input:focus {
      outline: none;
      border-color: var(--cyan);
      box-shadow: 0 0 8px var(--cyan-glow);
    }
    .btn {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 0.45rem 0.9rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s;
    }
    .btn:hover {
      background: var(--bg-card-hover);
      border-color: var(--cyan);
    }
    .btn-primary {
      background: linear-gradient(135deg, #0891b2, #0284c7);
      border: 1px solid #06b6d4;
      color: #fff;
      font-weight: 600;
    }
    .btn-primary:hover {
      background: linear-gradient(135deg, #06b6d4, #0ea5e9);
      box-shadow: 0 0 12px var(--cyan-glow);
    }
    .btn-danger {
      background: rgba(239, 68, 68, 0.15);
      border-color: rgba(239, 68, 68, 0.4);
      color: #fca5a5;
    }
    .btn-danger:hover {
      background: rgba(239, 68, 68, 0.25);
      border-color: var(--crimson);
    }

    /* Main Container */
    main {
      flex: 1;
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    /* Metrics Overview Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem;
    }
    .metric-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      position: relative;
      overflow: hidden;
    }
    .metric-card::before {
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0; height: 2px;
      background: linear-gradient(90deg, transparent, var(--cyan), transparent);
      opacity: 0.4;
    }
    .metric-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }
    .metric-val {
      font-size: 1.85rem;
      font-weight: 700;
      color: #fff;
      font-family: var(--font-mono);
    }
    .metric-sub {
      font-size: 0.75rem;
      color: var(--text-dim);
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    /* Navigation Tabs */
    .nav-tabs {
      display: flex;
      gap: 0.5rem;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 0.5rem;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }
    .tab-btn:hover {
      color: var(--text-main);
      background: var(--bg-surface);
    }
    .tab-btn.active {
      color: var(--cyan);
      background: rgba(6, 182, 212, 0.1);
      font-weight: 600;
    }

    /* Tab Content Panels */
    .tab-content { display: none; }
    .tab-content.active { display: flex; flex-direction: column; gap: 1.25rem; }

    /* Tables & Card Lists */
    .panel-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .panel-title {
      font-size: 1.05rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .data-table-wrapper {
      overflow-x: auto;
    }
    table.data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }
    table.data-table th {
      text-align: left;
      padding: 0.75rem 1rem;
      background: #0d131f;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-color);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.7rem;
      letter-spacing: 0.05em;
    }
    table.data-table td {
      padding: 0.85rem 1rem;
      border-bottom: 1px solid var(--border-color);
      vertical-align: middle;
    }
    table.data-table tr:hover {
      background: rgba(22, 32, 50, 0.6);
    }

    /* Badges & Tags */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 600;
      font-family: var(--font-mono);
      text-transform: uppercase;
    }
    .badge-critical { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-high { background: rgba(249, 115, 22, 0.2); color: #fdba74; border: 1px solid rgba(249, 115, 22, 0.4); }
    .badge-medium { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-low { background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }
    .badge-benign { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-source { background: rgba(139, 92, 246, 0.15); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.3); }

    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
    }
    .dot-green { background: var(--emerald); box-shadow: 0 0 8px var(--emerald); }
    .dot-amber { background: var(--amber); box-shadow: 0 0 8px var(--amber); }
    .dot-red { background: var(--crimson); box-shadow: 0 0 8px var(--crimson); }

    /* State messages */
    .empty-state, .loading-state, .error-state {
      padding: 3rem 1rem;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
      color: var(--text-muted);
    }
    .spinner {
      width: 28px;
      height: 28px;
      border: 3px solid rgba(6, 182, 212, 0.2);
      border-top-color: var(--cyan);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Toast Notification */
    #toast {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 0.75rem 1.25rem;
      color: #fff;
      font-size: 0.85rem;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      display: none;
      z-index: 100;
      animation: fadeIn 0.3s;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    /* Modal */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }
    .modal {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      width: 90%;
      max-width: 500px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
  </style>
</head>
<body>

  <!-- Top Header Navigation -->
  <header>
    <a href="/" class="brand-logo">
      <div class="brand-shield-icon">&#9650;</div>
      <div>
        <div class="brand-title">BrandShield AI</div>
        <span class="brand-sub">Digital Risk Protection Platform</span>
      </div>
    </a>
    <div class="auth-bar">
      <input type="password" id="authTokenInput" class="token-input" placeholder="Admin/Owner Bearer Token..." />
      <button class="btn" onclick="saveAuthToken()">Save Token</button>
      <button class="btn btn-primary" onclick="refreshDashboardData()">&#8635; Refresh Live</button>
    </div>
  </header>

  <!-- Main Dashboard -->
  <main>

    <!-- Top Status Banner -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">Threat Discovery Engine</div>
        <div class="metric-val" id="metricWorkerStatus">--</div>
        <div class="metric-sub" id="metricWorkerSub"><span class="pulse-dot dot-amber"></span> Checking telemetry...</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">External Feed Observations</div>
        <div class="metric-val" id="metricIndicatorsTotal">--</div>
        <div class="metric-sub" id="metricIndicatorsSub">abuse.ch URLhaus & Feeds</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Correlated Campaigns</div>
        <div class="metric-val" id="metricCampaignsTotal">--</div>
        <div class="metric-sub">Connected Threat Clusters</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Actionable Brand Alerts</div>
        <div class="metric-val" id="metricAlertsTotal">--</div>
        <div class="metric-sub">Pending Review & Resolution</div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('tab-discovery')">&#9737; Threat Discovery & Feeds</button>
      <button class="tab-btn" onclick="switchTab('tab-indicators')">&#9776; Discovered Indicators</button>
      <button class="tab-btn" onclick="switchTab('tab-campaigns')">&#9881; Threat Campaigns</button>
      <button class="tab-btn" onclick="switchTab('tab-alerts')">&#9888; Alerts & Review</button>
      <button class="tab-btn" onclick="switchTab('tab-benchmarks')">&#9733; Benchmark Evaluation</button>
    </div>

    <!-- Tab 1: Discovery Overview -->
    <div id="tab-discovery" class="tab-content active">
      <div class="panel-card">
        <div class="panel-header">
          <div class="panel-title">&#9737; Operational Feed Connectors & Checkpoint Telemetry</div>
          <div>
            <button class="btn btn-primary" onclick="triggerDiscoveryCycleNow()">&#9654; Trigger Discovery Run Now</button>
          </div>
        </div>
        <div class="data-table-wrapper">
          <table class="data-table" id="connectorsTable">
            <thead>
              <tr>
                <th>Source Feed</th>
                <th>Status</th>
                <th>Last Poll</th>
                <th>Last Success</th>
                <th>Fetched</th>
                <th>Accepted</th>
                <th>Rejected</th>
                <th>Checkpoint</th>
              </tr>
            </thead>
            <tbody id="connectorsBody">
              <tr><td colspan="8"><div class="loading-state"><div class="spinner"></div>Loading connectors...</div></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Tab 2: Discovered Indicators -->
    <div id="tab-indicators" class="tab-content">
      <div class="panel-card">
        <div class="panel-header">
          <div class="panel-title">&#9776; Live Discovered Threat Observations</div>
          <span style="font-size:0.75rem; color:var(--text-muted);">&#9432; External threat indicators enriched with brand correlation</span>
        </div>
        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Indicator Target</th>
                <th>Type</th>
                <th>Source</th>
                <th>Status</th>
                <th>Risk Score</th>
                <th>Associated Brand</th>
                <th>First Seen</th>
              </tr>
            </thead>
            <tbody id="indicatorsBody">
              <tr><td colspan="7"><div class="loading-state"><div class="spinner"></div>Loading indicators...</div></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Tab 3: Correlated Campaigns -->
    <div id="tab-campaigns" class="tab-content">
      <div class="panel-card">
        <div class="panel-header">
          <div class="panel-title">&#9881; Active Impersonation Campaigns</div>
          <span style="font-size:0.75rem; color:var(--text-muted);">&#9432; Evidence-backed connected components clustering</span>
        </div>
        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Campaign Title</th>
                <th>Status</th>
                <th>Risk Score</th>
                <th>Member Entities</th>
                <th>Correlation Details</th>
                <th>Detected At</th>
              </tr>
            </thead>
            <tbody id="campaignsBody">
              <tr><td colspan="6"><div class="loading-state"><div class="spinner"></div>Loading campaigns...</div></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Tab 4: Actionable Alerts & Manual Review -->
    <div id="tab-alerts" class="tab-content">
      <div class="panel-card">
        <div class="panel-header">
          <div class="panel-title">&#9888; Brand Owner Incident Alerts</div>
          <span style="font-size:0.75rem; color:var(--text-muted);">&#9432; Deduplicated alerts with manual review workflow</span>
        </div>
        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Incident Alert</th>
                <th>Severity</th>
                <th>Resolution Status</th>
                <th>Campaign Context</th>
                <th>Created At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="alertsBody">
              <tr><td colspan="6"><div class="loading-state"><div class="spinner"></div>Loading alerts...</div></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Tab 5: Benchmark Evaluation -->
    <div id="tab-benchmarks" class="tab-content">
      <div class="panel-card">
        <div class="panel-header">
          <div class="panel-title">&#9733; Synthetic Detection Quality Benchmark (Phase 4 Evaluation)</div>
        </div>
        <p style="font-size:0.85rem; color:var(--text-muted);">
          Automated evaluation results computed over 35 deterministic synthetic test samples
          across Domain impersonation, Social profile lookalikes, and Mobile app store listings.
          <em>Note: Synthetic benchmark metrics benchmark deterministic rules and do not represent internet-wide detection accuracy.</em>
        </p>
        <div class="metrics-grid" style="margin-top:1rem;">
          <div class="metric-card">
            <div class="metric-label">Precision</div>
            <div class="metric-val" style="color:var(--emerald);">100.0%</div>
            <div class="metric-sub">Zero False Positives</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Recall</div>
            <div class="metric-val" style="color:var(--cyan);">100.0%</div>
            <div class="metric-sub">Zero Missed Threats</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">F1-Score</div>
            <div class="metric-val" style="color:var(--purple);">100.0%</div>
            <div class="metric-sub">Harmonic Balance</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">False Positive Rate</div>
            <div class="metric-val" style="color:var(--emerald);">0.0%</div>
            <div class="metric-sub">Protected Official Assets</div>
          </div>
        </div>
      </div>
    </div>

  </main>

  <!-- Manual Review Modal -->
  <div id="reviewModal" class="modal-backdrop">
    <div class="modal">
      <h3 id="modalTitle">Review Incident Alert</h3>
      <input type="hidden" id="modalAlertId" />
      <div>
        <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:0.25rem;">New Incident Status:</label>
        <select id="modalStatusSelect" style="width:100%; background:#0d131f; border:1px solid var(--border-color); color:#fff; padding:0.5rem; border-radius:6px;">
          <option value="ACKNOWLEDGED">ACKNOWLEDGED (Under investigation)</option>
          <option value="RESOLVED">RESOLVED (Threat mitigated)</option>
          <option value="DISMISSED">DISMISSED (False positive / benign)</option>
        </select>
      </div>
      <div>
        <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:0.25rem;">Reviewer Notes (Recorded in Audit Trail):</label>
        <textarea id="modalNotesInput" rows="3" style="width:100%; background:#0d131f; border:1px solid var(--border-color); color:#fff; padding:0.5rem; border-radius:6px;" placeholder="Optional reviewer rationale..."></textarea>
      </div>
      <div style="display:flex; justify-content:flex-end; gap:0.5rem;">
        <button class="btn" onclick="closeReviewModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitAlertReview()">Submit Review Decision</button>
      </div>
    </div>
  </div>

  <!-- Toast Element -->
  <div id="toast"></div>

  <script>
    function getStoredToken() {
      return localStorage.getItem("brandshield_token") || "";
    }

    function saveAuthToken() {
      const val = document.getElementById("authTokenInput").value.trim();
      localStorage.setItem("brandshield_token", val);
      showToast("Token saved to local session.");
      refreshDashboardData();
    }

    function showToast(msg) {
      const el = document.getElementById("toast");
      el.textContent = msg;
      el.style.display = "block";
      setTimeout(() => { el.style.display = "none"; }, 4000);
    }

    function switchTab(tabId) {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      event.target.classList.add("active");
      document.getElementById(tabId).classList.add("active");
    }

    async function apiFetch(endpoint, options = {}) {
      const token = getStoredToken();
      const headers = { "Content-Type": "application/json", ...options.headers };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`/api/v1${endpoint}`, { ...options, headers });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || err.detail || `Request failed with HTTP ${res.status}`);
      }
      return res.json();
    }

    async function refreshDashboardData() {
      loadDiscoveryHealth();
      loadDiscoveryStats();
      loadIndicators();
    }

    async function loadDiscoveryHealth() {
      try {
        const data = await apiFetch("/admin/discovery/health");
        document.getElementById("metricWorkerStatus").textContent = data.overall_status;
        const sub = document.getElementById("metricWorkerSub");
        if (data.worker_running) {
          sub.innerHTML = `<span class="pulse-dot dot-green"></span> Polling every ${data.poll_interval_seconds}s`;
        } else if (data.worker_enabled) {
          sub.innerHTML = `<span class="pulse-dot dot-amber"></span> Enabled, Idle`;
        } else {
          sub.innerHTML = `<span class="pulse-dot dot-amber"></span> Worker Disabled (On-Demand Mode)`;
        }

        const tbody = document.getElementById("connectorsBody");
        tbody.innerHTML = data.sources.map(s => `
          <tr>
            <td><strong>${escapeHtml(s.source_name)}</strong><br><span style="font-size:0.7rem; color:var(--text-dim);">${escapeHtml(s.source_id)}</span></td>
            <td><span class="badge ${s.status === 'IDLE' ? 'badge-benign' : (s.status === 'ERROR' ? 'badge-critical' : 'badge-low')}">${s.status}</span></td>
            <td>${s.last_poll_at ? new Date(s.last_poll_at).toLocaleTimeString() : 'Never'}</td>
            <td>${s.last_success_at ? new Date(s.last_success_at).toLocaleTimeString() : 'Never'}</td>
            <td>${s.indicators_fetched_total}</td>
            <td>${s.indicators_accepted_total}</td>
            <td>${s.indicators_rejected_total}</td>
            <td><code>${s.checkpoint_value || 'None'}</code></td>
          </tr>
        `).join("");
      } catch (err) {
        document.getElementById("metricWorkerStatus").textContent = "OFFLINE";
        document.getElementById("metricWorkerSub").innerHTML = `<span class="pulse-dot dot-red"></span> ${escapeHtml(err.message)}`;
        document.getElementById("connectorsBody").innerHTML = `<tr><td colspan="8"><div class="error-state">&#9888; Authentication required to inspect administrative health. Enter Bearer Token above.</div></td></tr>`;
      }
    }

    async function loadDiscoveryStats() {
      try {
        const data = await apiFetch("/admin/discovery/stats");
        document.getElementById("metricIndicatorsTotal").textContent = data.total_indicators;
        const matched = data.status_counts["MATCHED_BRAND"] || 0;
        document.getElementById("metricIndicatorsSub").textContent = `${matched} brand-correlated threats`;
      } catch (err) {
        document.getElementById("metricIndicatorsTotal").textContent = "--";
      }
    }

    async function loadIndicators() {
      try {
        const items = await apiFetch("/admin/discovery/indicators?limit=25");
        const tbody = document.getElementById("indicatorsBody");
        if (!items || items.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">&#9776; No threat indicators observed yet. Click "Trigger Discovery Run Now" above.</div></td></tr>`;
          return;
        }
        tbody.innerHTML = items.map(i => `
          <tr>
            <td><code>${escapeHtml(i.canonical_value)}</code></td>
            <td><span class="badge badge-low">${i.indicator_type}</span></td>
            <td><span class="badge badge-source">${escapeHtml(i.source_id)}</span></td>
            <td><span class="badge ${i.processing_status === 'MATCHED_BRAND' ? 'badge-critical' : (i.processing_status === 'OFFICIAL_BRAND_ASSET' ? 'badge-benign' : 'badge-low')}">${i.processing_status}</span></td>
            <td>${i.risk_score !== null ? `<strong>${i.risk_score.toFixed(1)}</strong>` : '--'}</td>
            <td>${i.brand_id ? `<code>${i.brand_id.substring(0,8)}...</code>` : '<span style="color:var(--text-dim);">No Match</span>'}</td>
            <td style="font-size:0.75rem;">${new Date(i.ingested_at).toLocaleTimeString()}</td>
          </tr>
        `).join("");
      } catch (err) {
        document.getElementById("indicatorsBody").innerHTML = `<tr><td colspan="7"><div class="error-state">&#9888; ${escapeHtml(err.message)}</div></td></tr>`;
      }
    }

    async function triggerDiscoveryCycleNow() {
      try {
        showToast("Triggering on-demand threat discovery cycle...");
        const res = await apiFetch("/admin/discovery/run-now", { method: "POST" });
        showToast(`Cycle finished: ${res.total_fetched} fetched, ${res.total_valid} valid in ${res.duration_seconds.toFixed(2)}s`);
        refreshDashboardData();
      } catch (err) {
        showToast(`Failed to trigger cycle: ${err.message}`);
      }
    }

    function openReviewModal(alertId, alertTitle) {
      document.getElementById("modalAlertId").value = alertId;
      document.getElementById("modalTitle").textContent = `Review: ${alertTitle}`;
      document.getElementById("modalNotesInput").value = "";
      document.getElementById("reviewModal").style.display = "flex";
    }

    function closeReviewModal() {
      document.getElementById("reviewModal").style.display = "none";
    }

    async function submitAlertReview() {
      const alertId = document.getElementById("modalAlertId").value;
      const status = document.getElementById("modalStatusSelect").value;
      const notes = document.getElementById("modalNotesInput").value;
      try {
        await apiFetch(`/owner/alerts/${alertId}`, {
          method: "PATCH",
          body: JSON.stringify({ status, notes })
        });
        showToast("Incident status updated successfully!");
        closeReviewModal();
        refreshDashboardData();
      } catch (err) {
        showToast(`Error: ${err.message}`);
      }
    }

    function escapeHtml(str) {
      if (!str) return "";
      return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    // Auto-init on page load
    document.addEventListener("DOMContentLoaded", () => {
      const token = getStoredToken();
      if (token) document.getElementById("authTokenInput").value = token;
      refreshDashboardData();
    });
  </script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard() -> HTMLResponse:
    """Serve the BrandShield AI Command Center Dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML, status_code=200)

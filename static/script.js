// チャート管理用レジストリ（canvas id をキーに Chart インスタンスを保持）
const charts = {};

// 比較分析の結果データと、描画済みパネルの管理
let comparisonData = null;
const renderedPanels = new Set();

// ===== Chart.js ダークテーマの共通設定 =====
const THEME = {
  indigo: '#818CF8',
  emerald: '#34D399',
  text: 'rgba(226, 232, 240, 0.85)',
  grid: 'rgba(148, 163, 184, 0.12)'
};

if (window.Chart) {
  Chart.defaults.color = THEME.text;
  Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Hiragino Kaku Gothic ProN", sans-serif';
  Chart.defaults.borderColor = THEME.grid;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 8;
}

// インディゴ→エメラルドのグラデーションを生成（縦/横）
function accentGradient(ctx, horizontal) {
  const area = ctx.canvas;
  const g = horizontal
    ? ctx.createLinearGradient(0, 0, area.width || 600, 0)
    : ctx.createLinearGradient(0, 0, 0, area.height || 400);
  g.addColorStop(0, 'rgba(129, 140, 248, 0.9)');
  g.addColorStop(1, 'rgba(52, 211, 153, 0.9)');
  return g;
}

// 初期化
document.addEventListener('DOMContentLoaded', function() {
  initializeUI();
  updateMysteryPrice();
  loadLayout();
  initScrollReveal();
});

// スクロールに合わせてふわっと浮き上がる演出
function initScrollReveal() {
  const targets = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    targets.forEach(el => el.classList.add('is-visible'));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  targets.forEach(el => observer.observe(el));
}

// UI初期化
function initializeUI() {
  const machineSelect = document.getElementById('machine-select');
  const trialSlider = document.getElementById('trial-slider');
  const trialCount = document.getElementById('trial-count');

  machineSelect.addEventListener('change', function() {
    updateMysteryPrice();
    loadLayout();
  });

  trialSlider.addEventListener('input', function() {
    trialCount.textContent = parseInt(this.value).toLocaleString();
  });

  document.getElementById('simulate-once-btn').addEventListener('click', simulateOnce);
  document.getElementById('simulate-btn').addEventListener('click', runSimulation);
  document.getElementById('comparison-btn').addEventListener('click', runComparison);
}

// 符号付き数値の文字列化
function signed(value) {
  return (value >= 0 ? '+' : '') + value;
}

// ミステリー価格更新
async function updateMysteryPrice() {
  try {
    const response = await fetch('/api/machines');
    const data = await response.json();
    const machine = document.getElementById('machine-select').value;
    const priceInfo = document.getElementById('mystery-price');
    const price = data.prices[machine];
    priceInfo.innerHTML = `<strong>ミステリー代金: ${price}円</strong>`;
  } catch (error) {
    console.error('Error fetching machines:', error);
  }
}

// ===== 実機配置の表示 =====
async function loadLayout() {
  const machine = document.getElementById('machine-select').value;

  try {
    const response = await fetch('/api/layout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ machine })
    });

    const data = await response.json();
    const wrap = document.getElementById('layout-table-wrap');
    wrap.innerHTML = buildLayoutTable(data.layout);
  } catch (error) {
    console.error('Error loading layout:', error);
  }
}

// 配置テーブルのHTMLを生成
function buildLayoutTable(layout) {
  let rows = '';

  for (const shelfName in layout) {
    let cells = '';
    layout[shelfName].forEach(item => {
      const mysteryClass = item.is_mystery ? ' mystery-cell' : '';
      cells += `
        <td class="layout-cell${mysteryClass}">
          <span class="cell-name">${item.name}</span>
          <span class="cell-price">${item.price}</span>
        </td>`;
    });
    rows += `
      <tr>
        <th class="shelf-label">${shelfName}</th>
        ${cells}
      </tr>`;
  }

  return `<table class="layout-table">${rows}</table>`;
}

// 1回のシミュレーション実行
async function simulateOnce() {
  const machine = document.getElementById('machine-select').value;
  const btn = document.getElementById('simulate-once-btn');

  btn.disabled = true;

  try {
    const response = await fetch('/api/simulate-once', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ machine })
    });

    const result = await response.json();

    const resultSection = document.getElementById('single-result');
    document.getElementById('result-item1').textContent = result.item1;
    document.getElementById('result-price1').textContent = result.price1 + '円';
    document.getElementById('result-item2').textContent = result.item2;
    document.getElementById('result-price2').textContent = result.price2 + '円';
    document.getElementById('result-total').textContent = result.total + '円';

    const profitEl = document.getElementById('result-profit');
    profitEl.textContent = signed(result.profit) + '円';

    document.getElementById('result-roi').textContent = signed(result.roi) + '%';

    resultSection.style.display = 'block';
  } catch (error) {
    console.error('Error:', error);
    alert('エラーが発生しました');
  } finally {
    btn.disabled = false;
  }
}

// 大規模シミュレーション実行
async function runSimulation() {
  const machine = document.getElementById('machine-select').value;
  const trials = parseInt(document.getElementById('trial-slider').value);
  const btn = document.getElementById('simulate-btn');

  btn.disabled = true;
  document.getElementById('loading').style.display = 'flex';
  document.getElementById('stats-section').style.display = 'none';
  document.getElementById('charts-section').style.display = 'none';
  document.getElementById('comparison-section').style.display = 'none';
  document.getElementById('single-result').style.display = 'none';

  try {
    const response = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ machine, trials })
    });

    const data = await response.json();
    displayStatistics(data.statistics);
    displayCharts(data);

    document.getElementById('loading').style.display = 'none';
    document.getElementById('stats-section').style.display = 'block';
    document.getElementById('charts-section').style.display = 'block';
  } catch (error) {
    console.error('Error:', error);
    alert('シミュレーション中にエラーが発生しました');
    document.getElementById('loading').style.display = 'none';
  } finally {
    btn.disabled = false;
  }
}

// 統計情報表示（単機）
function displayStatistics(stats) {
  document.getElementById('stat-avg-total').textContent = stats.avg_total + '円';
  document.getElementById('stat-avg-profit').textContent = signed(stats.avg_profit) + '円';
  document.getElementById('stat-avg-roi').textContent = signed(stats.avg_roi) + '%';
  document.getElementById('stat-loss-rate').textContent = stats.loss_rate + '%';
  document.getElementById('stat-max-profit').textContent = '+' + stats.max_profit + '円';
  document.getElementById('stat-min-profit').textContent = stats.min_profit + '円';
  document.getElementById('stat-std-dev').textContent = stats.std_dev + '円';
}

// グラフ表示（単機・固定canvas id）
function displayCharts(data) {
  renderProfitChart('profit-chart', data.profit_distribution);
  renderComboChart('combo-chart', data.top_combinations);
  renderProductChart('product-chart', data.product_appearance);
  renderBracketChart('bracket-chart', data.bracket_distribution);
}

// ===== チャート描画関数（canvas id をパラメータ化）=====

// 利益分布グラフ
function renderProfitChart(canvasId, profitData) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  if (charts[canvasId]) charts[canvasId].destroy();

  charts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: profitData.labels,
      datasets: [{
        label: '出現回数',
        data: profitData.data,
        backgroundColor: accentGradient(ctx, false),
        borderColor: 'transparent',
        borderRadius: 6,
        borderWidth: 0,
        maxBarThickness: 28
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: THEME.grid }, title: { display: true, text: '出現回数' } },
        x: { grid: { display: false }, title: { display: true, text: '利益（円）' } }
      }
    }
  });
}

// 組み合わせランキンググラフ
function renderComboChart(canvasId, comboData) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  if (charts[canvasId]) charts[canvasId].destroy();

  charts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: comboData.full_labels,
      datasets: [{
        label: '出現回数',
        data: comboData.data,
        backgroundColor: accentGradient(ctx, true),
        borderColor: 'transparent',
        borderRadius: 6,
        maxBarThickness: 22
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, grid: { color: THEME.grid } },
        y: { grid: { display: false } }
      }
    }
  });
}

// 商品出現確率グラフ
function renderProductChart(canvasId, productData) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  if (charts[canvasId]) charts[canvasId].destroy();

  charts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: productData.labels,
      datasets: [{
        label: '出現確率 (%)',
        data: productData.data,
        backgroundColor: accentGradient(ctx, true),
        borderColor: 'transparent',
        borderRadius: 6,
        maxBarThickness: 18
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, max: 10, grid: { color: THEME.grid } },
        y: { grid: { display: false } }
      }
    }
  });
}

// 利益帯別分布グラフ
function renderBracketChart(canvasId, bracketData) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  if (charts[canvasId]) charts[canvasId].destroy();

  const colors = ['#F87171', '#FB923C', '#FBBF24', '#34D399', '#818CF8'];

  charts[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: bracketData.labels,
      datasets: [{
        data: bracketData.data,
        backgroundColor: colors,
        borderColor: 'rgba(15, 23, 42, 0.6)',
        borderWidth: 3,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '62%',
      plugins: {
        legend: { position: 'right' },
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.label + ': ' + context.parsed + '%';
            }
          }
        }
      }
    }
  });
}

// ===== 複数自販機比較 =====
async function runComparison() {
  const trials = parseInt(document.getElementById('trial-slider').value);
  const btn = document.getElementById('comparison-btn');

  btn.disabled = true;
  document.getElementById('loading').style.display = 'flex';
  document.getElementById('comparison-section').style.display = 'none';
  document.getElementById('stats-section').style.display = 'none';
  document.getElementById('charts-section').style.display = 'none';
  document.getElementById('single-result').style.display = 'none';

  try {
    const response = await fetch('/api/comparison', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trials })
    });

    const data = await response.json();
    comparisonData = data;
    renderedPanels.clear();

    displayComparisonSummary(data.comparison);
    buildMachineTabs(data.machines);

    document.getElementById('loading').style.display = 'none';
    document.getElementById('comparison-section').style.display = 'block';
  } catch (error) {
    console.error('Error:', error);
    alert('比較中にエラーが発生しました');
    document.getElementById('loading').style.display = 'none';
  } finally {
    btn.disabled = false;
  }
}

// 比較サマリー（表＋平均利益グラフ）
function displayComparisonSummary(comparison) {
  const tbody = document.querySelector('.comparison-table tbody');
  tbody.innerHTML = '';

  comparison.forEach(item => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><strong>${item.machine}</strong></td>
      <td>${item.mystery_price}円</td>
      <td>${signed(item.avg_profit)}円</td>
      <td>${signed(item.avg_roi)}%</td>
      <td>${item.loss_rate}%</td>
    `;
    tbody.appendChild(row);
  });

  const ctx = document.getElementById('comparison-chart').getContext('2d');
  if (charts['comparison-chart']) charts['comparison-chart'].destroy();

  charts['comparison-chart'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: comparison.map(item => item.machine),
      datasets: [{
        label: '平均利益（円）',
        data: comparison.map(item => item.avg_profit),
        backgroundColor: accentGradient(ctx, false),
        borderColor: 'transparent',
        borderRadius: 8,
        maxBarThickness: 90
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: THEME.grid },
          ticks: { callback: function(value) { return value + '円'; } }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

// 自販機別タブと詳細パネルの構築
function buildMachineTabs(machines) {
  const tabsEl = document.getElementById('machine-tabs');
  const detailsEl = document.getElementById('machine-details');

  // タブボタン
  tabsEl.innerHTML = machines.map((m, i) =>
    `<button class="tab-btn ${i === 0 ? 'active' : ''}" data-index="${i}">${m.machine}</button>`
  ).join('');

  // 詳細パネル（最初の1つだけ表示）
  detailsEl.innerHTML = machines.map((m, i) =>
    buildMachinePanel(m, i)
  ).join('');

  // タブ切り替えイベント
  tabsEl.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const index = parseInt(this.dataset.index);
      switchTab(index);
    });
  });

  // 最初のパネルのグラフを描画
  renderPanelCharts(0);
}

// 1自販機分の詳細パネルHTMLを生成
function buildMachinePanel(machine, index) {
  const s = machine.statistics;
  const display = index === 0 ? 'block' : 'none';

  const statsGrid = `
    <div class="stats-grid">
      ${statCard('平均獲得価格', s.avg_total + '円')}
      ${statCard('平均利益', signed(s.avg_profit) + '円')}
      ${statCard('平均ROI', signed(s.avg_roi) + '%')}
      ${statCard('赤字確率', s.loss_rate + '%')}
      ${statCard('最高利益', '+' + s.max_profit + '円')}
      ${statCard('最低利益', s.min_profit + '円')}
      ${statCard('標準偏差', s.std_dev + '円')}
    </div>`;

  return `
    <div class="machine-panel" id="panel-${index}" style="display: ${display};">
      <h3 class="panel-title">${machine.machine}（ミステリー ${machine.mystery_price}円）</h3>

      <div class="chart-container">
        <h3>🗺️ 配置</h3>
        <div class="layout-table-wrap">${buildLayoutTable(machine.layout)}</div>
      </div>

      ${statsGrid}

      <div class="chart-container">
        <h3>📊 利益分布</h3>
        <canvas id="profit-chart-${index}"></canvas>
      </div>
      <div class="chart-container">
        <h3>🏆 最も出現しやすい組み合わせ TOP10</h3>
        <canvas id="combo-chart-${index}"></canvas>
      </div>
      <div class="chart-container">
        <h3>📦 商品出現確率 TOP15</h3>
        <canvas id="product-chart-${index}"></canvas>
      </div>
      <div class="chart-container">
        <h3>💰 利益帯別の確率分布</h3>
        <canvas id="bracket-chart-${index}"></canvas>
      </div>
    </div>`;
}

// 統計カードのHTML
function statCard(label, value) {
  return `
    <div class="stat-card">
      <div class="stat-label">${label}</div>
      <div class="stat-value">${value}</div>
    </div>`;
}

// タブ切り替え
function switchTab(index) {
  // タブボタンのアクティブ状態
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', parseInt(btn.dataset.index) === index);
  });

  // パネルの表示切り替え
  document.querySelectorAll('.machine-panel').forEach(panel => {
    panel.style.display = panel.id === `panel-${index}` ? 'block' : 'none';
  });

  // 未描画ならグラフを描画（display:none での描画崩れを防ぐ遅延描画）
  renderPanelCharts(index);
}

// 指定パネルのグラフを描画（描画済みならスキップ）
function renderPanelCharts(index) {
  if (renderedPanels.has(index)) return;
  if (!comparisonData) return;

  const m = comparisonData.machines[index];
  renderProfitChart(`profit-chart-${index}`, m.profit_distribution);
  renderComboChart(`combo-chart-${index}`, m.top_combinations);
  renderProductChart(`product-chart-${index}`, m.product_appearance);
  renderBracketChart(`bracket-chart-${index}`, m.bracket_distribution);

  renderedPanels.add(index);
}

/* ==========================================================================
   chrome-bookmarks-organize · Chart.js 图表配置与数据
   数据来源：MAINTENANCE.md §8 变更日志中的真实回归测试计数
   （v1.6.0 引入 run_tests.py 起逐版真实记录，v1.11~v1.12 为文档层改动未增删）
   ========================================================================== */
(() => {
  'use strict';

  const GUARD = { /* 里程碑版本 */ x: [
    'v1.6.0', 'v1.7.0', 'v1.8.0', 'v1.9.0', 'v1.10.0', 'v1.13.0', 'v1.14.0'
  ], /* 对应回归测试项数 */ y: [28, 32, 42, 46, 48, 54, 54] };

  // 跟随 CSS 变量取主题色；未应用（深色默认变量未设时）退回系统
  const cssVar = (name, fallback) => {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  };
  const isDark = () => {
    const t = document.documentElement.getAttribute('data-theme');
    if (t) return t === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  };
  const scheme = () => ({
    grid: cssVar('--border', isDark() ? '#24304a' : '#e2e8f0'),
    text: cssVar('--text-dim', isDark() ? '#94a3b8' : '#5b6b84'),
    brand: cssVar('--brand', '#4f46e5'),
    brand2: cssVar('--brand-2', '#06b6d4'),
    accent: cssVar('--accent', '#10b981'),
  });

  function drawGuard() {
    const canvas = document.getElementById('guardChart');
    if (!canvas || typeof Chart === 'undefined') return;

    const c = scheme();
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.parentElement.clientHeight || 280);
    gradient.addColorStop(0, 'rgba(79,70,229,.32)');
    gradient.addColorStop(1, 'rgba(79,70,229,0)');

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: GUARD.x,
        datasets: [{
          label: '回归测试项数',
          data: GUARD.y,
          borderColor: c.brand2,
          backgroundColor: gradient,
          fill: true,
          tension: 0.32,
          pointBackgroundColor: GUARD.y.map((v, i) => i === GUARD.y.length - 1 ? c.accent : c.brand2),
          pointBorderColor: c.bgElev || '#fff',
          pointRadius: GUARD.y.map((v, i) => i === GUARD.y.length - 1 ? 6 : 4),
          borderWidth: 2.5,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: isDark() ? '#131a2e' : '#ffffff',
            titleColor: c.text,
            bodyColor: c.text,
            borderColor: c.grid,
            borderWidth: 1,
            padding: 10,
            displayColors: false,
            callbacks: { label: (i) => `${i.parsed.y} 项回归测试` },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: c.text, font: { size: 11 } } },
          y: {
            beginAtZero: false,
            suggestedMin: 20,
            suggestedMax: 60,
            grid: { color: c.grid, drawTicks: false },
            ticks: { color: c.text, padding: 6, font: { size: 11 } },
          },
        },
      },
    });
  }

  // 若主题被切换，图表颜色不再重绘——属可接受的静态降级；切换时手动重绘：
  document.getElementById('themeToggle')?.addEventListener('click', () => {
    setTimeout(() => {
      const holder = document.getElementById('guardChart');
      if (holder) {
        Chart.getChart(holder)?.destroy();
        drawGuard();
      }
    }, 30);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', drawGuard);
  } else {
    drawGuard();
  }
})();

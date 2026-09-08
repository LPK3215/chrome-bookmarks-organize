/* ==========================================================================
   chrome-bookmarks-organize · Chart.js 图表配置与数据
   数据来源（全部来自仓库真实状态，非估算）：
     1) 回归项数：scripts/test/run_tests.py 当前 54 项；
        历史数值取自 MAINTENANCE.md §8 变更日志逐版记录
        （v1.11 / v1.12 为文档层改动，未增删断言，故不单列）
     2) 样例归类分布：scripts/test/sample/Bookmarks.after 的 7 个类目目录
        （购物 / 新闻资讯 / 技术开发 / 学习资源 / 视频娱乐 / 生活工具 / 博客与阅读）
   ========================================================================== */
(() => {
  'use strict';

  if (typeof Chart === 'undefined') return;

  /* ---------- 主题色 ---------- */
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
    grid: cssVar('--border', isDark() ? '#1c2740' : '#e3e9f3'),
    text: cssVar('--dim', isDark() ? '#93a5c2' : '#55677f'),
    blue: cssVar('--blue', '#4285f4'),
    green: cssVar('--green', '#34a853'),
    yellow: cssVar('--yellow', '#fbbc05'),
    red: cssVar('--red', '#ea4335'),
    purple: cssVar('--purple', '#8b5cf6')
  });

  Chart.defaults.font.family = getComputedStyle(document.documentElement)
    .getPropertyValue('--font-ui').trim() || 'Inter, system-ui, sans-serif';
  Chart.defaults.font.size = 12;

  const charts = [];
  const register = (c) => { if (c) charts.push(c); };

  /* ---------- 图 1：回归护栏增长 ---------- */
  const GUARD = {
    labels: ['v1.6.0', 'v1.7.0', 'v1.8.0', 'v1.9.0', 'v1.10.0', 'v1.13.0', 'v1.14.4'],
    values: [28, 32, 42, 46, 48, 54, 54],
    notes: [
      '首次引入 run_tests.py',
      '新增云端同步感知',
      '占用锁 + 最小参数路径',
      '底牌校验 / 拒绝自我覆盖',
      '数量护栏（防丢书签）',
      '脏输入边界加固 6 项',
      '文档 / 部署层，行为零变化'
    ]
  };

  function drawGuard() {
    const canvas = document.getElementById('guardChart');
    if (!canvas) return null;
    const c = scheme();
    const ctx = canvas.getContext('2d');
    const grad = ctx.createLinearGradient(0, 0, 0, 230);
    grad.addColorStop(0, c.blue + 'cc');
    grad.addColorStop(1, c.blue + '10');

    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: GUARD.labels,
        datasets: [{
          label: '回归测试项数',
          data: GUARD.values,
          backgroundColor: grad,
          borderColor: c.blue,
          borderWidth: 1.5,
          borderRadius: 7,
          maxBarThickness: 44
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: isDark() ? '#131c2e' : '#0d1626',
            borderColor: c.grid,
            borderWidth: 1,
            padding: 10,
            displayColors: false,
            callbacks: {
              label: (ctx) => `${ctx.parsed.y} 项 · ${GUARD.notes[ctx.dataIndex]}`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: c.text, font: { size: 11 } }, border: { color: c.grid } },
          y: { beginAtZero: true, max: 60, grid: { color: c.grid, drawTicks: false }, ticks: { color: c.text, stepSize: 15 }, border: { display: false } }
        },
        animation: { duration: 900, easing: 'easeOutQuart' }
      }
    });
  }

  /* ---------- 图 2：样例归类分布（after 的 7 个类目） ---------- */
  const SAMPLE = {
    labels: ['购物', '新闻资讯', '技术开发', '学习资源', '视频娱乐', '生活工具', '博客与阅读'],
    values: [6, 6, 6, 6, 6, 6, 2]
  };

  function drawSample() {
    const canvas = document.getElementById('sampleChart');
    if (!canvas) return null;
    const c = scheme();
    const palette = [c.blue, c.green, c.yellow, c.red, c.purple, c.blue, c.green];

    return new Chart(canvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: SAMPLE.labels,
        datasets: [{
          label: '书签条数',
          data: SAMPLE.values,
          backgroundColor: palette.map((p) => p + '55'),
          borderColor: palette,
          borderWidth: 1.5,
          borderRadius: 6,
          maxBarThickness: 28
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: isDark() ? '#131c2e' : '#0d1626',
            borderColor: c.grid,
            borderWidth: 1,
            padding: 10,
            displayColors: false,
            callbacks: { label: (ctx) => `${ctx.parsed.x} 条书签` }
          }
        },
        scales: {
          x: { beginAtZero: true, grid: { color: c.grid, drawTicks: false }, ticks: { color: c.text, stepSize: 2 }, border: { display: false } },
          y: { grid: { display: false }, ticks: { color: c.text }, border: { color: c.grid } }
        },
        animation: { duration: 900, easing: 'easeOutQuart' }
      }
    });
  }

  /* ---------- 初始化 & 主题切换重绘 ---------- */
  const build = () => {
    charts.forEach((c) => c.destroy());
    charts.length = 0;
    register(drawGuard());
    register(drawSample());
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }

  let raf = null;
  window.addEventListener('themechange', () => {
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(build);
  });
})();

/* ==========================================================================
   chrome-bookmarks-organize · 全景观览页交互
   ========================================================================== */
(() => {
  'use strict';

  /* ---------- 主题：默认跟随系统，手动切换持久化 ---------- */
  const root = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const saved = localStorage.getItem('bm-theme');
  if (saved) root.setAttribute('data-theme', saved);
  themeToggle.addEventListener('click', () => {
    const cur = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    const next = cur === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('bm-theme', next);
  });

  /* ---------- 滚动进度条 ---------- */
  const progress = document.getElementById('progress');
  const updateProgress = () => {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    progress.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
  };
  document.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();

  /* ---------- 导航高亮 + 平滑滚动 ---------- */
  const navLinks = document.querySelectorAll('#navLinks a[data-nav]');
  const sections = [...navLinks].map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
  const navObserver = new IntersectionObserver((entries) => {
    entries.forEach(en => {
      if (en.isIntersecting) {
        navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + en.target.id));
      }
    });
  }, { rootMargin: '-38% 0px -55% 0px' });
  sections.forEach(s => navObserver.observe(s));

  navLinks.forEach(a => a.addEventListener('click', (e) => {
    e.preventDefault();
    const t = document.querySelector(a.getAttribute('href'));
    if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    document.getElementById('navLinks').classList.remove('open');
  }));

  /* ---------- 移动端汉堡菜单 ---------- */
  document.getElementById('hamburger').addEventListener('click', () => {
    document.getElementById('navLinks').classList.toggle('open');
  });

  /* ---------- Tab 切换（快速开始三路 + 图表/表格） ---------- */
  const bindTabs = (scope) => {
    scope.querySelectorAll('[role="tab"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const host = btn.closest('.tabs, .tabrow');
        if (!host) return;
        // 面板宿主：.tabs 配 .tab-panel，.tabrow 配 .panel（同处 .chart-card）
        const isMini = btn.classList.contains('tab-mini');
        host.querySelectorAll('[role="tab"]').forEach(t => {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        const container = isMini ? btn.closest('.chart-card') : host.parentElement;
        if (!container) return;
        const kind = isMini ? '.panel' : '.tab-panel';
        container.querySelectorAll(kind).forEach(p =>
          p.classList.toggle('active', p.id === btn.dataset.tab));
      });
    });
  };
  bindTabs(document);

  /* ---------- 数字动画 ---------- */
  const animateNum = (el) => {
    const target = parseInt(el.dataset.count, 10);
    if (Number.isNaN(target)) return;
    const dur = 1100, t0 = performance.now();
    const step = (now) => {
      const p = Math.min((now - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased);
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = target;
    };
    requestAnimationFrame(step);
  };
  const statObs = new IntersectionObserver((entries) => {
    entries.forEach(en => {
      if (en.isIntersecting) {
        en.target.querySelectorAll('[data-count]').forEach(animateNum);
        statObs.unobserve(en.target);
      }
    });
  }, { threshold: 0.4 });
  const statsBox = document.getElementById('stats');
  if (statsBox) statObs.observe(statsBox);

  /* ---------- 架构图：hover tooltip ---------- */
  const tipBox = document.getElementById('svgTip');
  if (tipBox) {
    document.querySelectorAll('.arch-svg .node').forEach(n => {
      const on = () => {
        const t = n.dataset.tip;
        if (t) { tipBox.textContent = t; tipBox.style.display = 'block'; }
      };
      const off = () => { tipBox.style.display = 'none'; };
      n.addEventListener('mouseenter', on);
      n.addEventListener('focus', on);
      n.addEventListener('mouseleave', off);
      n.addEventListener('blur', off);
      n.setAttribute('tabindex', '0');
      n.setAttribute('role', 'button');
      n.setAttribute('aria-label', n.dataset.tip || '节点');
    });
  }

  /* ---------- 代码复制 ---------- */
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const code = document.getElementById(btn.dataset.copy);
      const txt = code ? code.innerText : '';
      try {
        await navigator.clipboard.writeText(txt);
      } catch (_) {
        const ta = document.createElement('textarea');
        ta.value = txt; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); } catch (__) {}
        ta.remove();
      }
      const old = btn.textContent;
      btn.textContent = '已复制 ✓';
      btn.classList.add('copy-ok');
      setTimeout(() => { btn.textContent = old; btn.classList.remove('copy-ok'); }, 1600);
    });
  });

  /* ---------- 返回顶部 ---------- */
  const toTop = document.getElementById('toTop');
  document.addEventListener('scroll', () => {
    toTop.classList.toggle('show', window.scrollY > window.innerHeight * 0.9);
  }, { passive: true });
  toTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  /* ---------- 页面底部滚动状态（隐藏底部 footer 锚点冲突用） ---------- */
  // 文档卡片通过 target=_blank 直接打开源文件，不需要额外处理
})();

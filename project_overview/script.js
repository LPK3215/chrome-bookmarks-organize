/* ==========================================================================
   chrome-bookmarks-organize · 项目全景观览页交互逻辑
   模块：主题切换 / 滚动进度 / 导航高亮 / 演示卡 / 计数动画 / Tab / 复制 /
        SVG tooltip / 目录树 / 回到顶部 / 入场动画
   ========================================================================== */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------- 主题 ---------- */
  const THEME_KEY = 'cbm-overview-theme';
  const root = document.documentElement;
  const moon = $('#iconMoon');
  const sun = $('#iconSun');

  const applyTheme = (t) => {
    root.setAttribute('data-theme', t);
    if (moon) moon.style.display = t === 'dark' ? 'none' : 'block';
    if (sun) sun.style.display = t === 'dark' ? 'block' : 'none';
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: t } }));
  };

  const saved = localStorage.getItem(THEME_KEY);
  applyTheme(saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));

  const toggle = $('#themeToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      localStorage.setItem(THEME_KEY, next);
      applyTheme(next);
    });
  }

  /* ---------- 滚动进度条 + 导航状态 + 回到顶部 ---------- */
  const bar = $('#progress');
  const nav = $('#nav');
  const toTop = $('#toTop');

  const onScroll = () => {
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    const pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
    if (bar) bar.style.width = pct + '%';
    if (nav) nav.classList.toggle('is-stuck', doc.scrollTop > 8);
    if (toTop) toTop.classList.toggle('is-show', doc.scrollTop > doc.clientHeight * 0.7);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (toTop) {
    toTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  /* ---------- 汉堡菜单 ---------- */
  const hamburger = $('#hamburger');
  const navLinks = $('#navLinks');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      const open = navLinks.classList.toggle('is-open');
      hamburger.setAttribute('aria-expanded', String(open));
    });
    navLinks.addEventListener('click', (e) => {
      if (e.target.tagName === 'A') {
        navLinks.classList.remove('is-open');
        hamburger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------- 导航高亮 ---------- */
  const navItems = $$('[data-nav]');
  const sections = navItems.map((a) => $(a.getAttribute('href'))).filter(Boolean);
  if (sections.length && 'IntersectionObserver' in window) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        const id = '#' + en.target.id;
        navItems.forEach((a) => a.classList.toggle('is-active', a.getAttribute('href') === id));
      });
    }, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });
    sections.forEach((s) => spy.observe(s));
  }

  /* ---------- 演示卡：整理前 / 整理后 ---------- */
  const demo = $('#demo');
  if (demo) {
    const btns = $$('.ds-btn', demo);
    const views = $$('.demo-view', demo);
    const stat = $('#demoStat');
    const STATS = {
      before: '40 条 · 平铺 + 3 个「新建文件夹」',
      after: '38 条 · 归入 7 个类目目录（去重 1 / 清理 1）'
    };
    let timer = null;

    const setView = (name) => {
      btns.forEach((b) => {
        const on = b.dataset.view === name;
        b.classList.toggle('is-active', on);
        b.setAttribute('aria-selected', String(on));
      });
      views.forEach((v) => v.classList.toggle('is-active', v.dataset.view === name));
      if (stat) stat.textContent = STATS[name] || '';
    };
    const start = () => { stop(); timer = setInterval(() => {
      setView($('.ds-btn.is-active', demo).dataset.view === 'before' ? 'after' : 'before');
    }, 5000); };
    const stop = () => { if (timer) { clearInterval(timer); timer = null; } };

    btns.forEach((b) => b.addEventListener('click', () => { setView(b.dataset.view); start(); }));
    demo.addEventListener('mouseenter', stop);
    demo.addEventListener('mouseleave', start);
    start();
  }

  /* ---------- 数字计数动画 ---------- */
  const countUp = (el) => {
    const target = Number(el.dataset.count || 0);
    if (!target) { el.textContent = '0'; return; }
    const dur = 1100;
    const t0 = performance.now();
    const tick = (now) => {
      const p = Math.min((now - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString('en-US');
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  if ('IntersectionObserver' in window) {
    const numObs = new IntersectionObserver((entries, obs) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        countUp(en.target);
        obs.unobserve(en.target);
      });
    }, { threshold: .6 });
    $$('[data-count]').forEach((el) => numObs.observe(el));

    const revObs = new IntersectionObserver((entries, obs) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        en.target.classList.add('is-in');
        obs.unobserve(en.target);
      });
    }, { threshold: .12, rootMargin: '0px 0px -40px 0px' });
    $$('.sec, .card, .guard, .step-card, .limit, .doc-card, .ci-card, .s3').forEach((el, i) => {
      el.classList.add('reveal');
      el.style.transitionDelay = (i % 4) * 60 + 'ms';
      revObs.observe(el);
    });
  }

  /* ---------- Tab 切换（通用） ---------- */
  $$('.tab-bar').forEach((barEl) => {
    const wrap = barEl.closest('.tabs');
    const btns = $$('.tab-btn', barEl);
    btns.forEach((b) => b.addEventListener('click', () => {
      btns.forEach((x) => {
        const on = x === b;
        x.classList.toggle('is-active', on);
        x.setAttribute('aria-selected', String(on));
      });
      $$('.tab-panel', wrap).forEach((p) => p.classList.toggle('is-active', p.id === b.dataset.tab));
    }));
  });

  /* ---------- 图表 / 表格 分段切换 ---------- */
  $$('.seg').forEach((seg) => {
    const scope = seg.closest('.card') || document;
    const btns = $$('.seg-btn', seg);
    btns.forEach((b) => b.addEventListener('click', () => {
      btns.forEach((x) => x.classList.toggle('is-active', x === b));
      $$('.q-view', scope).forEach((v) => v.classList.toggle('is-active', v.dataset.view === b.dataset.view));
    }));
  });

  /* ---------- 代码复制 ---------- */
  $$('.copy-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const code = btn.closest('.code')?.querySelector('code');
      if (!code) return;
      const text = code.innerText;
      try {
        await navigator.clipboard.writeText(text);
      } catch (e) {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
      }
      const old = btn.textContent;
      btn.textContent = '已复制';
      btn.classList.add('is-done');
      setTimeout(() => { btn.textContent = old; btn.classList.remove('is-done'); }, 1600);
    });
  });

  /* ---------- SVG 节点 tooltip ---------- */
  const tip = $('#svgTip');
  if (tip) {
    const show = (e, text) => {
      tip.textContent = text;
      tip.classList.add('is-show');
      const pad = 14;
      const w = tip.offsetWidth;
      const h = tip.offsetHeight;
      let x = e.clientX + pad;
      let y = e.clientY + pad;
      if (x + w > window.innerWidth - 10) x = e.clientX - w - pad;
      if (y + h > window.innerHeight - 10) y = e.clientY - h - pad;
      tip.style.left = Math.max(8, x) + 'px';
      tip.style.top = Math.max(8, y) + 'px';
    };
    const hide = () => tip.classList.remove('is-show');
    $$('.node[data-tip]').forEach((n) => {
      n.addEventListener('mouseenter', (e) => show(e, n.dataset.tip));
      n.addEventListener('mousemove', (e) => show(e, n.dataset.tip));
      n.addEventListener('mouseleave', hide);
    });
  }

  /* ---------- 目录树折叠 ---------- */
  $$('.tree .t-dir > .t-row').forEach((row) => {
    row.addEventListener('click', () => row.parentElement.classList.toggle('open'));
  });
  const setTree = (open) => $$('.tree .t-dir').forEach((d) => d.classList.toggle('open', open));
  const exp = $('#treeExpand');
  const col = $('#treeCollapse');
  if (exp) exp.addEventListener('click', () => setTree(true));
  if (col) col.addEventListener('click', () => setTree(false));

  /* ---------- 锚点平滑滚动（兼容老浏览器） ---------- */
  $$('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id.length < 2) return;
      const target = $(id);
      if (!target) return;
      e.preventDefault();
      const top = target.getBoundingClientRect().top + window.scrollY - 76;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
})();

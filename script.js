document.addEventListener('DOMContentLoaded', function () {
  // Disable auto-rotate on mobile to save GPU
  if (window.innerWidth < 768) {
    document.querySelectorAll('model-viewer').forEach(mv => mv.removeAttribute('auto-rotate'));
  }

  const navToggle = document.getElementById('nav-toggle');
  const siteHeader = document.querySelector('.site-header');
  const navToggleLabel = document.querySelector('.nav-toggle-label');
  const nav = document.querySelector('.nav');

  // Robust mobile menu toggle (JS-driven, not relying on CSS :checked)
  if (navToggleLabel && nav) {
    navToggleLabel.addEventListener('click', function (e) {
      e.preventDefault();
      nav.classList.toggle('is-open');
      if (navToggle) navToggle.checked = nav.classList.contains('is-open');
      if (siteHeader) siteHeader.classList.toggle('nav-open', nav.classList.contains('is-open'));
      navToggleLabel.textContent = nav.classList.contains('is-open') ? '✕ Menu' : '☰ Menu';
    });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        nav.classList.remove('is-open');
        if (navToggle) navToggle.checked = false;
        if (siteHeader) siteHeader.classList.remove('nav-open');
        navToggleLabel.textContent = '☰ Menu';
      });
    });
    // Close when clicking outside the header
    document.addEventListener('click', function (e) {
      if (!siteHeader) return;
      if (!siteHeader.contains(e.target) && nav.classList.contains('is-open')) {
        nav.classList.remove('is-open');
        if (navToggle) navToggle.checked = false;
        siteHeader.classList.remove('nav-open');
        navToggleLabel.textContent = '☰ Menu';
      }
    });
  }

  if (navToggle && siteHeader) {
    navToggle.addEventListener('change', function () {
      siteHeader.classList.toggle('nav-open', navToggle.checked);
      if (nav) nav.classList.toggle('is-open', navToggle.checked);
    });
  }

  const targets = document.querySelectorAll('section, .card-dark, .service-card, .product, .project, .feature');
  targets.forEach(el => el.classList.add('reveal'));
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.01, rootMargin: '0px 0px -5% 0px' });
  targets.forEach(el => observer.observe(el));
});

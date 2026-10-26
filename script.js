document.addEventListener('DOMContentLoaded', function () {
  const navDetails = document.querySelector('.nav-details');
  function syncNav() {
    if (!navDetails) return;
    if (window.innerWidth >= 961) {
      navDetails.open = true;
    } else {
      navDetails.open = false;
    }
  }
  syncNav();
  window.addEventListener('resize', syncNav);

  const targets = document.querySelectorAll('section, .card-dark, .service-card, .product, .project, .feature');
  targets.forEach(el => el.classList.add('reveal'));
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  targets.forEach(el => observer.observe(el));
});

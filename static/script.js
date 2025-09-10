document.addEventListener("DOMContentLoaded", () => {
  const fadeSlides = document.querySelectorAll('.fade-slide');

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1
  });

  fadeSlides.forEach(el => observer.observe(el));
});

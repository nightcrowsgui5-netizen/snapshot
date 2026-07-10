/* Hero - troca automatica de imagens de fundo a cada 5s (com fade via CSS) */
(function () {
  "use strict";
  function start() {
    var slides = document.querySelectorAll("#home .hero-slide");
    if (slides.length < 2) return;
    var i = 0;
    setInterval(function () {
      slides[i].classList.remove("active");
      i = (i + 1) % slides.length;
      slides[i].classList.add("active");
    }, 5000);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();

/* Galeria "Projetos Selecionados" - filtro por abas (categorias) */
(function () {
  "use strict";
  function init() {
    var tabs = document.querySelectorAll("#work .gallery-tab");
    var items = document.querySelectorAll("#work .gallery-item");
    if (!tabs.length || !items.length) return;

    function show(cat) {
      items.forEach(function (it) {
        it.style.display = (it.getAttribute("data-cat") === cat) ? "" : "none";
      });
      tabs.forEach(function (t) {
        t.classList.toggle("active", t.getAttribute("data-cat") === cat);
      });
    }

    tabs.forEach(function (t) {
      t.addEventListener("click", function () {
        show(t.getAttribute("data-cat"));
      });
    });

    // inicia mostrando a primeira aba
    show(tabs[0].getAttribute("data-cat"));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

(() => {
  "use strict";
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];

  function initSlider(){
    const root = $("[data-home-slider]");
    if(!root) return;

    const slides = $$("[data-home-slide]", root);
    const dots = $$("[data-home-slider-dot]", root);
    const current = $("[data-slider-current]", root);
    if(!slides.length) return;

    let index = 0;
    let timer = null;

    function show(i){
      index = (i + slides.length) % slides.length;
      slides.forEach((slide, n) => slide.classList.toggle("is-active", n === index));
      dots.forEach((dot, n) => dot.classList.toggle("is-active", n === index));
      if(current) current.textContent = String(index + 1).padStart(2, "0");
    }

    function stop(){
      if(timer){ clearInterval(timer); timer = null; }
    }

    function start(){
      stop();
      timer = setInterval(() => show(index + 1), 5200);
    }

    dots.forEach(dot => {
      dot.addEventListener("click", () => {
        show(Number(dot.dataset.homeSliderDot || 0));
        start();
      });
    });

    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    show(0);
    start();
  }

  document.addEventListener("click", event => {
    const btn = event.target.closest("[data-auth-password]");
    if(!btn) return;

    const input = document.getElementById(btn.dataset.authPassword);
    if(!input) return;

    const show = input.type === "password";
    input.type = show ? "text" : "password";

    const icon = btn.querySelector("i");
    if(icon){
      icon.classList.toggle("fa-eye", !show);
      icon.classList.toggle("fa-eye-slash", show);
    }
  });

  document.addEventListener("DOMContentLoaded", initSlider);
})();

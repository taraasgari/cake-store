(() => {
  "use strict";
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];

  function initSlider(){
    const root = $("[data-home-slider]");
    if(!root || root.dataset.sliderReady === "1") return;
    root.dataset.sliderReady = "1";

    const slides = $$("[data-home-slide]", root);
    const dots = $$("[data-home-slider-dot]", root);
    const current = $("[data-slider-current]", root);
    if(!slides.length) return;

    let index = Math.max(0, slides.findIndex(slide => slide.classList.contains("is-active")));
    if(index < 0) index = 0;
    let timer = 0;

    function paint(){
      slides.forEach((slide, n) => {
        const active = n === index;
        slide.classList.toggle("is-active", active);
        slide.setAttribute("aria-hidden", String(!active));
        slide.style.opacity = active ? "1" : "0";
        slide.style.visibility = active ? "visible" : "hidden";
        slide.style.pointerEvents = active ? "auto" : "none";
        slide.style.zIndex = active ? "2" : "0";
      });
      dots.forEach((dot, n) => {
        const active = n === index;
        dot.classList.toggle("is-active", active);
        dot.setAttribute("aria-current", active ? "true" : "false");
      });
      if(current) current.textContent = String(index + 1).padStart(2, "0");
    }

    function show(nextIndex){
      index = (Number(nextIndex) + slides.length) % slides.length;
      paint();
    }

    function stop(){
      if(timer){
        window.clearTimeout(timer);
        timer = 0;
      }
    }

    function schedule(){
      stop();
      if(slides.length < 2 || document.hidden) return;
      timer = window.setTimeout(() => {
        show(index + 1);
        schedule();
      }, 3000);
    }

    function go(nextIndex){
      show(nextIndex);
      schedule();
    }

    root.addEventListener("click", event => {
      const prev = event.target.closest("[data-home-slider-prev]");
      if(prev){
        event.preventDefault();
        event.stopPropagation();
        go(index - 1);
        return;
      }
      const next = event.target.closest("[data-home-slider-next]");
      if(next){
        event.preventDefault();
        event.stopPropagation();
        go(index + 1);
        return;
      }
      const dot = event.target.closest("[data-home-slider-dot]");
      if(dot){
        event.preventDefault();
        event.stopPropagation();
        go(parseInt(dot.dataset.homeSliderDot || "0", 10));
      }
    });

    let touchX = null;
    root.addEventListener("touchstart", event => {
      touchX = event.touches?.[0]?.clientX ?? null;
    }, {passive:true});
    root.addEventListener("touchend", event => {
      if(touchX === null) return;
      const endX = event.changedTouches?.[0]?.clientX ?? touchX;
      const delta = endX - touchX;
      touchX = null;
      if(Math.abs(delta) >= 45) go(delta > 0 ? index - 1 : index + 1);
    }, {passive:true});

    document.addEventListener("visibilitychange", () => {
      if(document.hidden) stop(); else schedule();
    });

    paint();
    schedule();
  }

  function initAccountMenus(){
    const menus = $$('[data-p4-account-menu]');
    if(!menus.length) return;

    const closeAll = except => {
      menus.forEach(menu => {
        if(menu !== except && menu.open) menu.removeAttribute('open');
      });
    };

    menus.forEach(menu => {
      menu.addEventListener('toggle', () => {
        if(menu.open) closeAll(menu);
      });
      menu.querySelectorAll('a, form button[type="submit"]').forEach(control => {
        control.addEventListener('click', () => menu.removeAttribute('open'));
      });
    });

    document.addEventListener('pointerdown', event => {
      menus.forEach(menu => {
        if(menu.open && !menu.contains(event.target)) menu.removeAttribute('open');
      });
    });
    document.addEventListener('keydown', event => {
      if(event.key === 'Escape') closeAll();
    });
    window.addEventListener('scroll', () => closeAll(), {passive:true});
    window.addEventListener('blur', () => closeAll());
  }

  function initPasswordButtons(){
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
  }

  function init(){
    initSlider();
    initAccountMenus();
    initPasswordButtons();
  }

  if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, {once:true});
  else init();
})();

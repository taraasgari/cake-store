(() => {
  "use strict";
  const sidebar=document.querySelector("[data-pa-sidebar]");
  const overlay=document.querySelector("[data-pa-overlay]");
  function open(){sidebar?.classList.add("open");overlay?.classList.add("show");document.body.style.overflow="hidden"}
  function close(){sidebar?.classList.remove("open");overlay?.classList.remove("show");document.body.style.overflow=""}
  function toggleTheme(){const r=document.documentElement;const next=(r.dataset.perfumeTheme||"night")==="night"?"day":"night";r.dataset.perfumeTheme=next;try{localStorage.setItem("velora-theme",next);localStorage.setItem("perfume-theme",next);localStorage.setItem("theme",next)}catch(_){}}
  document.addEventListener("click",e=>{if(e.target.closest("[data-pa-open]")){open();return}if(e.target.closest("[data-pa-close]")||e.target.closest("[data-pa-overlay]")){close();return}if(e.target.closest("[data-pa-theme]")){toggleTheme();return}const c=e.target.closest("[data-pa-message-close]");if(c)c.closest(".pa-message")?.remove()});
  document.addEventListener("keydown",e=>{if(e.key==="Escape")close()});
})();

(() => {
 const root=document.documentElement;
 const setTheme=t=>{root.dataset.perfumeTheme=t;try{localStorage.setItem("perfume-luxury-theme",t)}catch(e){}};
 document.addEventListener("click",e=>{
  if(e.target.closest("[data-theme-toggle]")){setTheme(root.dataset.perfumeTheme==="night"?"day":"night");return}
  if(e.target.closest("[data-menu-open]")){document.querySelector("[data-menu]")?.classList.add("open");document.body.style.overflow="hidden";return}
  if(e.target.closest("[data-menu-close]")){document.querySelector("[data-menu]")?.classList.remove("open");document.body.style.overflow="";return}
  if(e.target.closest("[data-search-open]")){document.querySelector("[data-search]")?.classList.add("open");document.body.style.overflow="hidden";return}
  if(e.target.closest("[data-search-close]")){document.querySelector("[data-search]")?.classList.remove("open");document.body.style.overflow="";return}
  if(e.target.closest("[data-filter-open]")){document.querySelector("[data-filters]")?.classList.add("open");return}
  if(e.target.closest("[data-filter-close]")){document.querySelector("[data-filters]")?.classList.remove("open");return}
  if(e.target.closest("[data-toast-close]")){e.target.closest(".toasts>div")?.remove();return}
  const th=e.target.closest("[data-image]");if(th){const m=document.getElementById("detailMainImage");if(m)m.src=th.dataset.image;return}
  const v=e.target.closest("[data-variant]");if(v){document.querySelectorAll("[data-variant]").forEach(x=>x.classList.remove("selected"));v.classList.add("selected");const i=document.getElementById("variantInput"),p=document.getElementById("detailPrice"),m=document.getElementById("detailMainImage"),q=document.getElementById("qty");if(i)i.value=v.dataset.variant||"";if(p)p.textContent=new Intl.NumberFormat("fa-IR").format(Number(v.dataset.price||0));if(m&&v.dataset.vimage)m.src=v.dataset.vimage;if(q)q.max=Math.max(1,Number(v.dataset.stock||1));return}
  if(e.target.closest("[data-minus]")){const q=document.getElementById("qty");if(q)q.value=Math.max(1,Number(q.value||1)-1);return}
  if(e.target.closest("[data-plus]")){const q=document.getElementById("qty");if(q)q.value=Math.min(Number(q.max||9999),Number(q.value||1)+1)}
 });
 document.addEventListener("change",e=>{const s=e.target.closest("[data-sort]");if(!s)return;const u=new URL(location.href);u.searchParams.set("sort",s.value);u.searchParams.delete("page");location.href=u});
 document.addEventListener("keydown",e=>{if(e.key!=="Escape")return;document.querySelector("[data-menu]")?.classList.remove("open");document.querySelector("[data-search]")?.classList.remove("open");document.querySelector("[data-filters]")?.classList.remove("open");document.body.style.overflow=""});
 const h=document.querySelector("[data-header]");const sh=()=>h?.classList.toggle("scrolled",scrollY>18);sh();addEventListener("scroll",sh,{passive:true});
 document.querySelector("[data-variant]")?.click();
 if("IntersectionObserver" in window){const els=document.querySelectorAll(".reveal");els.forEach(x=>{x.style.opacity="0";x.style.transform="translateY(16px)";x.style.transition="opacity .55s, transform .55s"});const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.style.opacity="1";en.target.style.transform="translateY(0)";io.unobserve(en.target)}}),{threshold:.08});els.forEach(x=>io.observe(x))}
})();

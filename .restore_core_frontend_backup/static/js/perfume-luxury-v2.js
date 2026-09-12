(() => {
  const root=document.documentElement;
  const $=(s,c=document)=>c.querySelector(s);
  const $$=(s,c=document)=>[...c.querySelectorAll(s)];

  function setTheme(t){root.dataset.perfumeTheme=t;try{localStorage.setItem("velora-theme",t)}catch(e){}}

  document.addEventListener("click",e=>{
    if(e.target.closest("[data-theme-toggle]")){setTheme(root.dataset.perfumeTheme==="night"?"day":"night");return}
    if(e.target.closest("[data-menu-open]")){$("[data-menu]")?.classList.add("open");document.body.style.overflow="hidden";return}
    if(e.target.closest("[data-menu-close]")){$("[data-menu]")?.classList.remove("open");document.body.style.overflow="";return}
    if(e.target.closest("[data-search-open]")){$("[data-search]")?.classList.add("open");document.body.style.overflow="hidden";return}
    if(e.target.closest("[data-search-close]")){$("[data-search]")?.classList.remove("open");document.body.style.overflow="";return}
    if(e.target.closest("[data-filter-open]")){$("[data-filters]")?.classList.add("open");return}
    if(e.target.closest("[data-filter-close]")){$("[data-filters]")?.classList.remove("open");return}
    if(e.target.closest("[data-toast-close]")){e.target.closest(".v2-toast")?.remove();return}

    const th=e.target.closest("[data-image]");
    if(th){const img=$("#detailMainImage");if(img)img.src=th.dataset.image;return}

    const v=e.target.closest("[data-variant]");
    if(v){
      $$("[data-variant]").forEach(x=>x.classList.remove("selected"));v.classList.add("selected");
      const i=$("#variantInput"),p=$("#detailPrice"),m=$("#detailMainImage"),q=$("#qty");
      if(i)i.value=v.dataset.variant||"";
      if(p)p.textContent=new Intl.NumberFormat("fa-IR").format(Number(v.dataset.price||0));
      if(m&&v.dataset.vimage)m.src=v.dataset.vimage;
      if(q)q.max=Math.max(1,Number(v.dataset.stock||1));
      return;
    }

    if(e.target.closest("[data-minus]")){const q=$("#qty");if(q)q.value=Math.max(1,Number(q.value||1)-1);return}
    if(e.target.closest("[data-plus]")){const q=$("#qty");if(q)q.value=Math.min(Number(q.max||9999),Number(q.value||1)+1)}
  });

  document.addEventListener("change",e=>{
    const s=e.target.closest("[data-sort]");if(!s)return;
    const u=new URL(location.href);u.searchParams.set("sort",s.value);u.searchParams.delete("page");location.href=u;
  });

  const header=$("[data-header]"),progress=$("[data-progress]");
  function sync(){
    header?.classList.toggle("scrolled",scrollY>20);
    if(progress){const max=document.documentElement.scrollHeight-innerHeight;progress.style.width=(max>0?(scrollY/max)*100:0)+"%"}
  }
  sync();addEventListener("scroll",sync,{passive:true});

  const cursor=$("[data-cursor]"),ring=$("[data-cursor-ring]");
  if(matchMedia("(pointer:fine)").matches&&cursor&&ring){
    addEventListener("mousemove",e=>{cursor.style.left=e.clientX+"px";cursor.style.top=e.clientY+"px";ring.animate({left:e.clientX+"px",top:e.clientY+"px"},{duration:260,fill:"forwards"})});
    $$("a,button,input,select,textarea").forEach(el=>{el.addEventListener("mouseenter",()=>ring.classList.add("active"));el.addEventListener("mouseleave",()=>ring.classList.remove("active"))});
  }

  document.querySelector("[data-variant]")?.click();

  if("IntersectionObserver" in window){
    const items=$$(".reveal");
    items.forEach(el=>{el.style.opacity="0";el.style.transform="translateY(24px)";el.style.transition="opacity .7s ease,transform .7s ease"});
    const io=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.style.opacity="1";entry.target.style.transform="translateY(0)";io.unobserve(entry.target)}}),{threshold:.08});
    items.forEach(el=>io.observe(el));
  }
})();

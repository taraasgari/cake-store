(() => {
 const root=document.documentElement,$=(s,c=document)=>c.querySelector(s),$$=(s,c=document)=>[...c.querySelectorAll(s)];
 const setTheme=t=>{root.dataset.perfumeTheme=t;try{localStorage.setItem("velora-theme",t)}catch(e){}};

 document.addEventListener("click",e=>{
  if(e.target.closest("[data-theme-toggle]")){setTheme(root.dataset.perfumeTheme==="night"?"day":"night");return}
  if(e.target.closest("[data-menu-open]")){$("[data-menu]")?.classList.add("open");document.body.style.overflow="hidden";return}
  if(e.target.closest("[data-menu-close]")){$("[data-menu]")?.classList.remove("open");document.body.style.overflow="";return}
  const tc=e.target.closest("[data-toast-close]");if(tc){tc.closest(".phase-toasts>div")?.remove();return}
  const pt=e.target.closest("[data-password-toggle]");if(pt){const input=document.getElementById(pt.dataset.passwordToggle),icon=pt.querySelector("i");if(input){const show=input.type==="password";input.type=show?"text":"password";icon?.classList.toggle("fa-eye",!show);icon?.classList.toggle("fa-eye-slash",show)}return}
  const th=e.target.closest("[data-image],[data-detail-image]");if(th){const m=$("#detailMainImage,#mainProductImage");if(m)m.src=th.dataset.image||th.dataset.detailImage||"";return}
  const v=e.target.closest("[data-variant],[data-variant-id]");if(v){$$("[data-variant],[data-variant-id]").forEach(x=>x.classList.remove("selected"));v.classList.add("selected");const id=v.dataset.variant||v.dataset.variantId||"",price=v.dataset.price||v.dataset.variantPrice||"",img=v.dataset.vimage||v.dataset.variantImage||"",stock=Number(v.dataset.stock||v.dataset.variantStock||0),hid=$("#variantInput,#selectedVariantInput"),pe=$("#detailPrice,#detailFinalPrice"),mi=$("#detailMainImage,#mainProductImage"),q=$("#qty,#detailQty");if(hid)hid.value=id;if(pe&&price)pe.textContent=new Intl.NumberFormat("fa-IR").format(Number(price));if(mi&&img)mi.src=img;if(q&&stock>0)q.max=String(stock);return}
  if(e.target.closest("[data-minus],[data-qty-minus]")){const q=$("#qty,#detailQty");if(q)q.value=Math.max(1,Number(q.value||1)-1);return}
  if(e.target.closest("[data-plus],[data-qty-plus]")){const q=$("#qty,#detailQty");if(q)q.value=Math.min(Number(q.max||9999),Number(q.value||1)+1)}
 });

 document.addEventListener("change",e=>{const s=e.target.closest("[data-sort],[data-sort-select]");if(!s)return;const u=new URL(location.href);u.searchParams.set("sort",s.value);u.searchParams.delete("page");location.href=u});

 const progress=$("[data-progress]");
 const sync=()=>{if(progress){const max=document.documentElement.scrollHeight-innerHeight;progress.style.width=(max>0?(scrollY/max)*100:0)+"%"}};
 sync();addEventListener("scroll",sync,{passive:true});

 if("IntersectionObserver" in window){const items=$$(".reveal");items.forEach(x=>{x.style.opacity="0";x.style.transform="translateY(20px)";x.style.transition="opacity .65s ease,transform .65s ease"});const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.style.opacity="1";en.target.style.transform="translateY(0)";io.unobserve(en.target)}}),{threshold:.08});items.forEach(x=>io.observe(x))}
})();

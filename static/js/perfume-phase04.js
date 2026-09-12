(() => {
  const $=(s,r=document)=>r.querySelector(s);
  document.addEventListener('click',e=>{
    const account=e.target.closest('[data-p4-account-menu]');
    document.querySelectorAll('[data-p4-account-menu][open]').forEach(menu=>{if(menu!==account)menu.removeAttribute('open')});
    if(e.target.closest('[data-p4-menu-open]')){$('[data-p4-menu]')?.classList.add('open');document.body.style.overflow='hidden';return}
    if(e.target.closest('[data-p4-menu-close]')){$('[data-p4-menu]')?.classList.remove('open');document.body.style.overflow='';return}
    if(e.target.closest('[data-p4-filter-open]')){$('[data-p4-filter]')?.classList.add('open');return}
    if(e.target.closest('[data-p4-filter-close]')){$('[data-p4-filter]')?.classList.remove('open');return}
    const t=e.target.closest('[data-p4-toast-close]');if(t)t.closest('.p4-toast')?.remove();
  });
  document.addEventListener('change',e=>{const s=e.target.closest('[data-p4-sort]');if(!s)return;const u=new URL(location.href);u.searchParams.set('sort',s.value);u.searchParams.delete('page');location.href=u});
  document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;$('[data-p4-menu]')?.classList.remove('open');$('[data-p4-filter]')?.classList.remove('open');document.querySelectorAll('[data-p4-account-menu][open]').forEach(menu=>menu.removeAttribute('open'));document.body.style.overflow=''});
  const p=$('[data-p4-progress]');function sync(){if(!p)return;const m=document.documentElement.scrollHeight-innerHeight;p.style.width=(m>0?(scrollY/m)*100:0)+'%'}sync();addEventListener('scroll',sync,{passive:true});
})();

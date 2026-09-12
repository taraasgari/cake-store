(() => {
  "use strict";
  const node=document.getElementById("perfume-visual-rules");
  const themeNode=document.getElementById("perfume-theme-values");
  const validHex=v=>/^#[0-9a-f]{6}$/i.test(v||"");
  if(themeNode){const r=document.documentElement;const p=validHex(themeNode.dataset.primary)?themeNode.dataset.primary:"#C9954D";const s=validHex(themeNode.dataset.secondary)?themeNode.dataset.secondary:"#75471F";const a=validHex(themeNode.dataset.accent)?themeNode.dataset.accent:"#E3C286";r.style.setProperty("--p-gold",p);r.style.setProperty("--p-gold-deep",s);r.style.setProperty("--p-gold-pale",a);r.style.setProperty("--site-primary",p);r.style.setProperty("--site-secondary",s);r.style.setProperty("--site-accent",a)}
  if(!node)return;
  let raw;try{raw=JSON.parse(node.textContent||'"[]"')}catch(_){return}
  let rules=[];if(Array.isArray(raw))rules=raw;else if(typeof raw==="string"){try{const p=JSON.parse(raw||"[]");if(Array.isArray(p))rules=p}catch(_){}}
  const bp=()=>innerWidth<=620?"mobile":innerWidth<=1024?"tablet":"desktop";
  function apply(){const b=bp();for(const rule of rules){if(!rule||!rule.id)continue;const el=document.querySelector(`[data-bsg-edit="${CSS.escape(rule.id)}"]`)||document.getElementById(rule.id);if(!el)continue;const kind=el.dataset.bsgKind||rule.kind||"box";if(rule.hidden)el.style.display="none";if(kind==="text"&&rule.text)el.textContent=rule.text;if(kind==="image"&&rule.src&&el.tagName==="IMG")el.src=rule.src;Object.entries(rule.styles||{}).forEach(([k,v])=>{if(v!==""&&v!=null){try{el.style[k]=v}catch(_){}}});const pos=rule.responsive?.[b];if(pos){if(Number(pos.width)>0)el.style.width=`${Number(pos.width)}px`;if(Number(pos.height)>0)el.style.height=`${Number(pos.height)}px`;if(Number(pos.x)||Number(pos.y))el.style.transform=`translate(${Number(pos.x)||0}px,${Number(pos.y)||0}px)`;if(Number.isFinite(Number(pos.zIndex)))el.style.zIndex=String(Number(pos.zIndex))}}}
  apply();let timer;addEventListener("resize",()=>{clearTimeout(timer);timer=setTimeout(apply,120)},{passive:true});
})();

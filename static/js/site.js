document.addEventListener('DOMContentLoaded',()=>{const btn=document.querySelector('.whatsapp-float');if(!btn)return;const onScroll=()=>{btn.classList.toggle('compact',window.scrollY>180)};window.addEventListener('scroll',onScroll,{passive:true});onScroll();});
// Si un servidor externo deja de ofrecer una fotografía, la noticia sigue visible.
document.addEventListener('error',(event)=>{
  const img=event.target;
  if(!img || img.tagName!=='IMG' || img.dataset.fallbackHandled==='1') return;
  img.dataset.fallbackHandled='1';
  const fallback=document.createElement('div');
  fallback.className='image-load-fallback';
  fallback.textContent='IMAGEN NO DISPONIBLE';
  img.parentNode?.insertBefore(fallback,img);
  img.remove();
},true);

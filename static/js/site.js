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


// Fecha y efemérides del día, usando la zona horaria de Argentina.
document.addEventListener('DOMContentLoaded', async () => {
  const parts = new Intl.DateTimeFormat('es-AR', { timeZone: 'America/Argentina/Buenos_Aires', day: '2-digit', month: '2-digit', year: 'numeric' }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map(p => [p.type, p.value]));
  const day = Number(values.day), month = Number(values.month), year = values.year;
  document.querySelectorAll('[data-current-date]').forEach(el => {
    const mode = el.dataset.currentDate;
    el.textContent = mode === 'dots' ? `${values.day} · ${values.month} · ${year}` : `${values.day}/${values.month}/${year}`;
  });
  const container = document.getElementById('ephemeris-items');
  const dateLabel = document.getElementById('ephemeris-date');
  if (!container) return;
  if (dateLabel) dateLabel.textContent = `${values.day}/${values.month}/${year}`;
  try {
    const response = await fetch('static/data/ephemerides.json');
    if (!response.ok) throw new Error('No se pudieron cargar las efemérides');
    const records = await response.json();
    const todayItems = records.filter(item => Number(item.month) === month && Number(item.day) === day);
    container.replaceChildren();
    if (!todayItems.length) {
      const p = document.createElement('p'); p.textContent = 'No hay efemérides cargadas para esta fecha.'; container.appendChild(p); return;
    }
    todayItems.forEach(item => {
      const article = document.createElement('article');
      const title = document.createElement('h3'); title.textContent = item.title;
      const description = document.createElement('p'); description.textContent = item.description;
      article.append(title, description); container.appendChild(article);
    });
  } catch (error) {
    container.replaceChildren(); const p = document.createElement('p'); p.textContent = 'No se pudieron cargar las efemérides en este momento.'; container.appendChild(p);
  }
});

# Web Noticias – Pulso Digital | GitHub Pages

Esta carpeta contiene la versión estática del sitio, preparada para publicarse en GitHub Pages. No requiere Python, Flask, Gunicorn, base de datos ni Render.

## Publicación

1. Copiá TODO el contenido de esta carpeta a la raíz del repositorio `proyectowebnoticias`, reemplazando los archivos anteriores.
2. Conservá la carpeta `.git` de tu repositorio local: no la reemplaces ni la borres.
3. En GitHub, abrí **Settings → Pages** y elegí **Deploy from a branch**, rama `main` y carpeta `/(root)`.
4. Desde PowerShell, dentro de la carpeta local del repositorio, ejecutá:

```powershell
git add -A
git commit -m "Publicar Web Noticias estática en GitHub Pages"
git push origin main
```

5. Esperá a que finalice la publicación en **Actions**. El sitio estará en `https://exequielrivadera.github.io/proyectowebnoticias/`.

## Estructura esperada

- `index.html` en la raíz (página de inicio).
- Páginas HTML para noticias, secciones, contacto y en vivo.
- `static/css/`, `static/js/`, `static/img/` y `static/data/` con los recursos del sitio.
- `.nojekyll` para que GitHub Pages publique los recursos tal como están.

## Alcance de esta versión

Es una versión de presentación estática. Los enlaces, páginas, estilos, efemérides del día y contacto por WhatsApp funcionan en el navegador. No incluye panel de administración ni publicación dinámica de noticias. La versión Flask comercial debe conservarse por separado como respaldo.

Las fotografías de las noticias utilizan direcciones externas; su disponibilidad depende de los sitios que las alojan.

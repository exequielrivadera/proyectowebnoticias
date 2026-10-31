# Web Noticias

Proyecto inicial de periódico digital con portada editorial, secciones, artículos individuales, noticias destacadas, sección de último momento, espacios publicitarios, efemérides argentinas y panel administrativo.

## Requisitos
- Windows 10/11 o Linux
- Python 3.10 o superior

## Inicio rápido en Windows
1. Descomprimir la carpeta.
2. Ejecutar `run_windows.bat`.
3. Esperar la instalación de Flask y la apertura del servidor.
4. Abrir http://127.0.0.1:5000

También se puede ejecutar manualmente:
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

## Panel administrativo
- URL: http://127.0.0.1:5000/admin/login
- Usuario inicial: `admin`
- Contraseña inicial: `Cambiar123!`

**Cambiar la contraseña inmediatamente** desde el menú del panel. El panel incluye gestión de noticias, publicidades y efemérides.

## Funciones incluidas
- Portada responsive y navegación por secciones.
- 18 noticias iniciales en español: 3 por sección, con enlaces a fuentes de referencia.
- Noticias con título, copete, cuerpo, autor, imagen y fuente editable.
- Marcar noticias como destacadas o de último momento.
- Publicar, despublicar y eliminar noticias.
- Publicidades por ubicación: cabecera, lateral e intercalada; con URL y fechas de vigencia.
- Efemérides argentinas seleccionadas por fecha local de Argentina.
- Contacto por WhatsApp configurado para el número indicado.
- Base SQLite creada automáticamente en `data/web_noticias.db`.

## Importante antes de publicar en internet
Esta entrega está preparada para pruebas locales. Antes de producción se debe:
- Configurar `SECRET_KEY` con un valor aleatorio y secreto.
- Desactivar `debug`.
- Usar HTTPS y un servidor WSGI de producción.
- Migrar SQLite a PostgreSQL si habrá varios editores o tráfico sostenido.
- Configurar copias de seguridad y almacenamiento persistente para imágenes.
- Incorporar protección CSRF, límites de intentos de inicio de sesión y política de privacidad.
- Revisar y ampliar el calendario de efemérides con fuentes editoriales verificadas.

## Contenido editorial
El sitio incluye 18 artículos iniciales redactados para esta versión, basados en publicaciones y fuentes de referencia enlazadas. Son contenido editorial de muestra: antes de publicar el medio, la redacción debe revisarlos, actualizarlos y reemplazarlos según su línea editorial.


## Fotografías de las noticias
Las 18 noticias iniciales tienen fotografías editoriales relacionadas con sus temas. Las imágenes se muestran desde los servidores de sus publicaciones o instituciones de origen mediante enlaces externos; por eso, la computadora necesita conexión a internet y la disponibilidad depende de cada servidor. No son imágenes generadas.

**Antes de comercializar o publicar el sitio:** verificar los derechos de reproducción de cada fotografía y solicitar autorización o reemplazarla por material propio/licenciado cuando corresponda. Que una imagen esté visible en un sitio público no significa que sea de libre uso. Las imágenes cargadas por el administrador se guardan en `static/uploads/`.


### Firma de desarrollo
El pie de página incluye la firma visual de Pulso Digital. Las imágenes editoriales remotas cuentan con un reemplazo visual cuando el servidor de origen no responde.


## Publicar en Render

Este proyecto incluye `render.yaml` para desplegarlo como aplicación Flask.

1. Subí los archivos de esta carpeta al repositorio de GitHub.
2. En Render, elegí **New > Blueprint** y conectá el repositorio.
3. Render detectará `render.yaml` y preparará el servicio web.
4. Cuando lo solicite, definí `ADMIN_PASSWORD` con una contraseña fuerte y privada.
5. Esperá a que termine el despliegue y abrí la URL `onrender.com` asignada.

También podés crear un **Web Service** manualmente:
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --workers 2 --threads 4 --timeout 120`
- Variables: `SECRET_KEY` (aleatoria), `ADMIN_USERNAME`, `ADMIN_PASSWORD` y `WHATSAPP_NUMBER`.

**Importante sobre el plan gratuito:** el sistema de archivos de Render es efímero. La base SQLite y las imágenes subidas desde el panel pueden perderse al reiniciar o volver a desplegar el servicio. El plan gratuito sirve para presentar el proyecto en un portfolio; para administrar noticias de forma permanente, migrá la base a PostgreSQL y configurá almacenamiento persistente para imágenes. El servicio también puede tardar un poco en responder después de un período sin visitas.

**Seguridad:** no publiques contraseñas ni archivos `.env` en GitHub. Configurá `ADMIN_PASSWORD` como variable secreta en Render.

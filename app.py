import os
import sqlite3
from datetime import datetime, date
from functools import wraps
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "web_noticias.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar-esta-clave-en-produccion")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("RENDER", "").lower() == "true",
)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "543804507584")
CATEGORIES = ["Argentina", "Deportes", "Economía", "Tecnología", "Sociedad", "Mundo"]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT 'Argentina',
            image TEXT NOT NULL DEFAULT '', author TEXT NOT NULL DEFAULT 'Redacción',
            is_featured INTEGER NOT NULL DEFAULT 0,
            is_breaking INTEGER NOT NULL DEFAULT 0,
            published INTEGER NOT NULL DEFAULT 1,
            source_url TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, placement TEXT NOT NULL,
            image TEXT NOT NULL DEFAULT '', target_url TEXT NOT NULL DEFAULT '',
            starts_on TEXT NOT NULL DEFAULT '', ends_on TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS ephemerides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER NOT NULL, day INTEGER NOT NULL,
            title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
            UNIQUE(month, day, title)
        );
        """)
        article_columns = [row["name"] for row in con.execute("PRAGMA table_info(articles)").fetchall()]
        if "source_url" not in article_columns:
            con.execute("ALTER TABLE articles ADD COLUMN source_url TEXT NOT NULL DEFAULT ''")
        if not con.execute("SELECT id FROM users LIMIT 1").fetchone():
            initial_username = os.environ.get("ADMIN_USERNAME", "admin")
            initial_password = os.environ.get("ADMIN_PASSWORD", "Cambiar123!")
            con.execute("INSERT INTO users(username,password_hash) VALUES(?,?)",
                        (initial_username, generate_password_hash(initial_password)))
        if not con.execute("SELECT id FROM ephemerides LIMIT 1").fetchone():
            seeds = [
                (1, 1, "Año Nuevo", "Comienza un nuevo año calendario."),
                (2, 14, "Día de la Energía", "Jornada vinculada a la reflexión sobre el uso responsable de la energía."),
                (3, 24, "Día Nacional de la Memoria por la Verdad y la Justicia", "En memoria de las víctimas de la última dictadura cívico-militar."),
                (4, 2, "Día del Veterano y de los Caídos en la Guerra de Malvinas", "Homenaje a quienes participaron en la Guerra de Malvinas."),
                (5, 1, "Día Internacional de los Trabajadores", "Jornada de reconocimiento a los derechos y las luchas de las personas trabajadoras."),
                (5, 25, "Revolución de Mayo", "Se recuerda la conformación del primer gobierno patrio en 1810."),
                (6, 17, "Paso a la Inmortalidad del General Martín Miguel de Güemes", "Homenaje al líder de la guerra gaucha."),
                (6, 20, "Día de la Bandera", "Se conmemora el fallecimiento de Manuel Belgrano, creador de la bandera argentina."),
                (7, 9, "Día de la Independencia", "Se recuerda la declaración de la independencia en 1816."),
                (8, 17, "Paso a la Inmortalidad del General José de San Martín", "Homenaje al Libertador de América."),
                (9, 11, "Día del Maestro", "En homenaje a Domingo Faustino Sarmiento."),
                (10, 12, "Día del Respeto a la Diversidad Cultural", "Jornada de reflexión sobre la diversidad cultural."),
                (11, 20, "Día de la Soberanía Nacional", "Se recuerda la batalla de la Vuelta de Obligado."),
                (12, 10, "Día de la Restauración de la Democracia", "Se recuerda la asunción presidencial de Raúl Alfonsín en 1983."),
                (12, 24, "Nochebuena", "Víspera de Navidad.")
            ]
            con.executemany("INSERT OR IGNORE INTO ephemerides(month,day,title,description) VALUES(?,?,?,?)", seeds)

        if not con.execute("SELECT id FROM articles LIMIT 1").fetchone():
            sample_articles = [
                ("Argentina", "A 43 años del regreso democrático, la memoria vuelve al centro de la conversación pública", "En distintas localidades se realizaron actividades para recordar las elecciones del 30 de octubre de 1983. La fecha invita a repasar el valor de la participación ciudadana, las instituciones y la convivencia democrática.", "La conmemoración del 30 de octubre recupera una fecha clave de la historia reciente: las elecciones que marcaron el final de la última dictadura y el comienzo de una nueva etapa institucional. Actos y reflexiones en distintas ciudades ponen el foco en la memoria colectiva y en los desafíos de sostener la vida democrática.", "Redacción", 1, 0, "https://noticiasmercedinas.com/site/2026/10/30/emotivo-homenaje-a-raul-alfonsin-conmemoraron-el-retorno-a-la-democracia/"),
                ("Argentina", "El Congreso debate cambios en el régimen de inversiones y el mercado de carbono", "La agenda legislativa incorporó iniciativas vinculadas a inversiones y herramientas para el desarrollo de mercados ambientales.", "La discusión parlamentaria sobre instrumentos de inversión y mecanismos vinculados al mercado de carbono forma parte de una agenda económica que combina incentivos productivos y compromisos ambientales. El alcance de cada medida dependerá de su implementación y de la reglamentación correspondiente.", "Redacción", 0, 0, "https://www.lanacion.com.ar/politica/"),
                ("Argentina", "La agenda pública combina economía, educación y debates institucionales", "Un repaso de los temas que atraviesan la conversación nacional en el cierre de octubre.", "La actualidad argentina reúne discusiones económicas, decisiones legislativas y actividades educativas y científicas en distintas provincias. Para seguir estos temas resulta importante consultar documentos oficiales, escuchar a los sectores involucrados y distinguir los anuncios de las medidas efectivamente implementadas.", "Redacción", 0, 0, "https://www.cancilleria.gob.ar/es/cei/publicaciones/resumen-mensual-de-indicadores-economicos-de-la-argentina-octubre-2026"),
                ("Deportes", "Boca y River se preparan para un nuevo Superclásico en la recta final del Clausura", "El encuentro está previsto para el domingo 1 de noviembre y concentra la atención en la penúltima etapa del torneo.", "Boca Juniors recibirá a River Plate en La Bombonera por una nueva edición del Superclásico. El partido llega en un tramo decisivo del Torneo Clausura 2026, con posiciones y objetivos deportivos todavía en juego. La previa estará marcada por la expectativa de los hinchas y las decisiones de los cuerpos técnicos.", "Redacción Deportes", 0, 1, "https://www.tvn.cl/deportes/futbol-internacional/boca-juniors-vs-river-plate-horario-canal-y-donde-ver-el-superclasico-argentino"),
                ("Deportes", "La AFA aprobó un nuevo formato para el campeonato de Primera División 2027", "El esquema anunciado mantiene 30 equipos y propone volver a una competencia de todos contra todos.", "La organización del fútbol argentino tendrá cambios para la temporada 2027. Según la información publicada, el proyecto aprobado conserva la participación de 30 equipos y deja atrás el formato dividido en zonas para adoptar una tabla única de todos contra todos. El calendario y los detalles operativos serán claves para conocer el impacto deportivo.", "Redacción Deportes", 0, 0, "https://www.eldia.com/deportes/afa-aprobo-el-nuevo-torneo-2027-30-equipos-todos-contra-todos-una-tabla-y-los-detalles-deportes_1793291760"),
                ("Deportes", "El básquet 3x3 argentino entra en la etapa decisiva de los Juegos Argentinos Urbanos", "La Confederación Argentina de Básquetbol informó que el campeonato se acerca a su definición.", "El básquet 3x3 continúa ganando espacio dentro del calendario deportivo nacional. La Confederación Argentina de Básquetbol informó sobre el desarrollo del Campeonato Argentino de 3x3 en el marco de los Juegos Argentinos Urbanos 2026, con jornadas que acercan la competencia a su definición.", "Redacción Deportes", 0, 0, "https://argentina.basketball/"),
                ("Economía", "El Banco Central reconoció una caída de la actividad en el tercer trimestre y proyectó una recuperación", "El informe de política monetaria atribuyó parte del retroceso a factores que considera transitorios.", "El Banco Central señaló que la actividad económica retrocedió durante el tercer trimestre de 2026 y planteó que el último tramo del año podría mostrar una recuperación. La evolución dependerá de la normalización de sectores afectados y de la dinámica del consumo, la inversión y la producción. Las proyecciones oficiales deben leerse como estimaciones y no como resultados asegurados.", "Redacción Economía", 0, 0, "https://tn.com.ar/economia/2026/10/29/el-bcra-reconocio-que-la-actividad-economica-cayo-en-el-tercer-trimestre-pero-espera-una-recuperacion-en-el-ultimo-tramo-del-ano/"),
                ("Economía", "Cancillería publicó el resumen de indicadores económicos de octubre", "El informe reúne datos sobre actividad, industria, empleo, precios, comercio exterior y resultado fiscal.", "El Centro de Economía Internacional de la Cancillería difundió su resumen mensual de indicadores de la Argentina. El documento organiza información de distintas áreas y permite observar variables que suelen analizarse en conjunto para comprender la coyuntura. Para una lectura completa conviene consultar las series, períodos de comparación y metodología del informe original.", "Redacción Economía", 0, 0, "https://www.cancilleria.gob.ar/es/cei/publicaciones/resumen-mensual-de-indicadores-economicos-de-la-argentina-octubre-2026"),
                ("Economía", "Inversiones y actividad productiva: las variables que siguen de cerca empresas y mercados", "El cierre del año encuentra a distintos sectores atentos a la evolución de la actividad y las condiciones de financiamiento.", "La evolución de la actividad, el empleo, los precios y el comercio exterior son algunos de los indicadores que empresas y analistas siguen para evaluar decisiones de inversión. Los informes oficiales ofrecen una base para comparar tendencias, aunque cada sector puede mostrar comportamientos diferentes.", "Redacción Economía", 0, 0, "https://www.cancilleria.gob.ar/es/cei/publicaciones/resumen-mensual-de-indicadores-economicos-de-la-argentina-octubre-2026"),
                ("Tecnología", "La inteligencia artificial vuelve a abrir el debate sobre seguridad y responsabilidad digital", "Casos recientes en entornos educativos muestran la importancia de prevenir usos dañinos y proteger la privacidad.", "El avance de las herramientas generativas amplía las posibilidades creativas, pero también plantea desafíos para escuelas, familias y plataformas. Especialistas y comunidades educativas discuten cómo responder ante la manipulación de imágenes, la suplantación y la difusión de contenidos sin consentimiento. La alfabetización digital y los canales de denuncia son parte de una respuesta integral.", "Redacción Tecnología", 0, 0, "https://noticiasargentinas.com/inteligencia-artificial_t655533fb1d4fceb738dc2942"),
                ("Tecnología", "La Universidad Nacional de Rosario reúne proyectos científicos y tecnológicos", "Las jornadas institucionales buscan visibilizar investigaciones y fortalecer el vínculo entre universidad y sociedad.", "La Universidad Nacional de Rosario puso en marcha sus Jornadas de Ciencias, Tecnologías e Innovación 2026. El encuentro reúne a investigadores y equipos académicos para compartir proyectos, promover intercambios y acercar la producción científica a la comunidad.", "Redacción Tecnología", 0, 0, "https://radio.unr.edu.ar/2026/10/30/la-unr-lanzo-las-jornadas-de-ciencias-tecnologias-e-innovacion-2026/"),
                ("Tecnología", "El VAR semiautomático se prepara para llegar al fútbol argentino", "La nueva herramienta busca aportar precisión en la detección de posiciones adelantadas.", "La tecnología aplicada al arbitraje vuelve a estar en agenda con la llegada anunciada de un sistema de VAR semiautomático. Este tipo de asistencia utiliza cámaras y procesamiento de imágenes para colaborar en decisiones sobre posiciones adelantadas. Su funcionamiento, tiempos de revisión y comunicación con el público serán aspectos centrales de su implementación.", "Redacción Tecnología", 0, 0, "https://www.lanacion.com.ar/tema/torneo-clausura-2026/"),
                ("Sociedad", "La universidad pública busca acercar la investigación a los problemas de la comunidad", "Un encuentro académico en Rosario puso en común ciencia, innovación y desarrollo social.", "Las jornadas de ciencia e innovación de la Universidad Nacional de Rosario proponen un espacio para compartir investigaciones y fortalecer los vínculos entre equipos universitarios y la sociedad. La articulación entre conocimiento, instituciones y necesidades territoriales es uno de los ejes de este tipo de encuentros.", "Redacción Sociedad", 0, 0, "https://radio.unr.edu.ar/2026/10/30/la-unr-lanzo-las-jornadas-de-ciencias-tecnologias-e-innovacion-2026/"),
                ("Sociedad", "El debate sobre el acoso escolar vuelve a poner el foco en la convivencia", "Referentes provinciales señalaron la complejidad del bullying y la necesidad de abordajes sostenidos.", "El acoso entre pares requiere respuestas que involucren a las escuelas, las familias y los organismos de protección. La prevención no se limita a sancionar conductas: también incluye escucha, acompañamiento, educación emocional, protocolos claros y seguimiento de cada situación. Las intervenciones deben proteger a quienes atraviesan estas experiencias y evitar la exposición pública de menores.", "Redacción Sociedad", 0, 0, "https://inforama.com.ar/actualidad/2026/10/30/es-un-tema-muy-complejo-jalil-hablo-sobre-el-bullying/"),
                ("Sociedad", "El Senado aprobó cambios en la legislación vinculada a salud mental", "La iniciativa pasó a la siguiente instancia legislativa tras una sesión extensa.", "La discusión parlamentaria sobre salud mental volvió a ocupar un lugar central en la agenda institucional. El tratamiento de reformas legales abre una etapa de análisis sobre el alcance de las normas, los recursos disponibles y la coordinación entre los distintos niveles del sistema de atención. El seguimiento del trámite legislativo permitirá conocer el texto definitivo y sus efectos.", "Redacción Sociedad", 0, 0, "https://www.lanacion.com.ar/politica/"),
                ("Mundo", "Manifestaciones en Italia expresan reclamos por el costo de vida y las políticas del Gobierno", "Ciudades de todo el país registraron movilizaciones durante una jornada de protestas.", "La Agencia EFE informó sobre manifestaciones en distintas ciudades italianas en rechazo al costo de vida, a decisiones del Gobierno de Giorgia Meloni y al aumento del gasto en defensa. Roma fue uno de los principales puntos de concentración. Las protestas reflejan tensiones sociales y políticas que atraviesan el debate público italiano.", "Redacción Internacional", 0, 0, "https://efe.com/Mundo/"),
                ("Mundo", "Irán informó incidentes con embarcaciones en el estrecho de Ormuz", "El anuncio vuelve a poner la atención internacional sobre una ruta estratégica para el transporte marítimo.", "Las autoridades navales iraníes comunicaron incidentes que involucraron a varios buques en el estrecho de Ormuz. La información fue difundida por EFE y corresponde a la versión oficial iraní; cualquier evaluación independiente de los hechos requiere confirmación adicional. La zona es estratégica para el comercio energético internacional.", "Redacción Internacional", 0, 0, "https://efe.com/Mundo/"),
                ("Mundo", "Rusia y África profundizan sus diferencias en torno a la influencia regional", "El Kremlin expresó cuestionamientos sobre la participación de Ucrania en asuntos vinculados al continente africano.", "Según informó EFE, el Kremlin denunció intentos de interferencia ucraniana en sus intereses en África durante la cumbre Rusia-África. La declaración forma parte de un escenario geopolítico en el que distintos actores buscan ampliar sus vínculos políticos, económicos y de seguridad en el continente. La acusación corresponde a la postura expresada por Moscú.", "Redacción Internacional", 0, 0, "https://efe.com/Mundo/")
            ]
            now = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).isoformat(timespec="minutes")
            for cat, title, summary, body, author, featured, breaking_flag, source in sample_articles:
                con.execute("""INSERT INTO articles(title,summary,body,category,author,is_featured,is_breaking,published,source_url,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (title, summary, body, cat, author, featured, breaking_flag, 1, source, now))

        # Efemérides del 31 de octubre: se insertan también en bases ya existentes.
        october_31 = [
            (10, 31, "Día Universal del Ahorro", "Se recuerda la fecha instituida al finalizar el Congreso Internacional del Ahorro, celebrado en Milán en octubre de 1924. La jornada promueve la planificación y el uso responsable de los recursos."),
            (10, 31, "Día Mundial de las Ciudades", "Jornada establecida por las Naciones Unidas para promover ciudades inclusivas, seguras, resilientes y sostenibles. En 2026, el eje es la regeneración urbana y el acceso a una vivienda adecuada."),
            (10, 31, "Nace José María Contursi (1911)", "El 31 de octubre de 1911 nació el letrista argentino José María Contursi, autor de tangos como “Gricel” y “Cristal”, referentes del repertorio de la canción porteña."),
            (10, 31, "Fallece Lola Membrives (1969)", "El 31 de octubre de 1969 murió Lola Membrives, actriz argentina de destacada trayectoria en el teatro, con reconocimiento tanto en Argentina como en España.")
        ]
        con.executemany("INSERT OR IGNORE INTO ephemerides(month,day,title,description) VALUES(?,?,?,?)", october_31)

        # Asignar fotografías a las noticias iniciales (también completa la primera versión ya instalada).
        editorial_images = {
            "Argentina": [
                "https://media.urgente24.com/p/577db8c0c42d2fbe8fb8572485757094/adjuntos/319/imagenes/002/462/0002462232/800x0/smart/alfonsinjpg.jpg",
                "https://www.argentina.gob.ar/sites/default/files/casa_de_gobierno_fachada_jgm_1718.jpg",
                "https://www.rosarionoticias.gob.ar/library/timthumb/timthumb.php?h=634&src=%2Fuploads%2Ffotos%2Fp1j9n50dbi1q0t1vqm1m3ce6ckqvb.jpg&w=950&zc=1"
            ],
            "Deportes": [
                "https://www.diariopanorama.com/fotos/notas/2025/11/09/zeballos-boca-river-534243-172422.jpg",
                "https://cdn.mos.cms.futurecdn.net/QAQ4eaL7J4pL3YqXGffQpS.jpg",
                "https://media.0221.com.ar/p/beac6ca37e4c45890c653e18a6e9d6c8/adjuntos/357/imagenes/100/240/0100240166/1400x0/smart/basquet-3x3-plaza-moreno-3.jpg"
            ],
            "Economía": [
                "https://cloudfront-us-east-1.images.arcpublishing.com/bloomberglinea/4NDZMAVYLVEERBHUQ2CHHG2L7I.jpeg",
                "https://i-invdn-com.akamaized.net/trkd-images/LYNXMPEH1B1BL_L.jpg",
                "https://media.licdn.com/dms/image/v2/D4D22AQG1x9gQD_MLlA/feedshare-shrink_800/B4DZyvmqnpJkAg-/0/1772472675162?e=2147483647&t=GW2BSWrxYI1IyyUlIioJS0042DK96w3N94gjIH9-91g&v=beta"
            ],
            "Tecnología": [
                "https://media.lacapital.com.ar/p/3549df13cb2faa7b223eaa3c9d380d69/adjuntos/203/imagenes/102/855/0102855103/1200x675/smart/unr-ia.jpg",
                "https://acf.geeknetic.es/imagenes/auto/26/04/01/fc2-ia-en-centros-de-datos.png",
                "https://cloudfront-us-east-2.images.arcpublishing.com/reuters/2ZXHMVAP7RLXBGW2SW46KS65QA.jpg"
            ],
            "Sociedad": [
                "https://www.argentina.gob.ar/sites/default/files/nota_pensar_la_enfermeria_en_salud_mental.jpg",
                "https://tn.com.ar/resizer/v2/el-colegio-madre-teresa-de-san-fernando-fue-elegido-entre-los-mejores-del-mundo-foto-gentileza-colegio-madre-teresa-YGOYGH6HIZGF3IPXPHUR6ATRVU.jpeg?auth=20b9878fd07f0635018cacb7c1ed612833f87666d650fd7672e1e723278b13e3&width=1440",
                "https://tn.com.ar/resizer/v2/multitudinaria-marcha-de-la-cgt-y-movimientos-sociales-foto-leandro-heredia-tn-5VI4RVQQDNFJJIBNZIGDRO2Q74.jpg?auth=0ed57bf03ed1d2bb7ccdb0d9c4adcaaab3d1db9c1d29ada762e4c3a8242f43a4&width=1440"
            ],
            "Mundo": [
                "https://img.rtve.es/imagenes/italia-huelga-general-trabajadores-presupuestos-gobieno-meloni/01765538488593.jpg",
                "https://commons.wikimedia.org/wiki/Special:FilePath/USS_Essex_(LHD_2),_right,_and_USNS_Wally_Schirra_(T-AKE_8)_transit_the_Strait_of_Hormuz_in_formation._(51531961733).jpg?width=1200",
                "https://res.cloudinary.com/graham-media-group/image/upload/f_auto/q_auto/c_scale%2Cw_640/v1/media/gmg/Z6ZKCCITTBCEBJVSJF5DBHQTVU.jpg?_a=DAJHqpE+ZAAA"
            ]
        }
        for category, image_list in editorial_images.items():
            rows = con.execute("SELECT id FROM articles WHERE category=? ORDER BY id", (category,)).fetchall()
            for index, row in enumerate(rows[:3]):
                con.execute("UPDATE articles SET image=? WHERE id=? AND (image='' OR image IS NULL)",
                            (image_list[index], row["id"]))
        con.execute("""UPDATE articles SET image=? WHERE title LIKE ?""",
                    ("https://commons.wikimedia.org/wiki/Special:FilePath/USS_Essex_(LHD_2),_right,_and_USNS_Wally_Schirra_(T-AKE_8)_transit_the_Strait_of_Hormuz_in_formation._(51531961733).jpg?width=1200", "Irán informó incidentes con embarcaciones%"))


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

def upload_image(field):
    f = request.files.get(field)
    if not f or not f.filename:
        return ""
    allowed = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    ext = os.path.splitext(secure_filename(f.filename))[1].lower()
    if ext not in allowed:
        return ""
    name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
    f.save(os.path.join(UPLOAD_DIR, name))
    return f"uploads/{name}"

def active_ads(placement):
    today = date.today().isoformat()
    with db() as con:
        return con.execute("""SELECT * FROM ads WHERE active=1 AND placement=?
            AND (starts_on='' OR starts_on<=?) AND (ends_on='' OR ends_on>=?)
            ORDER BY id DESC""", (placement, today, today)).fetchall()

@app.context_processor
def globals_for_templates():
    def media_url(path):
        if path and path.startswith(("http://", "https://")):
            return path
        return url_for("static", filename=path) if path else ""
    return {"categories": CATEGORIES, "whatsapp_link": f"https://wa.me/{WHATSAPP_NUMBER}?text=Hola%2C%20quiero%20comunicarme%20con%20el%20medio.", "year": date.today().year, "media_url": media_url}

@app.route("/")
def index():
    today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    with db() as con:
        featured = con.execute("SELECT * FROM articles WHERE published=1 AND is_featured=1 ORDER BY created_at DESC LIMIT 1").fetchone()
        latest = con.execute("SELECT * FROM articles WHERE published=1 ORDER BY created_at DESC LIMIT 12").fetchall()
        breaking = con.execute("SELECT * FROM articles WHERE published=1 AND is_breaking=1 ORDER BY created_at DESC LIMIT 5").fetchall()
        sections = {cat: con.execute("SELECT * FROM articles WHERE published=1 AND category=? ORDER BY created_at DESC LIMIT 4", (cat,)).fetchall() for cat in CATEGORIES}
        eph = con.execute("SELECT * FROM ephemerides WHERE month=? AND day=? ORDER BY title", (today.month, today.day)).fetchall()
    return render_template("index.html", featured=featured, latest=latest, breaking=breaking, sections=sections, ephemerides=eph, today=today, top_ads=active_ads("top"), side_ads=active_ads("sidebar"), inline_ads=active_ads("inline"))

@app.route("/seccion/<category>")
def section(category):
    if category not in CATEGORIES:
        abort(404)
    with db() as con:
        articles = con.execute("SELECT * FROM articles WHERE published=1 AND category=? ORDER BY created_at DESC", (category,)).fetchall()
    return render_template("section.html", category=category, articles=articles)

@app.route("/noticia/<int:article_id>")
def article(article_id):
    with db() as con:
        item = con.execute("SELECT * FROM articles WHERE id=? AND published=1", (article_id,)).fetchone()
        related = con.execute("SELECT * FROM articles WHERE published=1 AND category=? AND id<>? ORDER BY created_at DESC LIMIT 3", (item["category"], article_id)).fetchall() if item else []
    if not item:
        abort(404)
    return render_template("article.html", item=item, related=related, inline_ads=active_ads("inline"))

@app.route("/en-vivo")
def live():
    with db() as con:
        items = con.execute("SELECT * FROM articles WHERE published=1 AND is_breaking=1 ORDER BY created_at DESC").fetchall()
    return render_template("live.html", articles=items)

@app.route("/contacto")
def contact():
    return render_template("contact.html")

@app.route("/admin")
@login_required
def admin():
    with db() as con:
        counts = {
            "articles": con.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
            "published": con.execute("SELECT COUNT(*) FROM articles WHERE published=1").fetchone()[0],
            "ads": con.execute("SELECT COUNT(*) FROM ads").fetchone()[0],
            "ephemerides": con.execute("SELECT COUNT(*) FROM ephemerides").fetchone()[0]
        }
        recent = con.execute("SELECT * FROM articles ORDER BY created_at DESC LIMIT 6").fetchall()
    return render_template("admin/dashboard.html", counts=counts, recent=recent)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE username=?", (request.form.get("username",""),)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password","")):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("admin"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin/noticias")
@login_required
def admin_articles():
    with db() as con:
        articles = con.execute("SELECT * FROM articles ORDER BY created_at DESC").fetchall()
    return render_template("admin/articles.html", articles=articles)

@app.route("/admin/noticia/nueva", methods=["GET", "POST"])
@app.route("/admin/noticia/<int:article_id>/editar", methods=["GET", "POST"])
@login_required
def edit_article(article_id=None):
    with db() as con:
        item = con.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone() if article_id else None
    if article_id and not item:
        abort(404)
    if request.method == "POST":
        image = upload_image("image") or (item["image"] if item else "")
        values = (request.form["title"].strip(), request.form.get("summary","").strip(),
                  request.form.get("body","").strip(), request.form.get("category","Argentina"),
                  image, request.form.get("author","Redacción").strip(),
                  1 if request.form.get("is_featured") else 0,
                  1 if request.form.get("is_breaking") else 0,
                  1 if request.form.get("published") else 0,
                  request.form.get("source_url","").strip())
        with db() as con:
            if item:
                con.execute("""UPDATE articles SET title=?,summary=?,body=?,category=?,image=?,author=?,is_featured=?,is_breaking=?,published=?,source_url=? WHERE id=?""", values + (article_id,))
            else:
                con.execute("""INSERT INTO articles(title,summary,body,category,image,author,is_featured,is_breaking,published,source_url,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""", values + (datetime.now().isoformat(timespec="minutes"),))
        flash("Noticia guardada correctamente.", "success")
        return redirect(url_for("admin_articles"))
    return render_template("admin/article_form.html", item=item)

@app.post("/admin/noticia/<int:article_id>/eliminar")
@login_required
def delete_article(article_id):
    with db() as con:
        con.execute("DELETE FROM articles WHERE id=?", (article_id,))
    flash("Noticia eliminada.", "success")
    return redirect(url_for("admin_articles"))

@app.route("/admin/publicidades", methods=["GET", "POST"])
@login_required
def admin_ads():
    if request.method == "POST":
        image = upload_image("image")
        with db() as con:
            con.execute("""INSERT INTO ads(name,placement,image,target_url,starts_on,ends_on,active) VALUES(?,?,?,?,?,?,?)""",
                (request.form["name"], request.form["placement"], image, request.form.get("target_url",""),
                 request.form.get("starts_on",""), request.form.get("ends_on",""), 1 if request.form.get("active") else 0))
        flash("Publicidad agregada.", "success")
        return redirect(url_for("admin_ads"))
    with db() as con:
        ads = con.execute("SELECT * FROM ads ORDER BY id DESC").fetchall()
    return render_template("admin/ads.html", ads=ads)

@app.post("/admin/publicidad/<int:ad_id>/eliminar")
@login_required
def delete_ad(ad_id):
    with db() as con:
        con.execute("DELETE FROM ads WHERE id=?", (ad_id,))
    flash("Publicidad eliminada.", "success")
    return redirect(url_for("admin_ads"))

@app.route("/admin/efemerides", methods=["GET", "POST"])
@login_required
def admin_ephemerides():
    if request.method == "POST":
        with db() as con:
            con.execute("INSERT OR IGNORE INTO ephemerides(month,day,title,description) VALUES(?,?,?,?)",
                (int(request.form["month"]), int(request.form["day"]), request.form["title"], request.form.get("description","")))
        flash("Efeméride guardada.", "success")
        return redirect(url_for("admin_ephemerides"))
    with db() as con:
        items = con.execute("SELECT * FROM ephemerides ORDER BY month,day").fetchall()
    return render_template("admin/ephemerides.html", items=items)

@app.post("/admin/efemeride/<int:item_id>/eliminar")
@login_required
def delete_ephemeris(item_id):
    with db() as con:
        con.execute("DELETE FROM ephemerides WHERE id=?", (item_id,))
    flash("Efeméride eliminada.", "success")
    return redirect(url_for("admin_ephemerides"))

@app.route("/admin/clave", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        if request.form.get("new_password","") != request.form.get("confirm_password","") or len(request.form.get("new_password","")) < 10:
            flash("Las contraseñas deben coincidir y tener al menos 10 caracteres.", "error")
        else:
            with db() as con:
                con.execute("UPDATE users SET password_hash=? WHERE id=?",
                    (generate_password_hash(request.form["new_password"]), session["user_id"]))
            flash("Contraseña actualizada.", "success")
            return redirect(url_for("admin"))
    return render_template("admin/password.html")

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)

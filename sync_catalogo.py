#!/usr/bin/env python3
"""
sync_catalogo.py — Sincroniza productos del Hub Art4Hotel al sitio web público.

Qué hace:
  1. Se conecta al Hub (default http://localhost:4401 — el Hub corre en ESTA máquina;
     override con la variable de entorno A4H_HUB)
  2. Toma los productos marcados con "Mostrar en web" (🌐) que tengan foto
     (excluye los exclusivos de un cliente — regla 2026-07-29 de WEB.md)
  3. Descarga sus fotos a Recursos/catalogo/
  4. Genera productos.json (lo que lee el sitio)
  5. (opcional) Hace commit + push a GitHub → el sitio se actualiza solo

Uso:
  python sync_catalogo.py            # descarga, genera JSON, commit y push
  python sync_catalogo.py --no-push  # solo descarga y genera JSON (para revisar antes)

Requisitos: Python 3 + Pillow (venv .venv de este repo). El Hub exige sesión: el script
genera un token importando /opt/art4hotel-hub/server.py (make_session); si corres el
script fuera de esta máquina, define la cookie en la variable de entorno A4H_SESSION.
"""
import json, urllib.request, urllib.error, urllib.parse, os, sys, subprocess, datetime, re

# Forzar UTF-8 en consola de Windows (evita UnicodeEncodeError con acentos/emoji)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HUB = os.environ.get("A4H_HUB", "http://localhost:4401")
HUB_DIR = os.environ.get("A4H_HUB_DIR", "/opt/art4hotel-hub")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOGO_DIR = os.path.join(REPO_DIR, "Recursos", "catalogo")
JSON_OUT = os.path.join(REPO_DIR, "productos.json")
TIMEOUT = 15
MAX_DIM = 1200       # lado máximo de la foto en el sitio
JPEG_QUALITY = 82    # calidad de compresión

try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def log(msg): print(msg, flush=True)

def hub_session_token():
    """Token de sesión del Hub: A4H_SESSION si está definida, si no se genera
    importando el server del Hub (misma máquina). None = intentar sin auth."""
    token = os.environ.get("A4H_SESSION")
    if token:
        return token
    try:
        sys.path.insert(0, HUB_DIR)
        import server as hub_server  # arranque HTTP protegido por __main__; init_db idempotente
        return hub_server.make_session("sync-catalogo")
    except Exception as e:
        log(f"  ⚠ No se pudo generar sesión del Hub ({e}) — intentando sin auth.")
        return None

SESSION_TOKEN = hub_session_token()

def _request(url):
    req = urllib.request.Request(url)
    if SESSION_TOKEN:
        req.add_header("Cookie", f"a4h_session={SESSION_TOKEN}")
    return req

def fetch_json(path):
    url = HUB + path
    with urllib.request.urlopen(_request(url), timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))

# Clientes "de prestigio" cuyo nombre sí mostramos como prueba social en la web
TIPOS_RECONOCIBLES = {"hotel", "restaurante"}

# Categorías de presentación web (2026-09-04): la web resume la clasificación del Hub.
CATEGORIA_WEB = {
    "Bolsas": "Gifting",
    "bolsa": "Gifting",
    "Cerámica": "Gifting",
    "Accesorios": "Gifting",
    "Mandiles": "Gifting",
    "Sombreros": "Gifting",
}
# Orden de aparición de las categorías en el catálogo público
CAT_WEB_ORDEN = ["Gifting", "Amenidades de baño", "Pantuflas"]

# Foto representativa de la categoría en el grid de navegación (decisión del usuario):
# el producto configurado aquí va PRIMERO dentro de su grupo (y da la foto del tile).
# Valor = fragmento del nombre, minúsculas, sin acentos.
def _norm(s):
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", (s or "").lower().strip()) if unicodedata.category(ch) != "Mn")

CAT_WEB_PORTADA = {
    "Amenidades de baño": "bolsa de manta para kit sustentable",
}

def descargar_comprimir(foto_url, dest_path):
    """Descarga una foto del Hub y la guarda comprimida (JPEG). Devuelve (orig_kb, new_kb)."""
    # La URL puede traer acentos/caracteres no-ASCII (nombres de archivo originales) — percent-encode
    url = HUB + urllib.parse.quote(foto_url, safe="/%")
    with urllib.request.urlopen(_request(url), timeout=TIMEOUT) as r:
        data = r.read()
    orig_kb = len(data) // 1024
    if HAS_PIL:
        img = Image.open(io.BytesIO(data))
        if img.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1])
            img = bg
        else:
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > MAX_DIM:
            ratio = MAX_DIM / max(w, h)
            img = img.resize((round(w*ratio), round(h*ratio)), Image.LANCZOS)
        img.save(dest_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        return orig_kb, os.path.getsize(dest_path) // 1024
    else:
        with open(dest_path, "wb") as fh:
            fh.write(data)
        return orig_kb, orig_kb

def main():
    no_push = "--no-push" in sys.argv

    log("═══ Sync catálogo Art4Hotel ═══")
    log(f"Hub: {HUB}")

    # 1. Verificar conexión al Hub
    try:
        productos = fetch_json("/api/productos")
        file_index = fetch_json("/api/file-counts")
        ordenes = fetch_json("/api/ordenes")
        clientes = fetch_json("/api/clientes")
    except (urllib.error.URLError, OSError) as e:
        log(f"\n✗ No se pudo conectar al Hub ({e}).")
        log("  Asegúrate de estar en la misma red que el servidor (192.168.50.46).")
        sys.exit(1)

    # Mapa cliente -> tipo (para mostrar nombre solo de hoteles/restaurantes)
    tipo_cliente = {c.get("nombre"): (c.get("tipo") or "").lower() for c in clientes}

    # 2. Filtrar: marcados para web Y con foto (y NO exclusivos de un cliente)
    seleccionados = []
    for p in productos:
        if int(p.get("mostrar_en_web") or 0) != 1:
            continue
        if int(p.get("activo") or 0) != 1:
            continue
        # Regla 2026-07-29 (WEB.md): diseños propiedad de un cliente nunca se publican,
        # aunque el flag mostrar_en_web se haya activado por SQL
        if (p.get("exclusivo_de") or "").strip():
            log(f"  ⚠ '{p['nombre']}' es exclusivo de '{p['exclusivo_de']}' — se omite por privacidad.")
            continue
        key = "prod-" + (p.get("sku") or str(p.get("id")))
        info = file_index.get(key) or {}
        first_image = info.get("first_image")
        if not first_image:
            log(f"  ⚠ '{p['nombre']}' está marcado para web pero NO tiene foto — se omite.")
            continue
        p["_foto_url"] = first_image
        p["_key"] = key
        seleccionados.append(p)

    if not seleccionados:
        log("\n⚠ Ningún producto marcado para web (con foto).")
        log("  Ve al Hub → Productos y marca el toggle 🌐 Web en los que quieras publicar.")
        sys.exit(0)

    log(f"\n✓ {len(seleccionados)} producto(s) para publicar:")

    # 3. Descargar fotos
    os.makedirs(CATALOGO_DIR, exist_ok=True)
    # Limpiar fotos viejas del catálogo (las regeneramos)
    for f in os.listdir(CATALOGO_DIR):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            os.remove(os.path.join(CATALOGO_DIR, f))

    if not HAS_PIL:
        log("\n⚠ Pillow no está instalado — las fotos se publican SIN comprimir (pesadas).")
        log("  Recomendado: pip install Pillow")

    total_ejemplos = 0
    catalogo = []
    for p in seleccionados:
        sku = p.get("sku") or str(p["id"])
        safe_sku = re.sub(r"[^\w\-.]", "_", sku)
        # ── Foto base ──
        try:
            fname = safe_sku + ".jpg"
            ok, nk = descargar_comprimir(p["_foto_url"], os.path.join(CATALOGO_DIR, fname))
        except (urllib.error.URLError, OSError) as e:
            log(f"   ✗ Error con foto de '{p['nombre']}': {e}")
            continue

        # ── Ejemplos: pedidos con foto cuyo producto coincide ──
        nombre_lower = (p["nombre"] or "").lower().strip()
        ejemplos = []
        for o in ordenes:
            if (o.get("producto") or "").lower().strip() != nombre_lower:
                continue
            # Solo ejemplos marcados explícitamente para web (curaduría manual)
            if int(o.get("web_ejemplo") or 0) != 1:
                continue
            fi = file_index.get(o["orden_id"]) or {}
            if not fi.get("first_image"):
                continue
            ej_fname = "ej-" + re.sub(r"[^\w\-.]", "_", o["orden_id"]) + ".jpg"
            try:
                descargar_comprimir(fi["first_image"], os.path.join(CATALOGO_DIR, ej_fname))
            except (urllib.error.URLError, OSError):
                continue
            # Etiqueta pública SOLO la manual (zona/"muestra") — nunca el cliente real
            ejemplos.append({
                "foto": f"Recursos/catalogo/{ej_fname}",
                "trabajo": o.get("tipo_trabajo") or "",
                "cliente": (o.get("web_etiqueta") or "").strip(),
            })
        total_ejemplos += len(ejemplos)

        # ── Ejemplos DIRECTOS del producto (2026-09-04): fotos subidas al producto con
        # prefijo web_ (sin pedido de por medio). La etiqueta pública viaja en el nombre:
        # web_{ts}_{Etiqueta}.jpg (regla: zona o "muestra", nunca el cliente real) ──
        try:
            pfiles = fetch_json("/api/files/" + urllib.parse.quote(p["_key"]))
        except (urllib.error.URLError, OSError):
            pfiles = []
        directos = [f for f in pfiles if f.get("is_image") and f["name"].startswith("web_")]
        n_dir = 0
        for n, f in enumerate(directos, 1):
            ej_fname = f"web-{safe_sku}-{n}.jpg"
            try:
                descargar_comprimir(f["url"], os.path.join(CATALOGO_DIR, ej_fname))
            except (urllib.error.URLError, OSError):
                continue
            partes = f["name"].rsplit(".", 1)[0].split("_")
            etiqueta = " ".join(partes[3:]).strip() if len(partes) >= 4 else ""
            ejemplos.append({
                "foto": f"Recursos/catalogo/{ej_fname}",
                "trabajo": "",
                "cliente": etiqueta,
            })
            n_dir += 1
        total_ejemplos += n_dir
        if n_dir:
            log(f"     ↳ {n_dir} ejemplo(s) directo(s) del producto")
        log(f"   • {p['nombre']}  (base {ok}→{nk} KB · {len(ejemplos)} ejemplos)")

        # Personalizaciones: desde tipos_trabajo_disponibles (CSV) si existe
        pers = []
        raw = (p.get("tipos_trabajo_disponibles") or "").strip()
        if raw:
            pers = [x.strip() for x in re.split(r"[,;|]", raw) if x.strip()]
        # Si no se definieron, inferirlas de las técnicas usadas en los ejemplos
        if not pers and ejemplos:
            pers = sorted({e["trabajo"] for e in ejemplos if e["trabajo"]})

        catalogo.append({
            "sku": sku,
            "nombre": p["nombre"],
            "descripcion": (p.get("descripcion_web") or "").strip(),
            "categoria": (p.get("categoria") or "").strip(),
            # Categoría de PRESENTACIÓN (2026-09-04, decisión del usuario): el Hub conserva
            # la clasificación operativa, pero la web la resume — bolsas, taza y accesorios
            # de regalo se presentan juntos como "Gifting".
            "categoria_web": CATEGORIA_WEB.get((p.get("categoria") or "").strip(), (p.get("categoria") or "").strip()),
            "personalizaciones": pers,
            "foto": f"Recursos/catalogo/{fname}",
            "ejemplos": ejemplos,
        })

    # Orden de presentación: primero las categorías resumidas más comerciales;
    # dentro de cada grupo, el producto portada (CAT_WEB_PORTADA) va primero
    catalogo.sort(key=lambda x: (
        CAT_WEB_ORDEN.index(x["categoria_web"]) if x["categoria_web"] in CAT_WEB_ORDEN else 99,
        0 if CAT_WEB_PORTADA.get(x["categoria_web"], "\x00") in _norm(x["nombre"]) else 1,
        _norm(x["nombre"])))

    # 4. Generar productos.json
    out = {
        "generado": datetime.datetime.now().isoformat(timespec="seconds"),
        "productos": catalogo,
    }
    with open(JSON_OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    log(f"\n✓ productos.json generado ({len(catalogo)} productos · {total_ejemplos} ejemplos)")

    # 5. Git commit + push
    if no_push:
        log("\n(--no-push) Listo. Revisa los cambios y haz commit/push manualmente cuando quieras.")
        return

    log("\n═══ Publicando al sitio (git) ═══")
    def git(*args):
        return subprocess.run(["git", "-C", REPO_DIR, *args],
                              capture_output=True, text=True)
    git("add", "productos.json", "Recursos/catalogo")
    status = git("status", "--porcelain")
    if not status.stdout.strip():
        log("  Sin cambios — el sitio ya estaba actualizado.")
        return
    msg = f"Sync catálogo: {len(catalogo)} productos ({datetime.date.today().isoformat()})"
    commit = git("commit", "-m", msg)
    if commit.returncode != 0:
        log(f"  ✗ Error en commit:\n{commit.stderr}")
        return
    push = git("push", "origin", "main")
    if push.returncode != 0:
        log(f"  ✗ Error en push:\n{push.stderr}")
        log("  Los cambios están en commit local. Corre 'git push' manualmente.")
        return
    log("  ✓ Publicado. El sitio se actualizará en ~1 minuto en https://www.art4hotel.com")

if __name__ == "__main__":
    main()

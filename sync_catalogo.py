#!/usr/bin/env python3
"""
sync_catalogo.py — Sincroniza productos del Hub Art4Hotel al sitio web público.

Qué hace:
  1. Se conecta al Hub (http://192.168.50.46:4401)
  2. Toma los productos marcados con "Mostrar en web" (🌐) que tengan foto
  3. Descarga sus fotos a Recursos/catalogo/
  4. Genera productos.json (lo que lee el sitio)
  5. (opcional) Hace commit + push a GitHub → el sitio se actualiza solo

Uso:
  python sync_catalogo.py            # descarga, genera JSON, commit y push
  python sync_catalogo.py --no-push  # solo descarga y genera JSON (para revisar antes)

Requisitos: Python 3 (solo librería estándar). Estar conectado a la red del Hub.
"""
import json, urllib.request, urllib.error, os, sys, subprocess, datetime, re

# Forzar UTF-8 en consola de Windows (evita UnicodeEncodeError con acentos/emoji)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HUB = "http://192.168.50.46:4401"
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

def fetch_json(path):
    url = HUB + path
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    no_push = "--no-push" in sys.argv

    log("═══ Sync catálogo Art4Hotel ═══")
    log(f"Hub: {HUB}")

    # 1. Verificar conexión al Hub
    try:
        productos = fetch_json("/api/productos")
        file_index = fetch_json("/api/file-counts")
    except (urllib.error.URLError, OSError) as e:
        log(f"\n✗ No se pudo conectar al Hub ({e}).")
        log("  Asegúrate de estar en la misma red que el servidor (192.168.50.46).")
        sys.exit(1)

    # 2. Filtrar: marcados para web Y con foto
    seleccionados = []
    for p in productos:
        if int(p.get("mostrar_en_web") or 0) != 1:
            continue
        if int(p.get("activo") or 0) != 1:
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

    catalogo = []
    for p in seleccionados:
        sku = p.get("sku") or str(p["id"])
        src_ext = (os.path.splitext(p["_foto_url"])[1] or ".png").split("?")[0]
        safe_sku = re.sub(r"[^\w\-.]", "_", sku)
        try:
            with urllib.request.urlopen(HUB + p["_foto_url"], timeout=TIMEOUT) as r:
                data = r.read()
            orig_kb = len(data) // 1024
            if HAS_PIL:
                # Redimensionar a MAX_DIM y comprimir a JPEG
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
                fname = safe_sku + ".jpg"
                dest = os.path.join(CATALOGO_DIR, fname)
                img.save(dest, "JPEG", quality=JPEG_QUALITY, optimize=True)
                new_kb = os.path.getsize(dest) // 1024
                log(f"   • {p['nombre']}  ({orig_kb} KB → {new_kb} KB)")
            else:
                fname = safe_sku + src_ext
                dest = os.path.join(CATALOGO_DIR, fname)
                with open(dest, "wb") as fh:
                    fh.write(data)
                log(f"   • {p['nombre']}  ({orig_kb} KB)")
        except (urllib.error.URLError, OSError) as e:
            log(f"   ✗ Error con foto de '{p['nombre']}': {e}")
            continue

        # Personalizaciones: desde tipos_trabajo_disponibles (CSV) si existe
        pers = []
        raw = (p.get("tipos_trabajo_disponibles") or "").strip()
        if raw:
            pers = [x.strip() for x in re.split(r"[,;|]", raw) if x.strip()]

        catalogo.append({
            "sku": sku,
            "nombre": p["nombre"],
            "descripcion": (p.get("descripcion_web") or "").strip(),
            "personalizaciones": pers,
            "foto": f"Recursos/catalogo/{fname}",
        })

    # 4. Generar productos.json
    out = {
        "generado": datetime.datetime.now().isoformat(timespec="seconds"),
        "productos": catalogo,
    }
    with open(JSON_OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    log(f"\n✓ productos.json generado ({len(catalogo)} productos)")

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

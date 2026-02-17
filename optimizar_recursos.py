"""
Script para optimizar recursos de art4hotel
- Crear favicons PNG desde SVG
- Optimizar imágenes grandes
- Generar versiones WebP
"""

import os
import subprocess
from pathlib import Path

RECURSOS_DIR = Path("Recursos")

def check_tools():
    """Verificar que las herramientas necesarias estén instaladas"""
    tools = {
        'magick': 'ImageMagick (para convertir SVG a PNG)',
        'cwebp': 'WebP (para convertir a WebP)'
    }

    missing = []
    for tool, description in tools.items():
        try:
            result = subprocess.run([tool, '-version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            if result.returncode == 0:
                print(f"✓ {tool} encontrado")
            else:
                missing.append((tool, description))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            missing.append((tool, description))

    if missing:
        print("\n⚠️  Herramientas faltantes:")
        for tool, desc in missing:
            print(f"  - {tool}: {desc}")
        print("\nPara instalar:")
        print("  ImageMagick: https://imagemagick.org/script/download.php")
        print("  WebP: https://developers.google.com/speed/webp/download")
        return False

    return True

def create_favicons():
    """Crear favicons PNG desde el SVG del icono"""
    print("\n📱 Creando favicons...")

    svg_source = RECURSOS_DIR / "art4hotel-icono-verde.svg"
    if not svg_source.exists():
        print(f"❌ No se encontró {svg_source}")
        return False

    sizes = [
        (16, "favicon-16x16.png"),
        (32, "favicon-32x32.png"),
        (48, "favicon-48x48.png"),
        (192, "favicon-192x192.png"),
    ]

    for size, filename in sizes:
        output = RECURSOS_DIR / filename
        try:
            cmd = [
                'magick',
                'convert',
                '-background', 'none',
                '-density', '300',
                str(svg_source),
                '-resize', f'{size}x{size}',
                str(output)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✓ Creado {filename} ({size}x{size})")
            else:
                print(f"  ❌ Error creando {filename}: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

    return True

def optimize_and_convert_images():
    """Optimizar imágenes grandes y crear versiones WebP"""
    print("\n🖼️  Optimizando imágenes...")

    images = [
        ("hero-textile.jpg", 85, 1920),  # Calidad 85%, ancho máx 1920px
        ("bolsa-boutique.png", 80, 800),
        ("bolsa-2026.png", 80, 800),
    ]

    for filename, quality, max_width in images:
        source = RECURSOS_DIR / filename
        if not source.exists():
            print(f"  ⚠️  No encontrado: {filename}")
            continue

        # Nombre para WebP
        webp_name = source.stem + ".webp"
        webp_output = RECURSOS_DIR / webp_name

        # Crear versión WebP
        try:
            cmd = [
                'cwebp',
                '-q', str(quality),
                '-resize', str(max_width), '0',
                str(source),
                '-o', str(webp_output)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                original_size = source.stat().st_size / (1024 * 1024)  # MB
                webp_size = webp_output.stat().st_size / (1024 * 1024)  # MB
                savings = ((original_size - webp_size) / original_size) * 100
                print(f"  ✓ {filename} → {webp_name}")
                print(f"    {original_size:.2f}MB → {webp_size:.2f}MB (ahorro: {savings:.1f}%)")
            else:
                print(f"  ❌ Error con {filename}: {result.stderr}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    return True

def generate_picture_tags():
    """Generar código HTML <picture> para usar con WebP"""
    print("\n📝 Código HTML sugerido para usar WebP:\n")

    images = [
        ("bolsa-boutique", "Bolsa boutique personalizada"),
        ("bolsa-2026", "Catálogo de bolsas 2026"),
    ]

    for filename, alt_text in images:
        print(f'''<!-- {filename} -->
<picture>
  <source srcset="Recursos/{filename}.webp" type="image/webp">
  <img src="Recursos/{filename}.png" alt="{alt_text}" loading="lazy">
</picture>
''')

def main():
    print("🚀 Optimizador de recursos para art4hotel\n")
    print("=" * 60)

    # Verificar que estamos en el directorio correcto
    if not Path("index.html").exists():
        print("❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto")
        return

    # Verificar herramientas
    if not check_tools():
        print("\n⚠️  Instala las herramientas faltantes y vuelve a ejecutar el script")
        return

    # Ejecutar optimizaciones
    success = True

    if create_favicons():
        print("✅ Favicons creados exitosamente")
    else:
        print("❌ Error al crear favicons")
        success = False

    if optimize_and_convert_images():
        print("✅ Imágenes optimizadas exitosamente")
    else:
        print("❌ Error al optimizar imágenes")
        success = False

    generate_picture_tags()

    if success:
        print("\n" + "=" * 60)
        print("✅ Optimización completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. Revisa las imágenes WebP generadas")
        print("2. Actualiza el HTML para usar <picture> tags")
        print("3. Prueba la página para verificar que todo funciona")
    else:
        print("\n⚠️  Completado con algunos errores. Revisa los mensajes arriba.")

if __name__ == "__main__":
    main()

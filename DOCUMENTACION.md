# Art4Hotel - Documentacion del Sitio Web

Fecha: 2026-02-12

## Resumen
Sitio web estatico (HTML/CSS/JS) para Art4Hotel, orientado a generar solicitudes de cotizacion y presentar el portafolio de servicios.

- Punto de entrada: `index.html`
- Estilos: `styles.css`
- Interaccion/validaciones: `script.js`
- Recursos (logos, SVGs, imagenes): `Recursos/`

## Estructura de Archivos
- `index.html`: Landing page de una sola pagina (one-page) con secciones ancladas.
- `styles.css`: Estilos globales, layout responsivo, animaciones y componentes (botones, tarjetas, navbar).
- `script.js`:
  - Menu mobile (abrir/cerrar)
  - Animaciones de reveal por IntersectionObserver
  - Validacion del formulario de contacto y envio via AJAX (FormSubmit)
- `CNAME`: dominio configurado para GitHub Pages (`www.art4hotel.com`).
- `Recursos/`: logos SVG, headers PNG y graficos de sectores.

## Secciones de la Pagina (index.html)
- Header (sticky):
  - Logo
  - Navegacion anclada: `#inicio`, `#nosotros`, `#servicios`, `#catalogos`, `#contacto`
  - CTA: "Solicitar Cotizacion"
- Hero:
  - Mensaje principal y CTAs (fondo: `Recursos/hero-textile.jpg`)
- Nosotros (`#nosotros`):
  - Propuesta de valor breve (layout editorial limpio, sin visual decorativo)
- Servicios (`#servicios`):
  - Amenidades, textiles, souvenirs, cristaleria, cocina profesional, manufactura propia
- Catalogos (`#catalogos`):
  - Menu seleccionable (Bolsas/Amenidades/Blancos/Accesorios) y galeria con placeholders "Proximamente"
- Diferenciadores:
  - Personalizacion, atencion, transparencia, disponibilidad, solucion integral
- Sectores:
  - Hoteles boutique, restaurantes, eventos
- Contacto (`#contacto`):
  - Formulario de solicitud (fondo limpio con gradiente)
- Footer:
  - Datos de contacto y enlaces de contacto rapido (WhatsApp/Email/Llamar)

## Formulario de Contacto
El formulario esta configurado con FormSubmit:

- `action`: `https://formsubmit.co/ventas@art4hotel.com`
- Envio por AJAX: `https://formsubmit.co/ajax/ventas@art4hotel.com`
- Campos:
  - `nombre` (min 2 chars)
  - `email` (regex basica)
  - `tipo` (select requerido)
  - `mensaje` (min 12 chars)
- Anti-spam:
  - Campo honey: `_honey`
  - Captcha deshabilitado: `_captcha=false`

Notas:
- Si el envio por AJAX falla, el script hace fallback al submit normal del formulario.
- Para produccion, conviene probar que FormSubmit este autorizado para ese correo y que no caiga en spam.

## Recursos (Recursos/)
Principales archivos:
- Logos/branding:
  - `Recursos/art4hotel-logo-principal.svg`
  - `Recursos/art4hotel-logo-oscuro.svg`
  - `Recursos/art4hotel-icono-verde.svg`
- Sectores:
  - `Recursos/sector-hotel.svg`
  - `Recursos/sector-restaurante.svg`
  - `Recursos/sector-eventos.svg`
  - Nota: se removio el sector "Yates" de la web
- Catalogos:
  - `Recursos/bolsa-boutique.png`
  - `Recursos/bolsa-2026.png`
- Headers:
  - `Recursos/web-header-1200x200-oscuro.png`

## Desarrollo Local
Opcion 1 (Python):
```bash
cd "C:\Users\claud\OneDrive\Documentos\Claude\Art 4 Hotel\Pagina Web\art4hotel"
python -m http.server 5500
```
Luego abre: `http://127.0.0.1:5500`

Opcion 2 (VS Code): extension Live Server.

## Publicacion (GitHub + Dominio en Wix)
Este repo esta listo para GitHub Pages (porque es estatico y tiene `index.html` en la raiz).

1. GitHub Pages
- Repo -> Settings -> Pages
- Source: Deploy from branch
- Branch: `main` / folder: `/ (root)`
- Custom domain: `www.art4hotel.com`
- Enforce HTTPS: habilitar cuando GitHub lo permita

2. DNS en Wix (dominio administrado en Wix)
- Mantener el `CNAME` para `www` apuntando a GitHub Pages (segun indique GitHub en Settings -> Pages).
- Para el dominio raiz (`art4hotel.com`), usar:
  - Redireccion a `www` desde Wix, o
  - Registros `A` del apex a GitHub Pages (usar los valores actuales que muestra la documentacion de GitHub).

## Mantenimiento
- Contenido (textos/servicios): `index.html`
- Colores/tipografia/estilos: `styles.css` (variables en `:root`)
- Logica del formulario y menu: `script.js`
- Dominios: `CNAME` y Settings -> Pages

## Pendientes Recomendados
- Revisar/actualizar enlaces de contacto (WhatsApp/Email/Llamar) si cambian.
- Agregar Open Graph/Twitter meta tags para compartir.
- Verificar encoding UTF-8 al editar en Windows para evitar texto con caracteres raros en el editor/terminal.

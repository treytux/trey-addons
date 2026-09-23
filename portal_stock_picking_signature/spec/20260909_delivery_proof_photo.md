# Justificante fotográfico del albarán sellado desde portal

## Objetivo

En el asistente de firma del portal, dar a elegir entre **firmar en pantalla** o
**adjuntar una foto del albarán sellado**. La foto se sube a resolución completa
(sin pasar por el `<canvas>` del widget de firma) y queda disponible en el
albarán de salida. Además, exponer la foto por una URL **sin token**: al abrirla
sin sesión, Odoo redirige a `/web/login`; solo un usuario interno con permiso de
lectura sobre el picking puede verla.

## Alcance de este módulo

Captura desde portal y controlador que sirve la foto con login. Los campos y el
asistente de backend están en `stock_picking_signature`. La reproducción en el
PDF está en `matedi_customize`.

## Decisiones fijadas

- **D-1** Sin token: la URL exige inicio de sesión. Se asume que un destinatario
  externo no podrá abrir el enlace; es aceptable.
- **D-2** `stock_picking_signature` está instalado; se declara en `depends`
  (ya presente).
- **D-3** Resolución máxima 1920 px.
- **D-4** Una sola foto por picking.
- **D-5** Se deshabilita el modo *load* del widget de firma.
- **D-6** Foto y URL van debajo de las líneas de producto en el PDF.

## Portal — plantilla (`portal_template.xml`)

- En `portal_my_pending_picking`, añadir un selector de modo con dos pestañas:
  «Firmar en pantalla» / «Foto del albarán sellado» (cadenas de origen en
  inglés).
- Modo firma: se reutiliza `portal.signature_form`, quitando `load` de su
  `data-mode` para forzar dibujo manual.
- Modo foto: `<input type="file" accept="image/*" capture="environment"
  class="js_psps_proof_input">` + previsualización (`js_psps_proof_preview`) +
  nombre de archivo (`js_psps_proof_name`) + botón de envío
  (`js_psps_proof_submit`).
- En `pending_picking_portal_content`, mostrar la foto ya guardada sin el tope de
  `6rem` para que se vea legible.

## Portal — JS (`static/src/js/portal_stock_picking_signature_proof.js`)

Patrón heredado del módulo: `odoo.define(...)` con `web.Class` / `web.dom_ready`
(no OWL). Flujo: `FileReader.readAsDataURL` → POST JSON a
`/my/pending_picking/<id>/accept_photo` → `window.location = redirect_url`.
Registrar el archivo en `assets['web.assets_frontend']` del manifiesto, en orden
alfabético.

## Controladores (`controllers/main.py`)

### `POST /my/pending_picking/<int:picking_id>/accept_photo` — `type='json'`, `auth='public'`

Mismo patrón que `.../accept`: `_document_check_access('stock.picking', id,
access_token=...)`; si no hay imagen, `{'error': _('Photo is missing.')}`. Crea
el `ir.attachment` con `sudo()` (necesario: el visitante del portal no tiene
permiso de creación de adjuntos sobre `stock.picking`) y escribe en el picking
`delivery_proof_image`, `delivery_proof_filename`,
`delivery_proof_attachment_id`, `signed_by`, `pending_signed='signed'` y
`signature_datetime`. Devuelve `{'force_refresh': True, 'redirect_url':
'/my/picking_sign'}`.

### `GET /picking/<int:picking_id>/delivery_proof` — `type='http'`, `auth='user'`, `website=True`

Sirve la foto con login (D-1). `auth='user'` hace que un anónimo sea redirigido
a `/web/login?redirect=...` en lugar de recibir el marcador de posición de
`/web/image`. Comprueba acceso con el usuario real
(`check_access_rights('read')` + `check_access_rule('read')`); si no hay adjunto,
`request.not_found()`. Devuelve el stream vía
`request.env['ir.binary']._get_stream_from(attachment.sudo(), 'raw')`
(`sudo()` solo para leer el binario, después de haber validado el acceso al
picking). Acepta `?download=1` para forzar descarga.

## Vistas de backend (`views/stock_picking_views.xml`)

Sin cambios funcionales nuevos respecto a la firma; la foto se muestra desde
`stock_picking_signature`. Mantener el botón «Sign from portal» existente.

## Textos e i18n

Cadenas de origen en inglés; traducción en `i18n/es.po` con cabeceras Trey, sin
`msgstr` vacíos; regenerar con `oo db translate <db> es_ES`. Eliminar el residuo
`i18n/es.po~`. Ejemplos: `Sign on screen`, `Photo of the stamped delivery note`,
`Photo is missing.`, `Take or choose a photo`.

## Versionado y manifiesto

`16.0.1.1.0` → `16.0.1.2.0` (rutas y asset nuevos, cambios de vista). Confirmar
el valor de partida antes de editar. Registrar el nuevo `.js` en `assets` en
orden alfabético; mantener `data` en orden alfabético; no añadir
`'installable': True`.

## Nota de despliegue

La subida de fotos desde móvil puede superar el límite de tamaño de petición;
revisar `client_max_body_size` en nginx si se rechazan subidas grandes.

## Validación

Pruebas de ruta con `HttpCase`; de modelo/asistente con `TransactionCase`:

- `accept_photo` guarda foto a resolución completa + adjunto +
  `pending_signed='signed'`.
- `accept_photo` sin token válido → error.
- `accept_photo` sin imagen → `{'error': ...}`.
- `/picking/<id>/delivery_proof` sin sesión → 302 a `/web/login`.
- `/picking/<id>/delivery_proof` con usuario sin acceso (incluido usuario de
  portal) → 403.
- `/picking/<id>/delivery_proof` con usuario interno de stock → 200 y
  `Content-Type` de imagen.

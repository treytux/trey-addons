# Captura de justificante fotográfico del albarán sellado

## Objetivo

Permitir que, además de la firma manuscrita en pantalla, se pueda adjuntar una
**foto del albarán en papel sellado** (sello de empresa en lugar de firma) como
prueba de entrega. La foto debe conservarse a resolución completa, sin pasar por
el lienzo del widget de firma, para que sea legible al reproducirla en el PDF.

## Contexto del problema

El widget `signature` (`name_and_signature.js`, modo *load*) dibuja la imagen
cargada sobre el `<canvas>` de pantalla (~300 px) y exporta ese lienzo reducido.
Cualquier foto subida por ese camino llega al servidor rasterizada y diminuta,
inservible como prueba de entrega. La solución es capturar la foto por un campo
`fields.Image` real (backend) o un `<input type="file">` plano (portal, ver
`portal_stock_picking_signature`), sin tocar el `<canvas>`.

## Alcance de este módulo

Capa de datos y captura desde backend. La captura y visualización desde portal
está en `portal_stock_picking_signature`; la reproducción en el PDF del albarán
de salida está en `matedi_customize`.

## Modelo de datos — `stock.picking`

Campos nuevos (se mantienen separados de `signature`, que sigue siendo
`fields.Binary` de forma deliberada):

- `delivery_proof_image` (`fields.Image`, `max_width=1920`, `max_height=1920`,
  `copy=False`) — foto del albarán sellado. `fields.Image` acota la resolución
  en la escritura y `attachment=True` es su valor por defecto.
- `delivery_proof_filename` (`fields.Char`, `copy=False`).
- `delivery_proof_attachment_id` (`fields.Many2one('ir.attachment'`,
  `copy=False`, `ondelete='set null'`) — adjunto asociado, para descarga y para
  servirlo por URL con login.

`is_signed` (campo estándar de `stock`) pasa a considerarse verdadero también
con foto:

```python
@api.depends('signature', 'delivery_proof_image')
def _compute_is_signed(self):
    super()._compute_is_signed()
    for picking in self:
        picking.is_signed = picking.is_signed or bool(picking.delivery_proof_image)
```

## Asistente — `wizard.stock.picking.signature`

- `capture_mode` (`fields.Selection`, opciones `sign` / `photo`, `default='sign'`,
  `required=True`, widget `radio`).
- `proof_image` (`fields.Image`).
- `signature` deja de ser `required=True`; la obligatoriedad se resuelve por
  `attrs` según `capture_mode` y con un `@api.constrains` que exige firma en
  modo `sign` y foto en modo `photo`.
- `button_accept_sign` bifurca: en modo `photo` escribe
  `delivery_proof_image` / `delivery_proof_filename` en el picking y crea el
  `ir.attachment` (`res_model='stock.picking'`, `res_id`), guardando su id en
  `delivery_proof_attachment_id`; en modo `sign` mantiene el comportamiento
  actual.

## Vistas

- Formulario del asistente: `capture_mode` arriba; `signature widget="signature"`
  y `proof_image widget="image"` mutuamente excluyentes por `attrs`.
- Formulario de `stock.picking` (página `picking_signature`): mostrar
  `delivery_proof_image` (`widget="image"`, solo lectura) junto a la firma.

## Textos e i18n

Cadenas de origen en inglés. Traducción al español en `i18n/es.po` con
cabeceras Trey (`Last-Translator: Trey <info@trey.es>`,
`Language-Team: Trey <info@trey.es>`, `Language: es_ES`), sin `msgstr` vacíos.
Regenerar con `oo db translate <db> es_ES`. Ejemplos:
`Stamped delivery note photo`, `Handwritten signature`,
`A handwritten signature is required.`, `A photo of the delivery note is required.`

## Versionado

`16.0.1.1.0` → `16.0.1.2.0` (campo nuevo = cambio de esquema, requiere
actualización de módulo). Confirmar el valor de partida con quien mantiene la
rama antes de editar el manifiesto.

## Validación

Pruebas (`TransactionCase`):

- El modo `photo` del asistente escribe `delivery_proof_image`,
  `delivery_proof_filename` y `delivery_proof_attachment_id`, y crea el adjunto.
- El modo `sign` sin firma lanza `ValidationError`.
- `is_signed` es verdadero con solo foto y con solo firma.
- La foto se guarda a resolución completa (no reducida a ~300 px).

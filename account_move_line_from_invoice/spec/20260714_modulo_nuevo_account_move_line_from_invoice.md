# SPEC: Módulo nuevo de account_move_line_from_invoice

## 1. Contexto
- Fecha: 2026-07-14
- Módulo: `account_move_line_from_invoice`
- Origen: el cliente pedía recuperar en v16 el botón de importación de
  líneas de factura por Excel que existía en v12
  (`account_invoice_usability`). Se decide alinear el módulo al patrón de
  casa `account_move_line_from_partner`, pero partiendo de la factura en
  lugar de la ficha de empresa.

## 2. Patrón de referencia
`account_move_line_from_partner`:
- Modelo: un `Integer` computado con el contador de apuntes.
- Vista: `ir.actions.act_window` declarativa con `context`
  (`search_default_...` + `active_id`) y `groups_id`; botón `type="action"`
  que invoca la acción por `name="%(...)d"` con `groups=`.
- Sin método Python en el botón, sin `safe_eval` ni `expression.AND`.

## 3. Cambios aplicados
- `account.move`: se sustituye el método `button_open_invoice_lines`
  (que leía la acción a mano, hacía `safe_eval` y `expression.AND`) por el
  patrón declarativo. El modelo queda solo con el campo computado
  `invoice_line_count`.
- Acción `action_account_move_line`: restringe con `groups_id` a los grupos
  contables, igual que el de partner. El contexto solo lleva
  `{'default_move_id': active_id}` (para la creación/importación).
- `domain` de la acción: `[('move_id', '=', active_id),
  ('display_type', 'in', ('product', 'line_section', 'line_note'))]`.
  - Filtrado por factura vía `domain` (igualdad por id), NO por
    `search_default_move_id`. El campo de búsqueda `move_id` de la vista de
    búsqueda estándar de `account.move.line` en el core tiene un
    `filter_domain` de texto (`ilike` sobre `move_id.name`, `move_id.ref` y
    `move_id.partner_id`); con `search_default_move_id` el `active_id`
    numérico se usaba como texto de ese `ilike`, de modo que las facturas
    cuyo nombre no contuviera ese número (p. ej. borradores con nombre `/`)
    devolvían lista vacía. El patrón `search_default_*` de partner no sirve
    aquí porque `partner_id` sí casa por id y `move_id` no.
  - La cláusula `display_type` deja solo las líneas comerciales (el mismo
    subconjunto que `account.move.invoice_line_ids`), ocultando la línea de
    impuesto (`tax`) y la de contrapartida a cobrar/pagar (`payment_term`).
    Así la lista cuadra con el contador `invoice_line_count`. Las líneas
    importadas sin `display_type` se calculan como `product`
    (`_compute_display_type` para facturas), por lo que siguen apareciendo.
- Botón: pasa a `type="action"` apuntando a la acción, con `groups=`.
- Vista `view_move_line_tree_creatable` con `mode="primary"`: se mantiene.
  Es la única pieza que el de partner no necesita (aquel solo consulta;
  aquí se crea/importa). El `mode="primary"` evita que el `create="1"` se
  filtre a la vista compartida `account.view_move_line_tree` de toda la
  aplicación.
- Override de `account.move.line.create`: inyecta `default_move_id` del
  contexto cuando la línea se importa sin columna de factura. Resuelve el
  `KeyError: 'move_id'` del core, que accede a `vals['move_id']` antes de
  aplicar los defaults del contexto.
- Orden de carga en el manifest: `account_move_line.xml` antes que
  `account_move.xml` (vista <- acción <- botón). Prevalece la corrección de
  carga sobre el orden alfabético.

## 4. No objetivos
- No se añade restricción por estado (borrador/validada).
- No se enriquece la vista con columnas adicionales; se usa la estándar
  (más `create="1"`).
- No se migra a un asistente (wizard) dedicado de importación.
- No se toca `account_invoice_usability` (módulo v12, no instalado).

## 5. Validación
- Factura (cliente o proveedor): el botón abre el listado de líneas filtrado
  por la factura, con `default_move_id` en contexto.
- Importar líneas sin columna de factura asigna la factura del contexto sin
  `KeyError` (test `test_create_injects_default_move_id_on_import`).
- El listado filtra por la factura por id (no por nombre) y muestra solo las
  líneas comerciales, no el impuesto ni la contrapartida
  (test `test_action_domain_matches_invoice_lines`), y coincide con el
  contador `invoice_line_count`.
- La vista compartida `account.view_move_line_tree` conserva
  `create="false"` tras instalar el módulo (test de regresión de la fuga).

## 6. Traducciones (2026-07-23)
- Se añade `i18n/account_move_line_from_invoice.pot` e `i18n/es.po`,
  generados con `oo db translate mercadoit160107_copy es_ES` (BBDD donde el
  módulo está instalado) y cabeceras normalizadas a convención Trey
  (`Last-Translator`/`Language-Team: Trey <info@trey.es>`,
  `Language: es_ES`).
- Términos traducidos (4, sin placeholders que preservar):
  - `Invoice line count` → `Recuento de líneas de factura` (label del campo
    computado `invoice_line_count`).
  - `Invoice lines` → `Líneas de factura` (nombre de la acción
    `action_account_move_line` y label del botón stat en el form de factura).
  - `Journal Entry` → `Asiento contable` (nombre de modelo `account.move`,
    término estándar del núcleo de Odoo, exportado porque el módulo añade
    campos a ese modelo).
  - `Journal Item` → `Apunte contable` (nombre de modelo `account.move.line`,
    mismo caso).
- Criterio de terminología: se usa "líneas de factura" en vez de "apuntes
  contables" (que sí usa el módulo de referencia
  `account_move_line_from_partner` para su acción genérica) porque aquí el
  dominio ya está acotado a las líneas comerciales de una factura concreta
  (ver `domain` de la acción en el punto 3), y así queda consistente con el
  lenguaje del propio spec.
- No se toca el manifest: Odoo carga `i18n/*.po` automáticamente sin
  declararlo en `data`, igual que en `account_move_line_from_partner`.

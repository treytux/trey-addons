# Spec Template

## Summary
- Objective:
  Migrar el módulo `purchase_propagated_comment` (Adarra) de Odoo 12 a Odoo
  16, creándolo como módulo propio en `trey-addons`, manteniendo su
  funcionalidad: propagar un comentario desde el pedido de compra (o desde
  el contacto proveedor) hacia los albaranes de entrada y las facturas de
  proveedor generadas.
- Target module:
  `purchase_propagated_comment`
- Business scope:
  El comentario se define en el contacto proveedor o en el propio pedido de
  compra, se muestra como aviso en el albarán de entrada asociado y se
  concatena en la factura de proveedor cuando sus líneas provienen de uno o
  varios pedidos de compra con comentario.

## Implementation Changes
- Backend:
  Eliminado el decorador obsoleto `@api.multi` en
  `models/purchase_order.py`. El campo `purchase_propagated_comment` en
  `purchase.order` pasa de campo simple con `@api.onchange('partner_id')` a
  campo `compute='_compute_purchase_propagated_comment'`, `store=True`,
  `readonly=False`, `precompute=True`, con `@api.depends('partner_id')`,
  para que también funcione en creaciones vía API/import y no solo desde el
  formulario.

  Renombrado `models/account_invoice.py` a `models/account_move.py`:
  `_inherit` pasa de `account.invoice` a `account.move`; el `@api.depends`
  cambia de `invoice_line_ids.purchase_id` a
  `invoice_line_ids.purchase_line_id`; el `mapped()` pasa de
  `purchase_id.purchase_propagated_comment` a
  `purchase_line_id.order_id.purchase_propagated_comment` (en v16 la línea
  de factura no tiene relación directa `purchase_id`, sino
  `purchase_line_id` hacia `purchase.order.line`).

  En `models/stock_picking.py`, el `@api.depends` y el `mapped()` cambian de
  `move_lines` a `move_ids` (campo renombrado en `stock.picking` desde
  Odoo 13).

  `models/res_partner.py` sin cambios funcionales.
- Frontend:
  `views/account_invoice_views.xml` renombrado a `views/account_move_views.xml`
  (convención: nombre de archivo de vista = nombre del modelo). El `inherit_id`
  pasa de `account.invoice_form` a `account.view_move_form`, y el `record id`
  de `invoice_form` a `view_move_form` para coincidir con la vista heredada.
  El punto de anclaje deja de ser `<field name="comment" position="after">`
  (el campo `comment` no existe en `account.move`) y pasa a un `xpath`
  sobre el campo `narration` (la vista `account.view_move_form` tiene dos
  campos `narration`: uno en la pestaña de factura, y otro en "Other Info"
  visible solo para asientos contables `move_type = 'entry'`; se necesita
  el primero, no el segundo). Un primer intento seleccionó ese campo con
  `@placeholder='Terms and Conditions'`, pero Odoo rechaza en tiempo de
  carga cualquier `xpath` de herencia que use un atributo traducible
  (`placeholder` incluido) como selector, con el error "View inheritance
  may not use attribute 'placeholder' as a selector." (ver
  `ir_ui_view.py: TRANSLATED_ATTRS_RE`). El selector final usa la clase
  estable del grupo contenedor:
  `//group[hasclass('oe_invoice_lines_tab')]//field[@name='narration']`,
  que en `account.view_move_form` solo envuelve al campo de la pestaña de
  factura. El `attrs` de invisibilidad pasa de
  `('type', 'not in', [...])` a `('move_type', 'not in', ['in_invoice',
  'in_refund'])`.

  `views/res_partner_views.xml`: un primer intento tradujo el `attrs` de
  invisibilidad de `('supplier', '!=', True)` a `('supplier_rank', '=', 0)`,
  ya que el booleano `supplier` de v12 fue sustituido por el entero
  `supplier_rank` (definido en el módulo `account`). Esa traducción resultó
  inutilizable en la práctica: `supplier_rank`/`customer_rank` solo se
  incrementan al validar una factura/factura de proveedor
  (`account/models/account_move.py:3667-3669`, único punto que llama a
  `_increase_rank` para esos campos aparte de POS); confirmar un pedido de
  venta o de compra NO los incrementa. Se comprobó en la base real
  `matedio_sin_bd`: 0 partners con `supplier_rank > 0` o `customer_rank > 0`
  pese a tener 19 pedidos de venta y 2 de compra confirmados, y 0 facturas
  registradas en `account_move`. Con esa condición, el campo nunca sería
  editable en un proveedor nuevo antes de completarle todo el ciclo compra
  → factura → validar factura, justo lo contrario de su propósito
  (predefinir el comentario antes del primer pedido). Se eliminó el
  `attrs` de invisibilidad: el campo se muestra siempre, igual que el
  campo `comment` estándar justo encima en la misma pestaña. El `xpath`
  sobre `page[@name='internal_notes']` no cambia.

  `views/purchase_order_views.xml` y `views/stock_picking_views.xml` sin
  cambios de xpath: `notes` sigue existiendo en `purchase.purchase_order_form`
  y `//header` sigue existiendo en `stock.view_picking_form`.
- Security:
  Sin cambios. El módulo no define modelos nuevos ni reglas de acceso
  propias; hereda modelos ya cubiertos por `account` y `purchase_stock`.
- Data migration:
  No aplica: es un módulo nuevo en `trey-addons`, no existía instalado en
  ninguna base v16.
- Reporting:
  Sin cambios.

## Test Plan
- Installation:
  Instalar `purchase_propagated_comment` en una base de pruebas con
  `account` y `purchase_stock` instalados.

  Comando sugerido:
  `oo exec <db> -i purchase_propagated_comment --stop-after-init`
- Automated tests:
  `tests/test_propagated_comment.py` migrado: `picking.action_done()` pasa a
  `picking.button_validate()` (método eliminado en `stock.picking` desde
  Odoo 13); el resto de la lógica (`button_confirm`, creación de
  `purchase.order`/`purchase.order.line`) no cambia. El `setUp` crea el
  proveedor con `supplier_rank: 1` en lugar del booleano `supplier: True`.

  Comando sugerido:
  `oo exec <db> -u purchase_propagated_comment --test-enable --stop-after-init`
- Manual smoke tests:
  1. Definir un "Comentario propagado compra" en un contacto proveedor.
  2. Crear un pedido de compra para ese proveedor y comprobar que el
     comentario se propone automáticamente en el pedido.
  3. Confirmar el pedido y comprobar que el albarán de entrada generado
     muestra el aviso con el comentario en la cabecera.
  4. Facturar el pedido y comprobar que la factura de proveedor muestra el
     comentario propagado en la pestaña de condiciones/factura.

## Assumptions
- Assumption 1
  La vista `account.view_move_form` es la única vista de formulario de
  `account.move` relevante para este módulo; no se ha localizado ninguna
  otra vista base que muestre el campo `narration` de "Terms and
  Conditions" para facturas de proveedor.
- Assumption 2
  El campo `purchase_propagated_comment` en el contacto se muestra siempre,
  sin condición de visibilidad. Se descartó gatearlo por `supplier_rank`
  (ver Frontend) por hacerlo impracticable para proveedores nuevos.

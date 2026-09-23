# Spec Template

## Summary
- Objective:
  Migrar el módulo `sale_propagated_comment` (Adarra) de Odoo 12 a Odoo 16,
  creándolo como módulo propio en `trey-addons`, con el mismo patrón ya
  aplicado en `purchase_propagated_comment`: propagar un comentario desde el
  pedido de venta (o desde el contacto cliente) hacia los albaranes de salida
  y las facturas de cliente generadas.
- Target module:
  `sale_propagated_comment`
- Business scope:
  El comentario se define en el contacto cliente o en el propio pedido de
  venta, se muestra como aviso en el albarán de salida asociado y se
  concatena en la factura de cliente cuando sus líneas provienen de uno o
  varios pedidos de venta con comentario.

## Implementation Changes
- Backend:
  El campo `sale_propagated_comment` en `sale.order` no puede reproducirse
  sobrescribiendo `onchange_partner_id` (método eliminado en v16: toda la
  lógica ligada a `partner_id` pasó a campos `compute`). Se implementa como
  campo `compute='_compute_sale_propagated_comment'`, `store=True`,
  `readonly=False`, `precompute=True`, con `@api.depends('partner_id')`,
  igual que `purchase_propagated_comment` en `purchase.order`: se propone al
  elegir cliente, sigue siendo editable después y también funciona en
  creaciones vía API/import.

  Renombrado `models/account_invoice.py` a `models/account_move.py`:
  `_inherit` pasa de `account.invoice` a `account.move`. A diferencia del
  módulo de compra (donde la línea de factura enlaza con `purchase.order`
  mediante `purchase_line_id`, un many2one), en ventas
  `account.move.line.sale_line_ids` es un many2many hacia
  `sale.order.line` (una línea de factura puede repartirse entre varias
  líneas de pedido, p. ej. anticipos). El `@api.depends` usa
  `invoice_line_ids.sale_line_ids` y el `mapped()` usa
  `sale_line_ids.order_id.sale_propagated_comment`.

  En `models/stock_picking.py`, `@api.depends` y `mapped()` usan
  `move_ids` y `move_ids.sale_line_id` (campo `sale_line_id`, many2one,
  añadido por `sale_stock` en `stock.move`; no cambia de nombre entre
  versiones).

  `models/res_partner.py` sin cambios funcionales respecto al patrón de
  `purchase_propagated_comment`.
- Frontend:
  `views/sale_order_views.xml`: el campo se añade con
  `<field name="note" position="after">` en `sale.view_order_form` (en v12
  el campo equivalente también se llamaba `note`, sin cambios de xpath).

  `views/account_move_views.xml`: mismo criterio ya adoptado en
  `purchase_propagated_comment` para evitar el error "View inheritance may
  not use attribute 'placeholder' as a selector" (atributos traducibles no
  son válidos como selector de xpath) y el problema del campo `narration`
  duplicado en `account.view_move_form` (aparece tanto en la pestaña de
  factura como en "Other Info" para asientos contables). Se reutiliza el
  mismo selector estable:
  `//group[hasclass('oe_invoice_lines_tab')]//field[@name='narration']`,
  que en `account.view_move_form` solo envuelve el campo de la pestaña de
  factura. El `attrs` de invisibilidad usa
  `('move_type', 'not in', ['out_invoice', 'out_refund'])` (equivalente de
  venta a `['in_invoice', 'in_refund']` usado en el módulo de compra).

  `views/res_partner_views.xml`: se aplica el mismo criterio ya decidido en
  `purchase_propagated_comment` para el campo del contacto: no se gatea la
  visibilidad con `customer_rank` (equivalente de venta al `supplier_rank`
  descartado en el módulo de compra), porque ese contador solo se
  incrementa al validar una factura de cliente
  (`account/models/account_move.py`, `_increase_rank`), no al confirmar un
  pedido de venta. Con esa condición el campo nunca sería editable en un
  cliente nuevo antes de completarle todo el ciclo venta → factura →
  validar factura, justo lo contrario de su propósito (predefinir el
  comentario antes del primer pedido). El campo se muestra siempre, en un
  grupo separado ("Propagated Comment Sale") dentro de la misma pestaña
  "Notas internas" donde ya vive el campo equivalente de compra.

  `views/stock_picking_views.xml`: mismo xpath `//header` de
  `stock.view_picking_form` usado en el módulo de compra, con su propio
  `div.alert` condicionado a `sale_propagated_comment`.
- Security:
  Sin cambios. El módulo no define modelos nuevos ni reglas de acceso
  propias; hereda modelos ya cubiertos por `account` y `sale_stock`.
- Data migration:
  No aplica: es un módulo nuevo en `trey-addons`, no existía instalado en
  ninguna base v16.
- Reporting:
  Sin cambios.

## Test Plan
- Installation:
  Instalar `sale_propagated_comment` en una base de pruebas con `account` y
  `sale_stock` instalados.

  Comando sugerido:
  `oo exec <db> -i sale_propagated_comment --stop-after-init`
- Automated tests:
  `tests/test_propagated_comment.py`, análogo al del módulo de compra:
  `picking.action_confirm()` / `action_assign()` / `button_validate()` sobre
  el albarán de salida generado al confirmar el pedido de venta
  (`action_confirm()`, no `button_confirm()` como en `purchase.order`). El
  `setUp` crea el cliente con `customer_rank: 1` en lugar del booleano
  `customer: True` de v12.

  Comando sugerido:
  `oo exec <db> -u sale_propagated_comment --test-enable --stop-after-init`
- Manual smoke tests:
  1. Definir un "Comentario propagado venta" en un contacto cliente.
  2. Crear un pedido de venta para ese cliente y comprobar que el
     comentario se propone automáticamente en el pedido.
  3. Confirmar el pedido y comprobar que el albarán de salida generado
     muestra el aviso con el comentario en la cabecera.
  4. Facturar el pedido y comprobar que la factura de cliente muestra el
     comentario propagado en la pestaña de factura.

## Assumptions
- Assumption 1
  La vista `account.view_move_form` es la única vista de formulario de
  `account.move` relevante para este módulo.
- Assumption 2
  El campo `sale_propagated_comment` en el contacto se muestra siempre, sin
  condición de visibilidad, por el mismo motivo ya documentado para
  `purchase_propagated_comment` (ver Frontend).

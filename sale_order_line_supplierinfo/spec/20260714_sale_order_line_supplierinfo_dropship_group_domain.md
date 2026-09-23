# Spec Template

## Summary
- Objective:
  Ajustar la lógica de `_make_po_get_domain()` en
  `sale_order_line_supplierinfo` para que, cuando la línea de venta
  corresponda a un producto dropship, se devuelva el dominio original de
  `super()` y no se elimine `group_id`.
- Target module:
  `sale_order_line_supplierinfo`
- Business scope:
  En un producto con varias rutas, por ejemplo compra y dropship, Odoo puede
  dejar `sale_line.route_id` vacío y resolver la ruta efectiva más tarde.
  La lógica anterior filtraba siempre `group_id` salvo en casos muy concretos,
  lo que rompía el comportamiento esperado de dropshipping. El cambio debe
  reconocer el dropship aunque la ruta de la línea esté vacía, mirando las
  rutas del producto.

## Implementation Changes
- Backend:
  Modificar `addons/trey-addons/sale_order_line_supplierinfo/models/stock_rule.py`
  para que `_make_po_get_domain()`:
  - lea la línea de venta desde `values['sale_line_id']`;
  - recupere la ruta de dropshipping con
    `stock_dropshipping.route_drop_shipping`;
  - considere dropship tanto si `sale_line.route_id` ya apunta a esa ruta
    como si la ruta está presente en `sale_line.product_id.route_ids`;
  - en ese caso devuelva directamente el dominio de `super()`;
  - en caso contrario, mantenga la lógica actual de eliminar el criterio
    `('group_id', ...)` del dominio.

  La condición debe quedar protegida frente a líneas vacías y debe respetar
  la precedencia lógica para no disparar el retorno original por error en
  productos no dropship.

  Añadir o ampliar una regresión en
  `addons/trey-addons/sale_order_line_supplierinfo/tests/test_sale_order_line_supplierinfo.py`
  que cubra:
  - un producto estándar con dominio filtrado sin `group_id`;
  - un producto con rutas `compra + dropship` y `sale_line.route_id` vacío,
    verificando que el dominio devuelto coincide con el de `super()`.
- Frontend:
  Sin cambios.
- Security:
  Sin cambios.
- Data migration:
  Sin migración de datos.
- Reporting:
  Sin cambios.

## Test Plan
- Installation:
  Actualizar el módulo en una base de pruebas con `stock_dropshipping`
  instalado.

  Comando sugerido:
  `oo exec <db_name> -u sale_order_line_supplierinfo --stop-after-init`
- Automated tests:
  Ampliar los tests del módulo para validar dos escenarios:
  - línea de venta sin dropship: `_make_po_get_domain()` sigue quitando
    `group_id`;
  - línea de venta con producto que tiene ruta dropship entre sus rutas,
    aunque `sale_line.route_id` esté vacío: `_make_po_get_domain()` debe
    devolver exactamente el dominio original de `super()`.

  Comando sugerido:
  `oo exec <db_name> -u sale_order_line_supplierinfo --test-enable --stop-after-init`
- Manual smoke tests:
  1. Crear un producto con rutas `Comprar` y `Dropship`.
  2. Crear una venta con ese producto y dejar `sale_line.route_id` vacío.
  3. Confirmar la venta y comprobar que la compra generada respeta el
     dominio original cuando la línea es dropship.
  4. Repetir con un producto no dropship para asegurar que el filtrado de
     `group_id` sigue activo.

## Assumptions
- Assumption 1
  La detección de dropship se basa en la ruta estándar
  `stock_dropshipping.route_drop_shipping`.
- Assumption 2
  El efecto deseado es restaurar el dominio original de `super()` sólo en
  dropshipping, no en cualquier producto con `route_id` vacío.

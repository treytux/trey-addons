# Spec Template

## Summary
- Objective:
  Corregir la selección de proveedor en las compras generadas desde ventas
  para que, si la línea de pedido tiene informado `supplierinfo_id`, el
  pedido de compra use siempre ese proveedor también cuando la compra nace
  desde una regla de reaprovisionamiento y la ruta no se selecciona en la
  propia línea.
- Target module:
  `sale_order_line_supplierinfo`
- Business scope:
  En la base `matedi_23feb_copy2`, al confirmar una venta del producto
  `MC_DR-3400` con el proveedor `INFORPOR S.L.` seleccionado en la línea,
  Odoo genera actualmente una compra para `ATRAMENTUM`. El comportamiento
  esperado es que la compra se cree para el proveedor elegido en la línea.

## Implementation Changes
- Backend:
  Añadir la propagación explícita de `supplierinfo_id` en
  `sale.order.line._prepare_procurement_values()` para que el proveedor
  seleccionado viaje desde el origen de la procurement, sin depender de que
  `_run_buy()` lo recupere más tarde a partir de `sale_line_id`.

  Mantener la propagación existente en `stock.move._prepare_procurement_values()`
  como compatibilidad para procurement encadenadas desde movimientos.

  Ampliar `models/stock_rule.py` para que, además de leer la línea de venta
  directa, sea capaz de resolver el `supplierinfo_id` cuando la compra viene
  de un `orderpoint` cuyo `origin` contiene referencias a pedidos de venta
  (`OP/... - SO...`). La resolución debe:
  - Priorizar la línea de venta directa si existe en la procurement.
  - Buscar líneas confirmadas de la misma compañía, producto y venta cuando
    la procurement sólo aporta `orderpoint_id` y `origin`.
  - Aplicar la sobreescritura sólo si el origen apunta de forma no ambigua a
    un único `product.supplierinfo`.

  Sincronizar `vendor_id` con `supplierinfo_id` en `sale.order.line` tanto en
  `onchange` como en `create/write` para evitar que quede un proveedor visual
  desactualizado respecto al `supplierinfo` realmente elegido.

  Añadir una regresión para el escenario donde la ruta aplicable proviene del
  producto o de la configuración estándar y `line.route_id` queda vacío,
  verificando que el `purchase.order.partner_id` coincide con
  `sale.order.line.supplierinfo_id.partner_id`.
- Frontend:
  Sin cambios funcionales en vistas. El campo `supplierinfo_id` ya existe en
  la línea de venta y sólo se corrige la coherencia con `vendor_id`.
- Security:
  Sin cambios.
- Data migration:
  Sin migración de datos. Requiere actualización del módulo para aplicar el
  cambio de lógica Python.
- Reporting:
  Sin cambios.

## Test Plan
- Installation:
  Actualizar `sale_order_line_supplierinfo` en una base de pruebas con compra
  instalada.

  Comando sugerido:
  `oo exec matedi_23feb_copy2 -u sale_order_line_supplierinfo --stop-after-init`
- Automated tests:
  Ampliar `tests/test_sale_order_line_supplierinfo.py` con una prueba de
  regresión que reproduzca:
  producto con ruta de compra aplicable desde producto/configuración,
  `line.route_id = False`, dos proveedores válidos, selección manual del
  proveedor secundario en la línea y comprobación de que la compra resultante
  usa ese proveedor.

  Añadir otra regresión orientada al caso real de `orderpoint`: construir una
  procurement de compra con `orderpoint_id`, `origin = "OP/... - SO..."` y
  proveedor por defecto en la regla de reaprovisionamiento, verificando que
  `_run_buy()` crea la compra para el `supplierinfo` marcado en la venta y no
  para el proveedor por defecto del producto/regla.

  Comando sugerido:
  `oo exec matedi_23feb_copy2 -u sale_order_line_supplierinfo --test-enable --stop-after-init`
- Manual smoke tests:
  1. En `matedi_23feb_copy2`, crear un pedido de venta con `MC_DR-3400`.
  2. Seleccionar `INFORPOR S.L.` en `supplierinfo_id`.
  3. No informar ruta en la línea.
  4. Confirmar el pedido.
  5. Verificar que el `purchase.order` generado tiene `partner_id =
     INFORPOR S.L.` y no `ATRAMENTUM`.
  6. Repetir una prueba con una línea que sí tenga ruta explícita para
     asegurar que no hay regresión en los casos ya cubiertos.

## Assumptions
- Assumption 1
  El proveedor incorrecto se debe a que el caso real entra por una compra
  lanzada desde `stock.warehouse.orderpoint`, donde el `supplierinfo_id` de
  la venta no llega a la selección de vendedor y acaba imponiéndose el
  proveedor por defecto del producto o de la regla de reaprovisionamiento.
- Assumption 2
  `INFORPOR S.L.` y `ATRAMENTUM` son dos `product.supplierinfo` válidos para
  `MC_DR-3400`, y el error no está en una restricción de datos sino en la
  selección de vendedor durante la generación de compra.

# Sale Order Confirm Lock

## Summary
- Objective:
  Impedir cambios en pedidos de venta confirmados para evitar
  inconsistencias con la logística ya generada.
- Target module:
  `sale_order_confirm_lock`
- Scope:
  En pedidos en estado `sale` no se permite:
  - añadir líneas,
  - eliminar líneas,
  - modificar `product_id`, `product_uom_qty`, `discount`, `price_unit`
    y `route_id`.

## Implementation
- Manifest:
  El módulo depende de `sale_stock` (aporta `route_id` en `sale.order.line`).
- Backend:
  Se sobrescribe `sale.order.line` para bloquear en pedidos confirmados:
  - `create` → líneas nuevas
  - `write` → cambios en campos protegidos
  - `unlink` → borrado de líneas
- Frontend:
  La vista deja `order_line` en readonly cuando el pedido está en estado
  `sale`, `done` o `cancel`.

## Flow
  Para modificar un pedido confirmado el flujo previsto es:
  - Cancelar el pedido.
  - Volver a ponerlo en borrador.
  - Realizar los cambios.
  - Confirmarlo de nuevo.

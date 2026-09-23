# Website Sale Payment Custom Autoconfirm

## Alcance

Añadir una opción por proveedor de pago custom para confirmar automáticamente
el pedido de venta al procesar el checkout.

## Comportamiento

- El campo `confirm_orders_automatically` se muestra para proveedores con
  `code = custom`.
- Si está activado, se confirma una única cotización enlazada cuando el
  importe de la transacción coincide con el total del pedido.
- La transacción continúa en estado `pending`, porque el pago puede liquidarse
  posteriormente según las condiciones acordadas.
- Si está desactivado, se conserva el comportamiento estándar de
  `payment_custom`.

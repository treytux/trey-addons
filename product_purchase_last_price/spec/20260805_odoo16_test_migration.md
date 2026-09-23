# Spec: adaptación de tests a Odoo 16

## Alcance

- Módulo: `product_purchase_last_price`
- Área: precios de compra, ventas y reporte de margen

## Cambios de migración

1. Usar `partner_id` en los proveedores de producto.
2. Sustituir `stock.picking.move_lines` por `move_ids`.
3. Sustituir `action_done()` por `button_validate()` en los tests.
4. Incluir `discount` en las dependencias del cálculo del importe de compra.
5. Crear los asistentes de stock con el contexto de Odoo 16.
6. Usar el precio neto de `purchase_discount` y conservar el inverso del coste
   almacenado en la línea de venta.
7. Copiar el último precio de compra al crear la línea de venta para evitar la
   precomputación con `product_id` vacío.
8. Sustituir el modificador XML `attrs` por `invisible` en la vista de
   producto.
9. Sustituir `decimal_precision.get_precision()` por la precisión nativa
   `digits='Product Price'`.
10. Añadir una regresión para plantillas con varias variantes y sus campos
    calculados de último precio de compra y margen.

## Criterios de aceptación

1. Las compras con descuento actualizan el último precio de compra neto.
2. Las pruebas usan la API de movimientos de stock de Odoo 16.
3. Una plantilla con varias variantes asigna `0.0` a sus campos calculados.

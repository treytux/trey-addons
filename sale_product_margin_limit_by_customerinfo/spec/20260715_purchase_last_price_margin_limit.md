# Spec: margen de cliente sobre `purchase_last_price`

## Alcance

- Módulo: `sale_product_margin_limit_by_customerinfo`
- Área funcional: validación de margen en líneas de pedido de venta

## Objetivo

Ajustar el cálculo del precio mínimo permitido para que use
`product.purchase_last_price` como base en lugar de `standard_price`.

## Implementación

1. Añadir dependencia explícita a `product_purchase_last_price`.
2. Calcular el límite de margen de `product.customerinfo` sobre
   `purchase_last_price`.
3. Mantener la prioridad de `product.customerinfo` por encima del margen
   general del producto.
4. Actualizar tests para validar el nuevo origen del coste.

## Criterios de aceptación

1. Si existe `product.customerinfo` válido, la validación usa su `margin_limit`.
2. El cálculo del precio mínimo parte de `purchase_last_price`.
3. Si no hay `product.customerinfo`, sigue aplicándose la lógica original del
   módulo base.
4. Los registros fuera de su periodo de vigencia no se consideran válidos.

## Validación propuesta

1. Crear un producto con `purchase_last_price` distinto de `standard_price`.
2. Crear una línea de `product.customerinfo` con un margen conocido.
3. Ver el campo `margin_limit` también en el tree de `product.customerinfo`.
4. Confirmar que la validación bloquea o permite según el precio calculado
   sobre `purchase_last_price`.
5. Confirmar el fallback con registros futuros, expirados y sin fechas.

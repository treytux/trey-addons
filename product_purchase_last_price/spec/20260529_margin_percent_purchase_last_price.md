# Spec: cálculo de `% Margen` sobre `purchase_last_price`

## Alcance

- Módulo: `product_purchase_last_price`
- Área funcional: exportación XLS del pivote para `sale.report.from_stock_move`

## Objetivo

Ajustar el cálculo de la columna `% Margen` para que use como base el campo
`purchase_last_price` en lugar de `price_unit`.

Fórmula objetivo:

- `% Margen = (1 - (purchase_last_price / operation_total)) * 100`

## Contexto técnico

- `sale_report_from_stock_move` añade la lógica de `% Margen` en un JS de
  extensión del pivote.
- `product_purchase_last_price` amplía el reporte con el campo
  `purchase_last_price`, por lo que debe sobreescribir la lógica de exportación
  para usar esta medida como denominador.

## Implementación

1. Añadir extensión JS del pivote en `product_purchase_last_price`.
2. Insertar columna `% Margen` únicamente cuando existan medidas
   `purchase_last_price` y `operation_total`.
3. Generar fórmula Excel con `purchase_last_price` como base y
   `operation_total` como denominador.
4. Cargar el JS en `web.assets_backend` desde el propio módulo.

## Criterios de aceptación

1. Con medidas `purchase_last_price` + `operation_total`, el XLS incluye `% Margen`
   calculado con la fórmula objetivo.
2. Si falta alguna medida, la exportación no falla y no añade `% Margen`.
3. No se afecta la exportación de otros modelos.

## Validación propuesta

1. Abrir pivote de `sale.report.from_stock_move`.
2. Activar medidas `purchase_last_price` y `operation_total`.
3. Exportar XLS y validar la fórmula resultante.
4. Repetir quitando `purchase_last_price` para confirmar que exporta sin
   columna extra ni errores.

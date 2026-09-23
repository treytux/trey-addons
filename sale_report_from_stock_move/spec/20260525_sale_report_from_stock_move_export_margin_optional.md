# Spec: exportación XLS de pivote con `% Margin` opcional

## Alcance

- Repositorio: `addons/trey-addons`
- Módulo: `sale_report_from_stock_move`
- Rango analizado: desde `8f43e50b4e7406fba37492d8aa6c5e7526ac09c3`
  hasta `HEAD`
- Commits en el módulo dentro del rango:
  - `12535c0a4` `[IMP] sale_report_from_stock_move: Added new margin`
    `percent column to the Excel`
  - `d33a4dcd4` `[IMP] sale_report_from_stock_move, allow export`
    `without fields` (autor: `Alex`, `2026-05-25`)

## Objetivo funcional

Permitir que la exportación XLS del pivote de
`sale.report.from_stock_move` no falle cuando no estén seleccionadas
las medidas `price_unit` y/o `margin`.

La columna calculada `% Margin` debe seguir apareciendo únicamente cuando
ambas medidas estén presentes.

## Contexto técnico detectado

El cambio previo (`12535c0a4`) introdujo:

- Lógica JS para añadir una columna `% Margin` al exportar el pivote.
- Validaciones bloqueantes en frontend y backend:
  - Frontend: advertencia + cancelación de descarga si faltaban medidas.
  - Backend: `UserError` en el controlador si faltaban medidas.

Ese enfoque hacía que la descarga completa del XLS quedara bloqueada en
escenarios válidos donde el usuario no necesitaba `% Margin`.

## Diseño técnico aplicado (modificaciones de `Alex`)

1. Quitar bloqueo en backend:
   - Archivo: `sale_report_from_stock_move/controllers/main.py`
   - Se elimina la validación de `technical_measures` y el `UserError`
     asociado a ausencia de `price_unit`/`margin`.

2. Mantener exportación siempre disponible en frontend:
   - Archivo: `sale_report_from_stock_move/static/src/js/pivot_extension.js`
   - Se elimina el rechazo de descarga cuando faltan medidas.
   - Si faltan `price_unit` o `margin`, se lanza exportación normal sin
     insertar `% Margin`.

3. Preservar cálculo `% Margin` cuando procede:
   - Si existen ambas medidas, se mantiene la inserción de columna,
     ajuste de encabezados y fórmulas Excel como en el diseño previo.

## Archivos afectados

- `sale_report_from_stock_move/controllers/main.py`
- `sale_report_from_stock_move/static/src/js/pivot_extension.js`

## Riesgos y compatibilidad

- Riesgo bajo: se reduce fricción de uso al no bloquear exportación.
- Compatibilidad funcional:
  - Se mantiene comportamiento previo de `% Margin` en vistas que sí
    incluyen `price_unit` y `margin`.
  - En vistas sin dichas medidas, el archivo exportado ya no falla,
    simplemente no incorpora la columna adicional.

## Validación propuesta

1. Caso con medidas completas:
   - En pivote de `sale.report.from_stock_move`, seleccionar
     `price_unit` y `margin`.
   - Exportar XLS y verificar aparición de columna `% Margin` con fórmula.

2. Caso sin una medida:
   - Quitar `margin` o `price_unit`.
   - Exportar XLS y verificar que la descarga se completa sin error.

3. Caso sin ambas medidas:
   - Exportar XLS y verificar descarga correcta sin columna `% Margin`.

## Implementación

1. Eliminar validación bloqueante en controlador HTTP de exportación.
2. Ajustar flujo JS para fallback a exportación estándar cuando no haya
   medidas suficientes para `% Margin`.
3. Mantener sin cambios el cálculo de `% Margin` para escenarios
   completos.

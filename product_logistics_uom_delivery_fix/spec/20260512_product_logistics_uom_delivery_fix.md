# Especificación incremental del módulo
# `product_logistics_uom_delivery_fix`

## Resumen
- Objetivo:
  Corregir el cálculo de `stock.move.weight` en albaranes con `delivery`
  cuando el producto define el peso en una unidad distinta a la del picking.
- Alcance:
  Incluye el override del compute de `stock.move`, la prueba automática del
  escenario gramos a kilogramos y la documentación básica del módulo.
- Fuera de alcance:
  No modifica el cálculo de paquetes, el peso de bultos ni los conectores de
  transportistas.

## Áreas impactadas
- Backend:
  Nuevos overrides de `_cal_move_weight()` en `stock.move`,
  `_cal_weight()` en `stock.picking` y `_compute_bulk_weight()` en
  `stock.picking`.
- QA:
  Nueva prueba transaccional validando la conversión `674 g x 2 = 1.348 kg`.
- Documentación:
  Nuevo `README.rst` y `static/description/index.html`.

## Diseño funcional
- Flujo:
  Al calcular el peso de cada movimiento, el sistema toma el peso del
  producto en `product.weight`, lo interpreta usando `product.weight_uom_id`
  y lo convierte a la unidad de peso del albarán antes de multiplicar por la
  cantidad.
- Regla de negocio:
  El peso agregado del albarán debe estar expresado en la unidad de peso del
  picking, evitando interpretaciones erróneas cuando el producto trabaja en
  gramos, libras u otra unidad de peso compatible.

## Diseño técnico
- Nuevo módulo:
  `addons/trey-addons/product_logistics_uom_delivery_fix`.
- Dependencias:
  `delivery`, `product_logistics_uom` y
  `stock_picking_delivery_info_computation`.
- Sobrescrituras:
  `stock.move._cal_move_weight()` recalcula `move.weight` convirtiendo desde
  `product.weight_uom_id` hacia `picking.weight_uom_id`, con fallback a la
  unidad por defecto configurada en producto.
  `stock.picking._cal_weight()` y `stock.picking._compute_bulk_weight()`
  deben cargarse después de
  `stock_picking_delivery_info_computation` para preservar la conversión de
  la unidad de peso del producto al peso del albarán y al peso de envío.

## Validación prevista
- Instalar el módulo.
- Crear un producto con `weight = 674` y `weight_uom_id = gr`.
- Crear un picking con unidad de peso en kg.
- Verificar que el movimiento y el picking muestran `0.674 kg` por unidad y
  `1.348 kg` para dos unidades.

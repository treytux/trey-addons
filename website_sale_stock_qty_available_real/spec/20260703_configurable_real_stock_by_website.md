# Criterio de stock configurable por sitio web

## 1. Contexto
- Modulo: `website_sale_stock_qty_available_real`
- Fecha: 2026-07-03

## 2. Objetivo
- Permitir que el modulo este instalado en bases multi-sitio sin forzar el
  mismo criterio de stock en todas las tiendas online.
- Permitir elegir por sitio web el criterio de stock que debe usar
  `website_sale_stock`.
- Soportar el stock pronosticado para sitios web que vendan contra
  previsiones, como Gote.

## 3. Alcance
### Incluido
- Sustituir la opcion booleana por un selector por `website`.
- Exponer el selector en Ajustes del sitio web.
- Permitir estos modos:
  - Stock disponible: comportamiento estandar de Odoo, basado en `free_qty`.
  - Stock real: usar `qty_available_real`.
  - Stock pronosticado: usar `virtual_available`.
- Condicionar ficha de producto, cambios de variante, carrito y validacion de
  pago por website.
- Mantener el comportamiento estandar de Odoo como valor por defecto.
- Anadir pruebas de regresion multi-website.

### Excluido
- Cambiar el calculo de `qty_available_real`.
- Cambiar textos o reglas de `website_sale_stock` fuera del modulo.
- Vincular el comportamiento a temas visuales.

## 4. Diseno tecnico
- Se anade `website_sale_stock_qty_mode` en `website`, con estos valores:
  - `available`: stock disponible, valor por defecto.
  - `real`: stock real.
  - `forecasted`: stock pronosticado.
- Se anade un campo relacionado editable en `res.config.settings`.
- El campo booleano previo `website_sale_stock_use_qty_available_real` debe
  eliminarse si no hay despliegues que dependan de el, o conservarse solo como
  compatibilidad tecnica si ya existe en alguna base actualizada.
- `product.template._get_combination_info()` activa el contexto de stock del
  website actual solo si el modo no es `available`.
- `product.product._compute_quantities_dict()` ajusta `free_qty` y
  `virtual_available` segun el modo:
  - `available`: sin cambios, Odoo calcula `free_qty`.
  - `real`: `free_qty` y `virtual_available` toman `qty_available_real`.
  - `forecasted`: `free_qty` toma el `virtual_available` original.
- `sale.order` activa el mismo contexto solo para pedidos de websites con modo
  distinto a `available`.
- La validacion final de pago usa el metodo correcto de Odoo 16,
  `shop_payment_transaction`.

## 5. Validacion esperada
- Un website en modo `available` debe mantener el calculo estandar de Odoo.
- Un website en modo `real` debe mostrar y validar contra
  `qty_available_real`.
- Un website en modo `forecasted` debe mostrar y validar contra
  `virtual_available`.
- El modo debe poder cambiarse desde ajustes de website.
- Gote podra usar modo `forecasted` sin afectar a webs configuradas en modo
  `real` o `available`.

## 6. Riesgos
- En flujos sin `website_id` explicito se conserva el comportamiento estandar
  para evitar afectar procesos backend.
- Es necesario actualizar el modulo por cambiar la configuracion almacenada en
  `website`.
- Si ya se actualizo una base con el booleano anterior, conviene migrar sus
  valores al nuevo selector: `True` debe equivaler a `real` y `False` a
  `available`.

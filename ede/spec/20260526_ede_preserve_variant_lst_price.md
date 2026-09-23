# Especificación incremental del módulo
# `ede` — Preservar `lst_price` al actualizar precios EDE en variantes

## Resumen
- Objetivo:
  Corregir la actualización de precios EDE para que, al modificar
  `product.supplierinfo.price`, se conserve correctamente el precio de venta
  (`lst_price`) tanto si la línea de proveedor apunta a una variante
  (`product.product`) como si apunta a la plantilla (`product.template`).
- Alcance:
  - Ajuste en `models/product_template.py` dentro de `job_ede_update_price`.
  - Conservación del `lst_price` previo usando el registro correcto según el
    tipo de referencia en `supplier_info`.
- Fuera de alcance:
  - No se modifican cron, colas, payloads EDE ni la lógica de simulación.
  - No se alteran reglas de cálculo de margen o de recomputación fuera del flujo
    actual de actualización de coste.

## Áreas impactadas
- Backend:
  - `models/product_template.py`
    - Ajuste en la lectura de `lst_price_previous`.
    - Ajuste en la restauración de `lst_price` tras escribir el nuevo coste.
- Datos/negocio:
  - Evita que una actualización de coste EDE afecte por error al precio de venta
    de variantes cuando `supplier_info.product_id` está informado.

## Problema detectado
- El flujo original asumía que la línea de proveedor siempre se restauraba sobre
  `supplier_info.product_tmpl_id.list_price`.
- En escenarios donde la línea de proveedor está asociada a una variante
  concreta (`supplier_info.product_id`), el precio de venta relevante es
  `product.product.lst_price`.
- Como consecuencia, al actualizar `supplier_info.price` podía producirse una
  recomputación no deseada del precio de venta de la variante o restaurarse el
  valor en el registro incorrecto.

## Diseño funcional
- Flujo esperado:
  1. El job obtiene el precio EDE calculado para la línea de proveedor.
  2. Si el coste no cambia, no se toca ningún precio de venta.
  3. Si el coste cambia:
     - Se guarda primero el `lst_price` actual del registro afectado.
     - Se actualiza `supplier_info.price`.
     - Se reescribe el `lst_price` anterior sobre el mismo nivel de dato:
       variante si existe `product_id`, plantilla en caso contrario.

## Diseño técnico
- Ubicación:
  - [addons/trey-addons/ede/models/product_template.py](/var/lib/odoo/odoo_12/addons/trey-addons/ede/models/product_template.py)
- Cambios aplicados en `job_ede_update_price(self)`:
  - Mover la captura de `lst_price_previous` para que solo se haga cuando el
    coste realmente cambia.
  - Resolver el precio previo con esta lógica:
    - `supplier_info.product_id.lst_price` si existe variante.
    - `supplier_info.product_tmpl_id.list_price` en caso contrario.
  - Restaurar el precio con `sudo()` sobre el mismo registro origen:
    - `supplier_info.product_id.sudo().lst_price = lst_price_previous`
    - o `supplier_info.product_tmpl_id.sudo().lst_price = lst_price_previous`

## Riesgos y consideraciones
- Si existen automatismos adicionales sobre `lst_price` a nivel de variante,
  este cambio preserva el valor actual pero no evita side effects de módulos
  externos que reaccionen a la escritura.
- La lógica sigue dependiendo de que `supplier_info` esté correctamente ligado a
  variante o plantilla; no cambia la calidad del dato maestro.

## Validación prevista
- Manual:
  1. Crear un producto con variante y línea de proveedor EDE enlazada a
     `product_id`.
  2. Asignar un `lst_price` específico en la variante.
  3. Ejecutar `job_ede_update_price()` con una respuesta EDE que cambie el
     coste.
  4. Verificar que `supplierinfo.price` cambia y `product.product.lst_price`
     permanece igual.
  5. Repetir con una línea de proveedor ligada solo a `product_tmpl_id` y
     comprobar que se conserva `product.template.list_price`.
- Automática:
  - Añadir test que cubra ambos escenarios:
    - `supplier_info` con `product_id`
    - `supplier_info` solo con `product_tmpl_id`

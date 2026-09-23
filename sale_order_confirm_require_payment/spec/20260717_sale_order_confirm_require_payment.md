# Spec

## Summary
- Objective:
  Impedir la confirmación de un pedido de venta cuando no se han informado los
  campos *Condiciones de pago* (`payment_term_id`) y *Modo de pago*
  (`payment_mode_id`), sin bloquear el guardado del presupuesto en borrador.
- Target module:
  `sale_order_confirm_require_payment`
- Business scope:
  En el formulario de `sale.order` (caso real S08675, cliente
  "Círculo Textil") es posible confirmar pedidos con esos dos campos vacíos.
  Se quiere forzar que ambos estén rellenos en el momento de la confirmación
  para garantizar la coherencia de la información de cobro.

## Implementation Changes
- Backend:
  Sobreescribir `action_confirm()` en un modelo que hereda `sale.order`. Antes
  de llamar a `super()`, recorrer el recordset y acumular los campos que falten
  (`payment_term_id`, `payment_mode_id`). Si hay alguno vacío, lanzar un
  `ValidationError` con un único mensaje que liste los campos que faltan. El
  mensaje se escribe en inglés en el código, envuelto en `_()`, y se traduce al
  español en `i18n/es.po`.
- Frontend:
  Sin cambios en vistas. Los campos `payment_term_id` y `payment_mode_id` ya se
  muestran en el formulario estándar (este último lo añade
  `account_payment_sale`).
- Security:
  Sin cambios. No se añaden modelos ni reglas de acceso.
- Data migration:
  Sin migración de datos. Requiere instalar el módulo para aplicar la lógica.
- Reporting:
  Sin cambios.

## Test Plan
- Installation:
  Instalar el módulo en una base de pruebas que tenga `account_payment_sale`
  disponible (se instala automáticamente con `sale` +
  `account_payment_partner`).

  Comando sugerido:
  `./odoo-bin -c odoo-server.conf -d <db> -i sale_order_confirm_require_payment --stop-after-init`
- Automated tests:
  `tests/test_sale_order_confirm_require_payment.py` (`TransactionCase`) con
  cuatro casos:
  1. Pedido sin `payment_term_id` ni `payment_mode_id` → `action_confirm()`
     lanza `ValidationError` y el estado no pasa a `sale`.
  2. Pedido solo con `payment_term_id` → sigue lanzando `ValidationError`.
  3. Pedido solo con `payment_mode_id` → sigue lanzando `ValidationError`.
  4. Pedido con ambos campos informados → `action_confirm()` confirma y el
     estado pasa a `sale`.

  Comando sugerido:
  `./odoo-bin -c odoo-server.conf -d <db> -i sale_order_confirm_require_payment --test-enable --stop-after-init`
- Manual smoke tests:
  1. Crear un presupuesto con un cliente y una línea de producto.
  2. Dejar vacíos *Condiciones de pago* y *Modo de pago* y guardar → guarda sin
     error.
  3. Pulsar *Confirmar* → aparece el error y el pedido no se confirma.
  4. Rellenar ambos campos y confirmar → el pedido pasa a *Pedido de venta*.

## Assumptions
- Assumption 1
  El campo `payment_mode_id` proviene de `account_payment_sale` (repo OCA
  bank-payment) y está siempre disponible gracias a la dependencia declarada en
  el manifest.
- Assumption 2
  La validación en la confirmación (y no marcar los campos como `required` en
  la vista o el modelo) es el comportamiento deseado, para no bloquear la fase
  de presupuesto ni los flujos que crean pedidos por código.

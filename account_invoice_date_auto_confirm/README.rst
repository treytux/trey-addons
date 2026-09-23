.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================
Account Invoice Date Auto Confirm
=================================

Este módulo crea una acción planificada que revisa las facturas en estado
borrador y confirma automáticamente aquellas cuya fecha de factura coincide
con el día de ejecución de la acción planificada.

**Tabla de contenidos**

.. contents::
   :local:

Características
~~~~~~~~~~~~~~~

- Crea una acción planificada ``Auto Confirm Draft Invoices by Date`` que se
  ejecuta cada 12 horas.
- Busca facturas en estado borrador cuya ``invoice_date`` coincida con la
  fecha de ejecución y las confirma mediante ``action_post()``.
- El método ``_cron_auto_confirm_draft_invoices`` admite el parámetro
  ``confirm_past_date`` (``False`` por defecto). Si se pasa ``True``,
  confirma también las facturas con ``invoice_date`` igual o anterior a la
  fecha de ejecución.
- Para activar ``confirm_past_date``, entra en Ajustes → Técnico →
  Automatización → Acciones planificadas, abre ``Auto Confirm Draft
  Invoices by Date`` y cambia el campo ``Código`` de::

      model._cron_auto_confirm_draft_invoices()

  a::

      model._cron_auto_confirm_draft_invoices(confirm_past_date=True)

  Para volver al comportamiento por defecto, deja el campo ``Código`` como
  ``model._cron_auto_confirm_draft_invoices()``.
- Si una factura no puede confirmarse, el error se registra en el log del
  servidor y el resto del lote continúa procesándose.

Instalación
~~~~~~~~~~~

- Copia la carpeta ``account_invoice_date_auto_confirm`` en el directorio de
  addons de tu instalación de Odoo.
- Reinicia el servidor de Odoo.
- Ve a la interfaz de Odoo, activa el modo desarrollador y actualiza la
  lista de aplicaciones.
- Instala el módulo ``Account Invoice Date Auto Confirm``.

Autor
~~~~~

- `Trey Kilobytes de Soluciones SL <https://www.trey.es>`__

====================================
Contract invoice date after invoiced
====================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

* Evita que la acción programada ``cron_recurring_create_invoice`` de contratos
  falle cuando ``date_start`` de la línea es posterior a ``last_date_invoiced``.
* Mantiene activas el resto de controles de fechas.

**Tabla de contenidos**

.. contents::
   :local:

Autor
~~~~~

* `Trey <https://www.trey.es>`__:

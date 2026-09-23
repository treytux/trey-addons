Stock Orderpoint Period Qty
===========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Extiende las reglas estándar de reabastecimiento de Odoo para calcular la
demanda media mensual a partir del histórico de movimientos.

Funcionalidad
=============

Este módulo reutiliza las cantidades estándar de Odoo 16, incluyendo
``qty_forecast`` y ``qty_to_order``. Añade únicamente la configuración del
período histórico y calcula la cantidad a pedir usando los movimientos del
período seleccionado.

Los períodos disponibles son:

* Anual: últimos 12 meses.
* Semestral: últimos 6 meses.
* Trimestral: últimos 3 meses.
* Mensual: último mes.

La cantidad media mensual se obtiene restando las entradas consideradas
devoluciones a las salidas. La cantidad resultante se compara con la
cantidad prevista estándar y se redondea según el múltiplo de compra de la
regla de reabastecimiento.

Configuración
=============

#. Ir a **Ajustes > Opciones generales > Inventario**.
#. Seleccionar el período de cálculo para los puntos de pedido.
#. Configurar las reglas estándar de reabastecimiento de Odoo con su ruta,
   múltiplo de compra y compañía.

El planificador estándar de Odoo calcula ``qty_to_order`` y genera el
aprovisionamiento según la ruta configurada, por ejemplo una solicitud de
presupuesto para la ruta de compra.

Créditos
========

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

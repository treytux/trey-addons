============================
Sale UTM Medium Smartbuttons
============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Añade smartbuttons a los Medios UTM (utm.medium) para acceder rápidamente a:

* Presupuestos relacionados
* Facturas y sus ingresos generados
* Leads/Oportunidades

Este módulo replica la funcionalidad existente en ``utm.campaign`` para ``utm.medium``,
permitiendo un análisis similar de marketing pero a nivel de medio de marketing.

**Tabla de contenidos**

.. contents::
   :local:

Funcionalidad
=============

Este módulo hereda el modelo ``utm.medium`` y añade:

Campos computados
~~~~~~~~~~~~~~~~~

* ``quotation_count``: Número de presupuestos relacionados con el medio
* ``invoiced_amount``: Ingresos totales generados por facturas del medio
* ``crm_lead_count``: Número de leads/oportunidades relacionados con el medio

Smartbuttons en la vista formulario
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Revenues**: Muestra los ingresos y al hacer clic navega a las facturas filtradas
* **Quotations**: Muestra el contador y al hacer clic navega a los presupuestos filtrados
* **Leads/Opportunities**: Muestra el contador y al hacer clic navega a los leads u oportunidades

Uso
===

#. Ir a *Marketing > UTM Tracking > Mediums*.
#. Abrir cualquier medio existente.
#. Los smartbuttons aparecerán en la parte superior del formulario mostrando las métricas.
#. Hacer clic en cualquier botón para ver los registros relacionados.

Créditos
========

Autor
~~~~~

* `Trey <https://www.trey.es>`__:

=====================================
Stock picking hide number of packages
=====================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Se añaden como dependencias los módulos delivery_package_number y stock_picking_delivery_info_computation.
    * Los dos módulos definen el campo number_of_packages en el mismo modelo y lo muestran en la vista formulario.
    * Oculta el campo number_of_packages de la vista formulario de los albaranes.
    * El campo que se oculta es el que introduce el módulo stock_picking_delivery_info_computation.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:

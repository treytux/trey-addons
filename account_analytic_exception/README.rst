==========================
Account analytic exception
==========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|
    Este módulo crea automáticamente una actividad de advertencia cuando se valida una factura (action_post) y una o más de sus líneas no tienen asignada una distribución analítica.
    Su objetivo es asegurar que todas las líneas de factura estén correctamente vinculadas a cuentas analíticas, facilitando así un mejor control y análisis financiero.
    La actividad se asigna al usuario responsable para que revise y corrija la factura si es necesario.
    Además, añade la posibilidad de bloquear la validación de los contratos de cliente cuando sus líneas
    no cuentan con cuenta/distribución analítica.


**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:

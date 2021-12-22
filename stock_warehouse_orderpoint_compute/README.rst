.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock warehouse orderpoint compute
==================================

Acción planificada para modificar el cálculo de los campos "Cantidad mínima" y "Cantidad máxima" de las reglas de abastecimiento de los productos en base a las cantidades compradas y vendidas junto con los nuevos campos añadidos en los siguientes modelos:

    - En la compañía:
        - Plazo de entrega.
        - Periodo.

    - En el proveedor:
        - Plazo de entrega.
        - Factor de stock mínimo.
        - Factor de stock máximo.

NOTA:
Para que las operaciones de actualización de reglas de abastecimiento se realicen deben estar creadas previamente.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

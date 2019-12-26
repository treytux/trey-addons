.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Procurement compute write make po errors
====

Si ocurre un error en segundo plano en la ejecución de los abastecimientos
cuando va a crearse un pedido de compra, en lugar de pararse la ejecución (que
es el comportamiento por defecto) se hace lo siguiente en el abastecimiento
que ha dado el error:

    - Se escribe el texto del error en el muro para que el usuario tenga
    información de lo que ha ocurrido.

    - Se pasa el abastecimiento a estado "Excepción" para que el usuario lo
    revise, corrija el error y vuelva a ejecutarlo.

De esta manera el resto de abastecimientos se ejecutarán aunque uno de ellos
falle.

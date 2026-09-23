=======================
Sale Order Confirm Lock
=======================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Impide modificar las líneas de un pedido de venta una vez confirmado.

Cuando el pedido está en estado confirmado:

- No permite añadir líneas nuevas.
- No permite eliminar líneas existentes.
- No permite modificar producto, cantidad, descuento, precio unitario ni
  ruta logística.

El flujo previsto para cambiar un pedido confirmado es:

- Cancelar el pedido.
- Volver a ponerlo en borrador.
- Realizar los cambios.
- Confirmarlo de nuevo.

El módulo aplica el bloqueo tanto en vista como en backend para evitar
modificaciones desde interfaz, RPC o automatizaciones.

**Tabla de contenidos**

.. contents::
   :local:

Autor
~~~~~

* `Trey <https://www.trey.es>`__

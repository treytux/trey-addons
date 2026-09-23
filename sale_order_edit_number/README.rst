.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
Sale order edit number
======================

Añade el campo "Force number" en el formulario del pedido de venta.

* El campo solo es visible para los usuarios del grupo "Sale order force
  number" y solo cuando el pedido está en borrador.
* Si se rellena, al crear o modificar el pedido el número del pedido
  (campo 'name') se sustituye por ese valor.
* Se valida que no exista otro pedido con el mismo número para evitar
  duplicados.
* No se puede forzar el número sobre varios pedidos a la vez.

* Añade un test para comprobar el estado.

Autor
~~~~~

* `Trey Kilobytes de Soluciones SL <https://www.trey.es>`__

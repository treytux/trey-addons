.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock rule purchase fix
=======================

Este módulo soluciona un error detectado en cualquier combinación de dos rutas en un mismo producto cuando una de ellas es "Comprar".

Por definición, para que funcione la ruta "Comprar" se necesita definir en el producto un proveedor y una regla de abastecimiento.

El problema es que, luego se ejecutará el planificador y se comprará el doble de mercancía de la necesaria.

Veamos un ejemplo:

  - Tenemos un producto con las rutas "Comprar" y "Bajo pedido" y una regla de abastecimiento con una cantidad mínima y una cantidad máxima de 0 unidades.
  Cuando se realiza una venta de 10 unidades y se confirma se generará un pedido de compra con 10 unidades.
  Después, cuando se ejecute el planificador y se lancen las reglas de abastecimiento, como el stock virtual es -10 y se necesitan como mínimo 0, se modificará la línea del presupuesto de compra incrementándose en 10 unidades, por lo que al final estaremos pidiendo al proveedor 20 unidades cuando realmente necesitamos sólo 10.

  - Lo mismo ocurre si tenemos un producto con las rutas "Comprar" y "Bajo pedido + bajo existencias".

Con este módulo instalado este problema queda solventado.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

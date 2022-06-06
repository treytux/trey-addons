.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock deposit suppplier
=======================

Este módulo se usa para gestionar mercancía del proveedor en depósitos, es decir, se compran al proveedor x unidades pero, aunque están pagadas y son suyas, no las reciben todas de una vez pero, si consultan el stock valorado, necesitan que estas unidades se tengan en cuenta, ya que son suyas.

De forma automática se crean:

    - Un nuevo tipo de operación "Depósito proveedores" con un nuevo campo booleano "¿Es depósito de proveedor?", que esta marcado por defecto sólo para este tipo de operación.

    - Una nueva ubicación "Depósito de proveedores".


Configuración
=============

- Crear un presupuesto de compra y seleccionar en el campo "Entregar a" el tipo de operación "Depósito de proveedor".

- Confirmar el presupuesto de compra.

Automáticamente se crearán los dos albaranes correspondientes:

    - Uno de "Proveedores" a "Depósito de proveedores".

    - Otro de "Depósito de proveedores" a "Stock", que se quedará esperando otra operación hasta que el primero esté realizado.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

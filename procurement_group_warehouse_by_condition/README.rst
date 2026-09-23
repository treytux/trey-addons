.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Procurement group warehouse by condition
========================================

Este módulo permite enviar mercancía a los clientes desde distintos almacenes dependiendo de las reglas de condiciones definidas por el usuario. Para ello el usuario en el pedido de venta debe seleccionar un nuevo almacén definido para tal fin: "Almacén según condiciones". Cuando se confirme el pedido de venta, el sistema consultará el listado de reglas de condiciones y obtendrá para cada línea de pedido el almacén desde el que enviará la mercancía.


Configuración
-------------

- Por defecto se crea un nuevo almacén "Almacén según condiciones" para la compañía principal con el campo "¿Es almacén por condiciones?" marcado. En entornos multicompañía debe crearse un almacén de este tipo para cada compañía.

- Desde el menú "Inventario/Configuración/Abastecimientos de almacén según condiciones" debe crear líneas con los siguientes campos:
	- Secuencia.
	- Aplicar en, para aplicar la condición a una de las siguientes opciones:
		- Todos los productos
		- Categoría de producto.
		- Plantilla de producto.
		- Variante de producto.
	- Signo (>, >=, =, <, <=).
	- Cantidad.
	- Códigos postales de la dirección de entrega del cliente.
	- Almacén principal desde el que se surte la mercancía.
	- Almacenes alternativos: lista de almacenes ordenados por prioridad de los cuales se usará uno para enviar la mercancía si no hay stock en el almacén principal definido.

El sistema irá comprobando las condiciones por orden de secuencia hasta que se cumpla una de ellas para decidir desde qué almacén se enviará la mercancía para cada línea del pedido de venta. Se añadirá una nota por cada línea de pedido en el muro del pedido de venta para indicar la condición que se ha aplicado a cada una de ellas.
Si no hay stock en el almacén definido como principal ni en los almacenes alternativos, se usará el almacén definido como principal.
Si no se encuentra ninguna condición que se cumpla, se enviará la mercancía desde el almacén principal de la compañía y se creará una nota en el muro del pedido y una planificación al usuario que corresponda.
Si hay algún error se dejará una nota en el muro del pedido y se creará una planificación al usuario que corresponda.

- En Compañía y Ajustes/Opciones Generales/Compras:

	- Usuario para avisos de almacén por condiciones: usuario al que se notificarán los errores cuando se apliquen las líneas de condición para el almacén de grupo de abastecimiento por condición.

	Si se deja vacío, se notificará al comercial del pedido de venta y, en el caso de que no tenga ninguno asociado, al usuario que haya confirmado el pedido.

Uso
---
- Al crear un pedido de venta, si se desea aplicar un almacén según condiciones, el usuario debe asignar en el campo "Almacén" el almacén "Almacén según condiciones" y, posteriormente, añadir las líneas al pedido.

- Cuando se confirma el pedido de venta, el sistema consultará el listado de reglas de condiciones y obtendrá para cada línea de pedido el almacén desde el que enviará la mercancía y se creará una nota en el muro del pedido de venta para indicar la condición que se ha aplicado a cada una de ellas. También se creará un albarán de salida para enviar la mercancía desde el almacén que corresponda.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

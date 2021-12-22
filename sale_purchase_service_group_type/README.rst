.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================================
Sale purchase service group type
================================

Cuando marcamos un producto como servicio y lo configuramos para que haga un pedido de compra por defecto, si hay una
solicitud de compra para ese proveedor y tiene una línea con ese artículo, suma a la cantidad solicitada la que proviene
del pedido de venta.
Este módulo podemos cambia este comportamiento agregando un campo tipo con el que controlamos como deben de hacerse
estas agrupaciones.

Configuración
=============

* Crear el proveedor de transporte y su producto servicio asociado.
* A nivel de producto tenemos que configurar:
    * Crear registro de proveedor con las condiciones de compra del mismo.
    * Marcar el producto como "comprar automáticamente".
    * Seleccionar el tipo de agrupación de solicitudes de compra.
        * Vacío: Comportamiento normal. Si hay una solicitud de compra para ese proveedor y ese producto, usara dicha
          solicitud y agrupara las cantidades.
        * Sin agrupar: Creara una nueva solicitud de pedido y no agrupara cantidades.
        * Por fecha: Teniendo el dia de agrupación y los dias de liquidación, agrupara o creara solicitudes nuevas.

Uso
====

Al crear un pedido de venta, seleccionamos el método de envío. En base a la configuración del producto nos creara un
solicitud de compra o bien agregara a una solicitud existente ese registro.


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

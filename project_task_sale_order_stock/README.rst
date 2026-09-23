.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================
Project task sale order stock
=============================

Permite crear pedidos de venta desde tareas usando partes de horas y los
materiales añadidos en la propia tarea, con trazabilidad sobre lo ya
traspasado a venta y soporte para flujos con stock.

Funcionalidad
~~~~~~~~~~~~~

El módulo amplía las tareas de proyecto para permitir:

* Crear pedidos de venta desde una tarea.
* Incluir en el pedido las horas pendientes de facturar desde partes de
  horas.
* Incluir en el pedido los materiales pendientes registrados en la tarea.
* Mantener trazabilidad entre horas, materiales y líneas de pedido de
  venta.
* Evitar que una misma hora o material se vuelva a traspasar a venta.
* Gestionar flujos automáticos de pedido, albarán y facturación desde el
  asistente de creación de tareas.

Pedido de venta desde la tarea
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La tarea incorpora una acción para crear un pedido de venta a partir de la
información pendiente de vender.

El asistente de creación de pedido:

* Recoge los partes de horas que todavía no se han pasado a venta.
* Recoge los materiales de tarea con cantidad positiva que todavía no se
  han pasado a venta.
* Genera las líneas de pedido correspondientes.
* Rellena el campo `sale_order_line_id` tanto en horas como en materiales
  para dejar trazabilidad.

Gracias a esta trazabilidad:

* Se sabe qué registros ya han sido vendidos.
* Se evita que vuelvan a incluirse en pedidos posteriores.
* Se pueden crear nuevos pedidos desde la misma tarea sólo con lo que siga
  pendiente.

Integración con stock
~~~~~~~~~~~~~~~~~~~~~

Cuando la venta incluye materiales, el flujo se integra con `sale_stock`:

* El pedido de venta puede tomar el almacén a partir de la ubicación de
  destino de la tarea.
* La tarea muestra accesos a pedidos de venta, albaranes y movimientos de
  stock relacionados.
* El pedido confirmado sigue el flujo estándar de Odoo para generar el
  albarán cuando corresponde.

Asistente "Crear tarea"
~~~~~~~~~~~~~~~~~~~~~~~

El módulo amplía el asistente de creación de tareas para que pueda lanzar
automáticamente el flujo comercial y logístico.

Desde este asistente se puede:

* Crear la tarea con horas y materiales.
* Informar una ubicación de destino.
* Informar lotes en las líneas de materiales cuando proceda.

Al confirmar el asistente:

* Se crea la tarea.
* Se crea automáticamente el pedido de venta asociado.
* Se confirma el pedido de venta.
* Si procede, se genera y procesa el albarán.
* Se intenta crear la factura del pedido.

Gestión de almacén y ubicación
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La ubicación de destino informada en la tarea o en el asistente se utiliza
para localizar el almacén correspondiente y asignarlo al pedido de venta.

Esto permite que el flujo de stock se apoye en el almacén correcto cuando
la venta genera operaciones logísticas.

Lotes y validación de stock
~~~~~~~~~~~~~~~~~~~~~~~~~~~

En el asistente de creación de tarea:

* El lote sólo se puede seleccionar para el producto de su línea.
* Antes de continuar se comprueba que existe stock suficiente.
* Si el usuario informa un lote, también se valida la disponibilidad de ese
  lote.
* Si no hay stock suficiente, el sistema muestra un aviso y no continúa con
  el flujo.

Cuando el pedido confirmado genera albarán:

* Se reservan las cantidades.
* Se asignan los lotes indicados a las líneas de stock que corresponden.
* El albarán se valida y se transfiere automáticamente.

Facturación automática
~~~~~~~~~~~~~~~~~~~~~~

Después de crear y confirmar el pedido de venta desde el asistente de
creación de tarea, el módulo intenta facturarlo automáticamente.

Si la factura no puede generarse:

* No se interrumpe el resto del proceso.
* Se muestra un aviso al usuario.
* La tarea, el pedido y el posible albarán permanecen creados y
  procesados.

Interfaz de usuario
~~~~~~~~~~~~~~~~~~~

La funcionalidad añade o amplía elementos visibles en la tarea:

* Botón para crear pedido de venta.
* Ubicación de destino.
* Contadores y accesos a pedidos, albaranes y movimientos.
* Campo `sale_order_line_id` en horas, en sólo lectura.
* Campo `sale_order_line_id` en materiales, en sólo lectura.

Casos de uso principales
~~~~~~~~~~~~~~~~~~~~~~~~

El módulo está orientado a escenarios como:

* Facturar horas y materiales consumidos en una intervención o proyecto.
* Crear la tarea y lanzar en un solo paso el pedido, la entrega y la
  factura cuando exista stock suficiente.
* Mantener control de qué consumos ya han pasado a venta y cuáles siguen
  pendientes.

Autor
~~~~~

* `Trey Kilobytes de Soluciones SL <https://www.trey.es>`__

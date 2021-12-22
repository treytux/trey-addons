.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock deposit
=============

Creación de depósito
--------------------

Permite crear una ubicación depósito mediante el asistente "Crear depósito" alojado en el menú Inventario/Configuración/Crear depósito.

De forma automática el sistema crea:

    - La ubicación depósito de tipo interno.

    - Las reglas de stock asociadas.

Antes de crear el depósito hay que rellenar el campo "Depósito padre" del almacén correspondiente con una ubicación de tipo vista.

Una vez creado el depósito hay que configurar las direcciones de envío de los clientes que van a trabajar como depósitos seleccionando en el campo "Ubicación de cliente" la ubicación del depósito que se acaba de crear.

De esta manera, cuando se crea un pedido de venta con una dirección de envío configurada como depósito al confirmarlo se genera un albarán interno desde la ubicación de existencias del almacén a la ubicación depósito.

Si no se modifica la dirección de envío del cliente, los pedidos de venta siguen funcionando de la forma habitual.


Asistente para mover stock
--------------------------

Mediante el asistente "Mover stock depósito" alojado en el menú Inventario/Operaciones se pueden realizar distintas operaciones según el tipo indicado en cada línea.

El asistente solicita al usuario:

    - La dirección de envío del depósito.

    - La ubicación del depósito.

    - El almacén al que pertenece el depósito.

    - Opción de precio:

        - "Precio del pedido de venta (FIFO)": el precio de la línea de factura se obtiene de la línea del pedido de venta y, si no hay línea de venta asociada, se asigna el precio de venta de la ficha de producto con la tarifa correspondiente aplicada.

        - "Último precio": el precio de la línea de factura se obtiene de la última línea de pedido de venta confirmada para ese cliente y, si no hay ninguna línea de venta, se asigna el precio de venta de la ficha de producto con la tarifa correspondiente aplicada.

    - Crear factura: si se selecciona esta opción, se generará la factura correspondiente a los movimientos realizados. Si no está seleccionada, debe generarla manualmente más tarde desde el pedido de cliente.

    - Líneas de los movimientos que se desean realizar. Estos son los tipos disponibles que se pueden seleccionar:

        - "Venta" (depósito -> clientes): genera un nuevo pedido de venta con las cantidades a mover desde la ubicación depósito a la ubicación "Clientes", con su albarán interno asociado transferido. Si el campo "Crear factura" del asistente está marcado también se crea la factura correspondiente.

        - "Inventario": genera un nuevo pedido de venta con la diferencia entre las cantidades que se movieron al depósito y las que el depósito dice tener, se confirma y se generan dos albaranes internos que se transfieren de forma automática: uno que va del depósito del cliente a "Clientes" y otro que va de "Clientes" a "Ajustes de inventario". Si el campo "Crear factura" del asistente está marcado también se crea la factura correspondiente.

        - "Devolución a cliente" (clientes -> depósito): genera un nuevo albarán interno desde la ubicación "Clientes" a la ubicación depósito cuyo movimiento de stock está enlazado con el pedido de venta original y lo transfiere. Si el campo "Crear factura" del asistente está marcado también se crea la factura correspondiente.

        - "Devolución a central" (depósito -> existencias): genera un nuevo albarán interno desde la ubicación depósito a la ubicación "Existencias" y se transfiere. No genera factura en ningún caso.

        - "Devolución clientes -> depósito -> existencias" (clientes -> depósito -> existencias): realiza las dos operaciones anteriores en un solo paso:
            - "Devolución a cliente" (clientes -> depósito).
            y
            - "Devolución a central" (depósito -> existencias).

Pedidos de venta manuales
-------------------------
Se han añadido dos nuevos campos booleanos al pedido de venta que el usuario también puede usar para crear pedidos manuales sin usar el asistente (obviamente se moverá la cantidad indicada en las líneas del pedido):

    - "¿Es venta depósito?": al confirmar el pedido de venta, crea automáticamente un albarán interno desde la ubicación depósito a la ubicación "Clientes" y lo transfiere.
    El usuario deberá crear la factura manualmente desde el pedido, ya que, no se genera de forma automática.

    - "¿Es inventario depósito?": al confirmar el pedido de venta, crea automáticamente dos albaranes, uno que va del depósito del cliente a "Clientes" y otro que va de "Clientes" a "Ajustes de inventario" y los transfiere.
    El usuario deberá crear la factura manualmente desde el pedido, ya que, no se genera de forma automática.

IMPORTANTE: si se crean pedidos de forma manual usando estos campos el sistema no avisará en caso de que no haya stock y forzará la transferencia de material.


Configuración
-------------

- Para que los usuarios encargados puedan ver la configuración del almacén y añadir la ubicación padre para los depósitos deben pertenecer al grupo "Gestionar flujos de inventario push y pull".

- Para que los usuarios puedan ver el campo dirección de envío en los pedidos de venta deben pertenecer al grupo "Direcciones en los pedidos de venta".


Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Stock deposit
=============

Permite crear una ubicación depósito mediante el asistente "Crear depósito"
alojado en el menú Inventario/Configuración/Crear depósito.

De forma automática el sistema crea:

    - La ubicación depósito de tipo interno.

    - Las reglas de stock asociadas.

Antes de crear el depósito hay que rellenar el campo "Depósito padre" del
almacén correspondiente con una ubicación de tipo vista.

Una vez creado el depósito hay que configurar las direcciones de envío de los
clientes que van a trabajar como depósitos seleccionando en el campo
"Ubicación de cliente" la ubicación del depósito que se acaba de crear.

De esta manera, cuando se crea un pedido de venta con una dirección de envío
configurada como depósito al confirmarlo se genera un albarán interno desde
la ubicación de existencias del almacén a la ubicación depósito.

Si no se modifica la dirección de envío del cliente, los pedidos de venta
siguen funcionando de la forma habitual.


También permite realizar movimientos de stock de un depósito a un cliente
mediante el asistente "Mover stock depósito" alojado en el menú
Inventario/Configuración/Mover stock depósito.

El asistente solicita al usuario:

    - La dirección de envío del depósito.

    - La ubicación del depósito.

    - El almacén al que pertenece el depósito.

    - Opción de precio "Precio del pedido de venta (FIFO)": el precio de la
    línea de factura se obtiene de la línea del pedido de venta y, si no hay
    línea de venta asociada, se asigna el precio de venta de la ficha de
    producto con la tarifa correspondiente aplicada.

    - Opción de precio "Último precio": el precio de la línea de factura se
    obtiene de la última línea de pedido de venta confirmada para ese cliente
    y, si no hay ninguna línea de venta, se asigna el precio de venta de la
    ficha de producto con la tarifa correspondiente aplicada.

    - Crear factura: si se selecciona esta opción, se generará la factura
    correspondiente a los movimientos realizados. Si no está seleccionada,
    debe generarla manualmente más tarde desde el pedido de cliente.

    - Líneas de los movimientos que se desean realizar desde el depósito al
    cliente.

Al confirmar, de forma automática el sistema genera un nuevo pedido con las
cantidades a mover desde el depósito al cliente, con su albarán interno
asociado y la factura correspondiente, si se marca el campo "Crear factura".

Configuración
-------------

Para que los usuarios encargados puedan ver la configuración del almacén y
añadir la ubicación padre para los depósitos deben pertenecer al grupo
"Gestionar flujos de inventario push y pull".

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

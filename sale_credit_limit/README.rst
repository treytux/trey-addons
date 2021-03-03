.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html

=================
Sale credit limit
=================

Cuando se crea, se actualiza o se confirma un pedido de venta se verifica si el cliente tiene límite de crédito y se recalculan dos campos que muestran la información sobre el crédito del cliente y los avisos de crédito excedido, si los hay.

Si dicho cliente tiene límite de crédito establecido se calcula la suma de los importes de las facturas impagadas con pedidos de venta confirmados. Si esta suma es mayor que el límite de crédito y el usuario no pertenece al grupo "Permitir límite de crédito de venta" la operativa será la siguiente, dependiendo de la configuración del campo "Tipo de notificación de límite de crédito" desde el menú "Configuración/Compañías/Compañía":

    - Bloqueo: no se podrá confirmar el pedido.

    - Aviso: se mostrará el aviso correspondiente en el campo en rojo pero se permitirá continuar y confirmar el pedido.

Además, si el cliente ya ha excedido el límite de crédito, mostrará un aviso al rellenar el campo del cliente.

También se incluye un asistente para importar límites de crédito desde un archivo disponible desde el menú 'Contabilidad/Configuración/Importar límite de crédito'.


Autor
~~~~~~~
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

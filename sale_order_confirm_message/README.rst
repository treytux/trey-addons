=========================
Sale order confirm message
=========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Evita que los comerciales confirmen presupuestos de venta sin cotejar
      antes los datos con el documento firmado por el cliente.
    * Al pulsar «Confirmar» en un presupuesto (en estado borrador o enviado),
      se muestra una ventana con los datos importantes en solo lectura y un
      aviso destacado en rojo para que se revisen antes de confirmar.
    * El recuadro rojo muestra siempre, bajo el texto configurable, la lista
      fija de datos que no podrán modificarse tras confirmar (cliente,
      direcciones, plazos y modo de pago, incoterm, datos de las líneas y
      totales), con independencia del texto que edite el administrador. Esta
      lista se genera desde el código en el idioma del usuario, por lo que se
      traduce también con el servidor en modo desarrollo (``--dev=xml``).
    * Datos mostrados: cliente, dirección de entrega, dirección de factura,
      plazos de pago, modo de pago e incoterm; por cada línea el producto,
      la cantidad, el precio unitario, los impuestos, el descuento y el
      subtotal; y los totales del pedido (base imponible, impuestos y total).
    * Opcionalmente exige marcar una casilla de conformidad antes de permitir
      la confirmación.

Configuración
~~~~~~~~~~~~~

En *Ventas > Configuración > Ajustes*, por compañía:

* Activar o desactivar la ventana de revisión al confirmar.
* Exigir o no la casilla de conformidad.
* Editar el texto del aviso (traducible).

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:

===========================
Website Sale Payment Mode
===========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Asigna modos de pago a los proveedores de pago disponibles en el sitio web.

**Tabla de contenidos**

.. contents::
   :local:

Configuración
=============

Antes de utilizar este módulo, asegúrate de que:

#. El módulo **account_payment_sale** está instalado.
#. Se han creado y configurado correctamente los modos de pago (*account.payment.mode*) en *Contabilidad > Configuración > Modos de pago*.
#. Los proveedores de pago en *Sitio web > Configuración > Proveedores de pago* tengan asignado un modo de pago válido.

Esto garantiza que, al procesar una venta desde el sitio web, se asignará correctamente el modo de pago correspondiente.

Uso
===

#. Ir a *Sitio web > Configuración > Proveedores de pago*.
#. Seleccionar un proveedor de pago.
#. Indicar el modo de pago deseado en el nuevo campo disponible.

Esto permitirá que las ventas realizadas desde el sitio web tengan automáticamente asignado un modo de pago dependiendo del proveedor seleccionado por el cliente.

Créditos
========

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

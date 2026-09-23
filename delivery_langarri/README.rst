=================
Delivery Langarri
=================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo integra los servicios web de Langarri para registrar envíos,
obtener el identificador de seguimiento y generar la etiqueta de transporte.

**Índice**

.. contents::
   :local:

Uso
===

Debe configurar el transportista Langarri en el albarán que va a enviar:

 * En el formulario del albarán, acceda a la pestaña *Información adicional* y seleccione Langarri como transportista, junto con el servicio y el código de producto.
   Solo podrá hacerlo si el estado del albarán es «Preparado».

 * Cuando el albarán pase a «Transferido», la etiqueta de transporte se adjuntará y la referencia de seguimiento se mostrará en la pestaña de información adicional.

Notas
=====

Langarri no proporciona credenciales de prueba estándar. Debe solicitar
credenciales para poder utilizar el módulo.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: Licencia: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

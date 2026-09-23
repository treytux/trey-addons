============================
Stock Picking Return Address
============================

Muestra la dirección del cliente en el encabezado del albarán de devolución
(movimientos de entrada).

Características
===============

* Añade el bloque ``Dirección para devolución`` en el informe de albarán
* Usa el contacto del albarán (``partner_id``)
* Muestra nombre, dirección y teléfono
* Solo aplica a albaranes de tipo ``incoming``

Instalación
===========

El módulo está en ``addons/trey-addons/stock_picking_return_address/``.

Para instalar:

#. Inicia sesión en Odoo con credenciales de administrador
#. Ve a Apps -> All Apps
#. Busca ``Stock Picking Return Address``
#. Pulsa Install

O por línea de comandos:

::

    ./odoo-bin -c odoo-server.conf -d <database_name> -i stock_picking_return_address

Configuración
=============

No requiere configuración adicional.

Uso
===

#. Abre un albarán de devolución o recogida (tipo de operación ``incoming``)
#. Imprime el albarán
#. Verifica que aparece el bloque ``Dirección para devolución`` con los datos
   del cliente

Créditos
========

Trey, Kilobytes de Soluciones <www.trey.es>


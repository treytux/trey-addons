==========================
Stock Picking Line Section
==========================

Muestra la sección del pedido de venta en una columna ``Section`` específica
en los informes de albarán.

Características
===============

* Añade una columna ``Section`` en las tablas del informe de albarán
* Mantiene separados el nombre del producto y el texto de sección
* Soporta los formatos de albarán pendiente y realizado
  (líneas en serie y agregadas)
* Gestiona automáticamente los productos sin sección

Instalación
===========

El módulo está en ``addons/trey-addons/stock_picking_line_section/``.

Para instalar:

#. Inicia sesión en Odoo con credenciales de administrador
#. Ve a Apps -> All Apps
#. Busca ``Stock Picking Line Section``
#. Pulsa Install

O por línea de comandos:

::

    ./odoo-bin -c odoo-server.conf -d <database_name> -i stock_picking_line_section

Configuración
=============

No se requiere configuración adicional.

Uso
===

#. Crea un pedido de venta con líneas de sección
   (tipo de visualización ``line_section``)
#. Añade productos bajo cada sección
#. Confirma el pedido de venta y abre el albarán relacionado
#. Imprime el informe de albarán
#. El informe mostrará el valor de la sección en la columna ``Section``,
   separado de la columna de producto

Créditos
========

Trey, Kilobytes de Soluciones <www.trey.es>

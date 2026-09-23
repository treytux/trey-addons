=============================
Website Sale Availability Msg
=============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Muestra mensajes de disponibilidad del producto en la tienda online.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__


Descripción
~~~~~~~~~~~

Este módulo modifica la tienda online de Odoo para mostrar un mensaje de
producto no disponible tanto en el listado como la ficha de producto en caso
de que el campo configurado (por defecto `cantidad disponible`) sea 0.

El campo utilizado para determinar la disponibilidad puede configurarse entre
`Cantidad disponible` y `Cantidad prevista` desde la configuración general.

De igual forma, muestra en las líneas del carrito un mensaje bajo la cantidad
de las unidades disponibles si las que se han añadido al carrito son mayores
que las mencionadas unidades disponibles.

Características
~~~~~~~~~~~~~~~

* Muestra mensajes de disponibilidad en el listado y ficha de producto.
* Permite configurar el campo de stock `Cantidad disponible` o `Cantidad prevista`.
* Muestra las unidades disponibles en el carrito si se superan las unidades
disponibles.

Uso
~~~

Una vez instalado el módulo, los mensajes se mostrarán en la tienda online.
El campo de stock utilizado puede configurarse desde la configuración general.

Instalación
~~~~~~~~~~~

1. Copie el módulo en su carpeta de addons.
2. Actualice la lista de módulos en Odoo.
3. Instale el módulo desde el menú de aplicaciones.

Requisitos
~~~~~~~~~~

* Odoo 16.0 o superior.

Créditos
~~~~~~~~

Desarrollado por Trey.

Licencia
~~~~~~~~

AGPL-3.0

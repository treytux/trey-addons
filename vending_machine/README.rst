==================
Vending Machine
==================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Gestión de máquinas expendedoras mediante integración con ventas y stock.

**Tabla de contenidos**

.. contents::
   :local:

Uso
===

Este módulo permite la gestión de máquinas expendedoras integradas con los módulos de ventas y stock, automatizando tanto la reposición como la facturación de productos consumidos.

Configuración
-------------

1. Asigne un usuario responsable que recibirá por correo electrónico el presupuesto de reposición.
2. Configure las credenciales de acceso a la máquina expendedora.
3. En la ficha del cliente, en la pestaña *Facturación Máquinas Expendedoras*, defina si se desea unificar la facturación de todas las máquinas asociadas.

Creación de máquinas expendedoras
---------------------------------

Para crear una máquina expendedora:

1. Vaya a *Ventas > Máquinas expendedoras*.
2. Pulse *Crear* y configure los campos necesarios.

Acciones disponibles
--------------------

- **Obtener datos de stock**: mediante el botón *Obtener datos de stock*, se recupera el stock actual de la máquina y se muestra en un asistente.

- **Reposición de productos**: el botón *Reposición* genera un presupuesto de reposición de productos. Este se notifica por correo al usuario configurado. Una vez validado el albarán interno, se reponen los productos en la máquina y se actualiza su stock.

- **Mover stock depósito**: el botón *Mover stock depósito* crea un pedido de venta para facturar al cliente los productos consumidos durante el mes anterior (del día 1 al último día del mes anterior). Este rango puede modificarse manualmente desde el asistente.

    - Si el campo *Unificar facturación de máquinas expendedoras* está activado en la compañía, se generará un único pedido de venta con los productos consumidos por todas las máquinas del cliente que estén en Odoo.
    - En caso contrario, se generará un pedido por cada máquina expendedora individual.

========

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

Licencia
========

AGPL-3

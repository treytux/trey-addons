============================
Sale order line supplierinfo
============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo añade la posibilidad de establecer unas rutas personalizadas por línea de "Información del proveedor" (modelo
"product.supplierinfo").

En las líneas de pedido de venta podrá seleccionar qué proveedor desea usar para la línea de pedido, y puede cambiar el comportamiento de las rutas dependiendo de su información de proveedor.

Es útil cuando se tiene varios proveedores para un mismo producto y con varias rutas de abastecimiento, como puede ser "Comprar" y "Bajo pedido" para un proveedor y "Dropshipping" para otro.

**Tabla de contenidos**

.. contents::
   :local:

Características principales
===========================

- Añade un campo de selección de proveedor (`supplierinfo`) en cada línea de pedido de venta.
- Permite seleccionar el proveedor concreto con el que se desea adquirir ese producto.
- Al confirmar un pedido de venta, si la línea tiene definido un proveedor específico, el pedido de compra se generará con ese proveedor. Antes de crear un nuevo pedido de compra a dicho proveedor, debe comprobar si ya existe alguno previo en borrador y, si es así, añadir la línea a dicho pedido de compra.
- La generación del pedido de compra es inmediata al confirmar el pedido de venta (no espera al planificador), por lo que en ese instante no aplica la lógica de regla de reabastecimiento diferida: se comporta como un flujo bajo pedido.
- El sistema respeta la lógica habitual de Odoo para la generación de compras, adaptándola para que tome en cuenta el `supplierinfo` asignado.
- Mejora la trazabilidad entre ventas y compras para productos con múltiples proveedores.

Uso
===

1. Configurar los proveedores del producto desde la pestaña *Información de proveedor* del formulario del producto.
2. Crear un pedido de venta y añadir productos.
3. Para cada línea de pedido, seleccionar el proveedor deseado (si aplica).
4. Confirmar el pedido de venta.
5. El sistema generará automáticamente un pedido de compra para cada proveedor seleccionado en las líneas.


Errores conocidos
=================

Si al instalar este módulo da el siguiente error:

    TypeError: Many2many fields product.customerinfo.route_ids and product.supplierinfo.route_ids use the same table and columns​

Se debe a que en la base de datos está instalado también el módulo "product_supplierinfo_for_customer". Para solucionarlo hay que instalar el módulo "sale_order_line_supplierinfo_fix_customerinfo".


Créditos
========

Autor
~~~~~

* `Trey <https://www.trey.es>`__:

~~~~~

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Purchase Supplierinfo No Create
===============================

- Deshabilita la creación de registros de información de proveedor al confirmar
 un pedido de compra.

Funcionalidad
-------------

- Añade un campo booleano en las categorías de producto: "Disable Supplierinfo Creation"
- Cuando este campo está marcado, al confirmar órdenes de compra no se crearán
  automáticamente registros de supplierinfo para los productos de esa categoría
- Por defecto, el campo está marcado a True para evitar la creación automática.


Uso
---

1. Ir a Inventario > Configuración > Categorías de Producto
2. Seleccionar la categoría deseada
3. Marcar el campo "Disable Supplierinfo Creation"
4. Los productos de esta categoría ya no crearán supplierinfo automáticamente al confirmar pedidos de compra

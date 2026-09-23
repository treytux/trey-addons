============================
Contract invoice extra lines
============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo añade líneas extra al contrato para que se añadan a la factura generada por el contrato.

Uso
---
Acceda al formulario del contrato y, en la pestaña "Líneas extra", añada las líneas que desea que se incluyan en la factura. Rellene los siguientes campos por cada línea:
    - Producto.
    - Nombre: por defecto se asigna el del producto, pero puede modificarse.
    - Cantidad.
    - Precio unitario: por defecto se asigna el del producto, pero puede modificarse.
    - Fecha de facturación: por defecto se asigna la fecha actual, pero puede modificarse. Indica la fecha en la que se incluirá este producto en la factura del contrato.
    - Factura asociada: factura donde se ha añadido esta línea extra de contrato.

- Cuando genere la factura del contrato, se añadirán a la factura las líneas extra que correspondan.


**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:

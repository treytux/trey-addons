=================================
Website sale product image import
=================================

Importación masiva de imágenes de productos mediante un archivo ZIP para
Odoo 16.

Acceso
======

Disponible en ``Ventas > Productos > Importar imágenes de productos`` para
usuarios internos.

Formato del ZIP
===============

Los archivos deben estar en la raíz y seguir el patrón::

    REFERENCIA-N.extensión

Se admiten ``.jpg``, ``.jpeg``, ``.png`` y ``.webp``. La referencia debe
coincidir exactamente con ``product.product.default_code``. La numeración
debe empezar en ``1`` y ser consecutiva, sin duplicados::

    31GTIAS-1.jpg
    31GTIAS-2.jpg
    31GTIAS-3.jpg

El archivo ``-1`` sustituye la imagen principal; los demás se guardan como
imágenes adicionales en el orden indicado.

Destinos
========

Plantilla de producto
---------------------

Es el destino predeterminado. Se sustituyen únicamente la imagen principal y
las imágenes adicionales de la plantilla. Las imágenes propias de sus
variantes se conservan.

Si varias referencias diferentes del ZIP apuntan a una misma plantilla, se
omite esa plantilla y se informa del conflicto. La comprobación se realiza al
validar y se repite al importar. Una referencia compartida por variantes de la
misma plantilla sí es válida; si apunta a varias plantillas, queda bloqueada.

Variante de producto
--------------------

Se sustituyen únicamente la imagen principal y las imágenes adicionales de la
variante. Si la referencia corresponde a varias variantes activas, se informa
del conflicto y no se elige ninguna automáticamente.

Compañías y archivados
======================

Solo se buscan variantes activas de la compañía seleccionada. Los productos
de otras compañías y los archivados no se importan.

Validación e informe
====================

``Validar ZIP`` comprueba el archivo sin modificar productos. Después se puede
pulsar ``Importar ZIP validado`` o importar directamente desde el formulario.
El informe distingue elementos validados y cargados, y muestra referencias no
encontradas, archivos inválidos, conflictos y errores de actualización.

Cada producto se procesa de forma independiente: un error no revierte los
productos cargados correctamente.

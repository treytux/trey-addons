.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Product BMEcat Export
=====================

Este módulo extiende el modelo `product.catalog` (proporcionado por `product_catalog_label`) para añadir la capacidad de exportar el catálogo de productos al formato XML estándar **BMEcat 2005**, un formato ampliamente utilizado en el intercambio electrónico de catálogos entre fabricantes, distribuidores y plataformas de comercio electrónico B2B.

**Tabla de contenidos**

.. contents::
   :local:

Funcionalidades
===============

- Exportación de productos al formato XML BMEcat 2005.
- Generación de un token único por catálogo para control de acceso a la descarga.
- Sistema de caché configurable para evitar regenerar el XML en cada petición.
- URL pública de descarga protegida por token: `/bmcat/<token>/download`
- Asistente para exportación rápida desde el menú de catálogos.
- Incluye en el XML: cabecera del catálogo, datos del proveedor (empresa actual), y por cada producto:

  - Código de artículo (SUPPLIER_AID / ARTICLE_NO)
  - Código EAN / barcode
  - Nombre corto y descripción larga
  - Categoría (CLASIFICATION_GROUP)
  - Precio neto (list_price) en EUR
  - Peso (PRODUCT_FEATURES)
  - Imagen principal (MIME, formato PNG)

Configuración
=============

1. Acceda al formulario de un **Catálogo de productos** (Product Catalog).
2. En la pestaña **BMEcat Export**:
   - Haga clic en **Regenerate token** para generar un token único que protegerá la descarga.
   - Establezca **Cache hours** para indicar durante cuántas horas se almacena el XML generado. Valor 0 desactiva la caché.
3. La URL pública de descarga se muestra en el formulario:
   `/bmcat/<token>/download`

Uso
===

Desde el catálogo
-----------------

En el formulario del catálogo, pulse el botón **Export BMEcat now**. La exportación genera el XML y redirige a la URL de descarga.

Desde el asistente
------------------

1. Vaya a **Catálogos > Export BMEcat**.
2. Seleccione el catálogo a exportar.
3. Pulse **Export**. El XML estará disponible para descargar directamente.

Descarga por token
------------------

Comparta la URL pública `/bmcat/<token>/download` con sus clientes o sistemas externos. La descarga no requiere autenticación en Odoo, solo el token. Si la caché está activa, las descargas sucesivas devolverán el mismo archivo hasta que expire.

Dependencias
============

- ``product_catalog_label`` — proporciona el modelo `product.catalog` base.
- ``product`` — modelos de producto base.
- ``sale`` — precios y unidades de venta.

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

Licencia
========

Este módulo está licenciado bajo AGPL-3.
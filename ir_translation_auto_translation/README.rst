=====================
Automatic Translation
=====================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo permite traducir automáticamente contenido de negocio en Odoo
utilizando un proveedor externo de traducción.

Funcionalidad principal
~~~~~~~~~~~~~~~~~~~~~~~

* Traducción de registros individuales desde asistente.
* Traducción masiva por modelo (todos, por dominio o por selección).
* Selección de campos traducibles (``char``, ``text``, ``html``).
* Traducción a uno o varios idiomas de destino.
* Opción para sobrescribir o respetar traducciones existentes.
* Registro de resultados con éxitos, omitidos y errores.

Modelos soportados en traducción masiva
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``product.template``
* ``product.public.category``
* ``website.page``
* ``product.product``
* ``res.partner``

Cómo se usa
~~~~~~~~~~~

1. Ir a **Ajustes > Traducciones** y configurar Auto Translation:
   proveedor, timeout, reintentos y parámetros de lote.
2. Para traducción individual:
   abrir un producto y pulsar **Auto Translate**.
3. Para traducción masiva:
   usar **Traducciones > Auto Translation > Bulk Translate** o la acción
   contextual desde la lista de productos.
4. Seleccionar idioma origen, idiomas destino, campos y filtro.
5. Ejecutar y revisar el ``Status Log``.

Ejemplo real
~~~~~~~~~~~~

Una tienda con 800 productos en español quiere publicar en inglés:

1. Abrir **Bulk Translate**.
2. Modelo: ``product.template``.
3. Campos: ``name`` y ``description``.
4. Idioma origen: ``es_ES``.
5. Idioma destino: ``en_US``.
6. Filtro: todos los registros.
7. Ejecutar.

Resultado esperado:

* Se crean traducciones en inglés para los campos seleccionados.
* Si no se marca sobrescritura, no se pisan traducciones manuales previas.
* El log muestra cuántos campos se tradujeron, omitieron o fallaron.

Notas
~~~~~

* El texto original del idioma base no se modifica.
* Las traducciones se guardan en base de datos (``ir.translation``),
* Dependencia Python requerida: ``deep-translator>=1.11.0``.

Autor
~~~~~

* `Trey <https://www.trey.es>`__:

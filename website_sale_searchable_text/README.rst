============================
Website sale searchable text
============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Añade un campo calculado y almacenado ``searchable_text`` en
      ``product.template`` que concatena el nombre del producto, la descripción
      web (sin etiquetas HTML), el campo ``hidden_mapping`` y las referencias
      internas de todas sus variantes.
    * Añade el campo ``hidden_mapping`` para introducir términos de búsqueda
      adicionales (sinónimos, nombres alternativos, errores frecuentes) que no
      se muestran en la ficha pública pero sí hacen que el producto aparezca en
      los resultados del buscador de la tienda web.
    * Registra ``searchable_text`` como campo de búsqueda de la tienda web
      (``product.template._search_get_detail``), de modo que el buscador de
      ``/shop`` y su autocompletado también consultan ese contenido.

**Tabla de contenidos**

.. contents::
   :local:


Uso
~~~

* En la ficha del producto (pestaña Ventas, sección eCommerce) se rellena
  opcionalmente el campo "Hidden mapping" con palabras clave extra.
* El campo "Searchable text" se recalcula automáticamente y es visible solo en
  modo desarrollador (solo lectura).
* En la tienda web, al buscar en ``/shop`` el término se busca también sobre
  ``searchable_text``, por lo que un producto es localizable por su referencia
  de variante o por los términos de "Hidden mapping".


Notas de migración (12.0 -> 16.0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* En la 12.0 el módulo reescribía por completo
  ``WebsiteSale._get_search_domain`` y hacía OR entre las palabras buscadas,
  con soporte de frase exacta entre comillas.
* En la 16.0 la búsqueda de ``/shop`` pasa por la búsqueda "fuzzy"
  (``website._search_with_fuzzy`` -> ``product.template._search_get_detail``).
  El módulo se limita a añadir ``searchable_text`` a ``search_fields``, por lo
  que se adopta la semántica estándar de Odoo 16: deben coincidir todas las
  palabras (AND), cada una en alguno de los campos de búsqueda.


Autor
~~~~~

* `Trey <https://www.trey.es>`__

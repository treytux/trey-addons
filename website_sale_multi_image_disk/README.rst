.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Website Sale Multi Image Disk
=============================

- Lee las imágenes de los productos de la tienda online desde una carpeta en el
servidor en lugar de desde la base de datos.

Configuración en el sitio web
-----------------------------

- Directorio de imagen slug: Directorio donde están las imágenes en el disco.

- Imagen slug traducción: Si se marca el slug será traducido dependiento el
idioma del usuario, por el contrario se usa el idioma por defecto del sitio
web (recomendado si no se quieren mostrar imágenes diferentes por idioma).

Uso
---

- Los productos muestran en la ficha el campo slug.

- Para que los productos muestren fotografías, basta con crear una carpeta en
el "Directorio de imagenes" en el servidor con el slug de cada producto y subir
dentro las imágenes renombradas con el formato "[slug del producto]-[1-n].jpg".

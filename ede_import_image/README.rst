.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================
Ede import images
=================

Modulo para la importación de imágenes proporcionadas por ede del siguiente modo:

- Fichero XML en formato bmecat convertido a csv según documentación.
- Carpeta de imágenes.

Conversion de formato bmecat a csv
===================================
El fichero BMECAT contiene toda la información del catalogo de EDE. El problema es que es un fichero muy pesado y al
procesarlo con Python da errores de memoria.

Como solo tenemos que cargar las imágenes, mediante Pentaho Kettle realizamos las operaciones necesarias para extraer la
información y grabarlo en un fichero csv con una estructura definida.

Dicho trabajo de transformación esta en la carpeta tools del modulo 01_bmecat_2_csv_images.ktr.



Configuración
==============

En la configuración de la compañía, necesitamos revisar los siguientes parámetros:

* Lote de carga de imágenes: Al lanzar la tarea programada se cargaran en lotes según este parámetro.
* Localización de la carpeta de imágenes. Normalmente será \instance\filestore\database\ede_images.
* La carpeta contendrá un fichero csv con el nombre ede_images.csv y un directorio llamado images con las mismas.
* La carpeta contendrá un fichero csv con el formato esperado llamado ede_images.csv.
* La carpeta contendrá un subdirectorio llamado images.


Uso
====

Programar la tarea de carga dejando el suficiente intervalo para la finalización de la carga anterior.

Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

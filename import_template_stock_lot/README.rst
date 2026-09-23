=========================
Import template stock lot
=========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo depende del módulo "import_template" que añade un asistente para importar plantillas a través de un fichero. Al instalar el módulo se añade la funcionalidad para importar registros de lotes en Odoo a partir de la plantilla de ejemplo que se adjunta.

**Tabla de contenidos**

.. contents::
   :local:

Configuración
=============

#. En *Ajustes > Importar fichero > Importar fichero* se muestra el asistente donde el usuario selecciona la plantilla del modelo a importar; en este caso "Plantilla para importar fichero de lotes". Una vez seleccionada se mostrará la ayuda para cada columna del fichero a importar.
#. El usuario subirá el fichero a importar; puede descargar un ejemplo desde el botón "Abrir plantilla".
#. Cuando acepte, se hará una simulación de la importación y se mostrará al usuario un listado con avisos y/o errores, en caso de que exista alguno. Si acepta, se importará el fichero y se mostrará un listado con los posibles avisos y/o errores que se hayan producido.

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_

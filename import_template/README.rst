===============
Import template
===============

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo añade un asistente para importar plantillas a través de un fichero. Se usará como base para importar distintos registros de modelos en cada módulo que herede de éste.

**Tabla de contenidos**

.. contents::
   :local:

Configuración
=============

#. En *Ajustes > Importar fichero > Importar fichero* se muestra el asistente donde el usuario selecciona la plantilla del modelo a importar. Una vez seleccionada se mostrará la ayuda para cada columna del fichero a importar.
#. El usuario subirá el fichero a importar; puede descargar un ejemplo desde el botón "Abrir plantilla".
#. Cuando acepte, se hará una simulación de la importación y se mostrará al usuario un listado con avisos y/o errores, en caso de que exista alguno. Si acepta, se importará el fichero y se mostrará un listado con los posibles avisos y/o errores que se hayan producido.
#. Si se desea, se puede activar desde  *Ajustes > Opciones generales > Registros de importe plantillas* la activación/desactivación de registros de log de la importación.

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_

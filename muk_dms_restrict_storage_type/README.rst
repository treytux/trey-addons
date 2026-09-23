=============================
MuK Dms Restrict Storage Type
=============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Módulo para requerir que el tipo de guardado de los almacenamientos del gestor de documentos MuK IT sea 'Filestore'.

    * Evitar el guardado de documentos en base de datos, con el consiguiente aumento de tamaño de ésta, fuerza a guardarlos en el filestore.

    * Depende del módulo 'muk_dms', del repositorio `MuK Document Management System <https://github.com/muk-it/muk_dms>`__.


**Tabla de contenidos**

.. contents::
   :local:

Uso
~~~

#. Una vez instalado el módulo, es necesario configurar el tipo de guardado de los almacenamientos a 'Filestore' si no están establecidos y pulsar en el botón 'Migrate Files' para convertirlos.

Autor
~~~~~

* `Trey <https://www.trey.es>`__

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
Document Expiry Course
======================

Módulo para gestionar la caducidad de la documentación relacionada con los
cursos de los empleados. Añade el tipo de documento ``Curso`` al módulo
``document_expiry`` y permite vincular cada documento con un curso de
``hr_course``.

Funcionalidades
===============

* Añade ``Curso`` como tipo de documento para la documentación de empleados.
* Permite seleccionar el curso asociado al documento de caducidad.
* Muestra los documentos de cursos en la pestaña **Documentación** del
  empleado.
* Permite buscar y agrupar los documentos por curso.
* Conserva los estados de ``document_expiry``: válido, próximo a caducar y
  caducado.
* Utiliza las fechas de inicio y vencimiento para controlar la vigencia del
  certificado o documento del curso.

Uso
===

#. Asignar al usuario el grupo **Caducidad de documentos / Usuario** o
   **Caducidad de documentos / Responsable**.
#. Crear los cursos desde el menú de cursos de empleados.
#. Abrir un empleado y acceder a la pestaña **Documentación**.
#. Añadir una línea, seleccionar ``Curso`` y elegir el curso correspondiente.
#. Introducir las fechas de vigencia y guardar el documento.

Cuando la fecha de vencimiento se aproxima, el documento utiliza los avisos y
actividades configurados por ``document_expiry``.

Alcance
=======

El módulo registra la vigencia de un certificado o documento relacionado con
un curso. No gestiona la matrícula, asistencia, evaluación ni la superación
del curso; esas operaciones pertenecen al módulo ``hr_course``.


Autor
=====

.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL

`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_

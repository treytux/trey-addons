.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========
Education
=========

Este módulo permite gestionar estudiantes, profesores, tutores, planes formativos, clases, asignaturas y matrículas.


Configuración
=============

.. image:: education/static/description/education.png

Existen los siguientes roles de usuario:

* Responsable
* Usuario
* Estudiante
* Profesor
* Tutor

El rol correspondiente a padres o responsables del estudiante.

Es necesario asignar alguno de los roles para poder ver el menú de "Educación".


Gestión de planes formativos
============================

El orden lógico para gestionar correctamente los planes educativos es:

1. Crear las asignaturas
Las asignaturas se crean desde el apartado "Educación > Configuración > Asignaturas".
Ejemplo: "Matemáticas"

2. Crear el plan formativo
Los planes formativos se crean desde "Educación > Planes formativos > Planes formativos"
Ejemplo: "1º ESO 2017/2018"

3. Crear las clases para los planes formativos
Pueden crearse desde "Educación > Planes formativos > Clases" o bien desde dentro de un plan formativo, en el apartado "Clases".
Ejemplo: "1º A" para el plan formativo "1º ESO 2017/2018"

4. Crear los profesores
Los profesores se gestionan en "Educación > Profesores > Profesores" o bien, se pueden crear desde una línea de plan formativo, en el campo dedicado al profesor. Es importante que en la pestaña "Ventas y compras", el campo "Profesor" quede marcado para indicar que es un profesor.
Ejemplo: "Pedro Jiménez"

5. Crear las líneas de plan formativo
Las líneas de plan formativo se crean desde dentro de un plan educativo, en el apartado "Líneas" o bien desde el menú "Educación > Planes formativos > Planes formativos > Líneas plan formativo".
Ejemplo: dentro del plan formativo "1º ESO 2017/2018", hacemos uso de los ejemplos anteriores y creamos una línea que contiene "Matemáticas" / "Pedro Jiménez" / "1º A"

El plan educativo quedaría de la siguiente forma:

.. image:: education/static/description/training_plan.png

Gestión de matrículas
=====================

Las matrículas pueden ser gestionadas desde "Educación > Matrículas > Matrículas".

Los posibles estados de la matrícula son:

- Borrador
- Activo: es el único estado en el que la matrícula está vigente.
- Finalizado
- Cancelado: desde este estado puede pasarse de nuevo a borrador.

Antes de crear la matrícula, es conveniente dar de alta al alumno, si no estuviera dado de alta previamente. Para ello, se puede hacer desde dentro de la propia matrícula o bien desde el menú "Educación > Estudiantes > Estudiantes". Es importante que el alumno tenga marcado "Estudiante" en el apartado de "Ventas & Compras" para que se considere que es un estudiante.

A parte del alumno, es posible seleccionar los tutores del estudiante. Son considerados tutores los padres o tutores legales del alumno. Los tutores se pueden crear desde la ficha del estudiante, apartado "Tutores" o bien desde el apartado "Educación > Estudiantes > Tutores". En este caso, es importante indicar en el apartado de "Ventas & Compras" que es un tutor y en el apartado "Estudiantes" seleccionar el alumno o alumnos que están a su cargo.

Las matrículas tienen su propio informe para imprimirlas en pdf, que incluye la información visible en la matrícula, los datos del alumno y sus tutores, si los hubiera, y la descripción del plan formativo seleccionado.

.. image:: education/static/description/matricula.png








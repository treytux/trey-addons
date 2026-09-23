.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======
Academy
=======

Este módulo permite gestionar una academia en Odoo 16 cubriendo:

* Planes formativos y actividades.
* Estudiantes, tutores y profesores.
* Matrículas y su ciclo de vida.
* Evaluaciones, conceptos evaluables y calificaciones.
* Boletines de notas.
* Facturación mensual de actividades.


Roles y acceso
==============

El módulo define los siguientes grupos de seguridad:

* Responsable
* Usuario
* Estudiante
* Profesor
* Tutor

Cada grupo habilita menús y vistas específicas dentro de ``Academy``.

Además:

* El estudiante sólo puede ver sus propias matrículas.
* Profesor, tutor y estudiante tienen acceso de lectura a los contactos
  relacionados.


Datos maestros
==============

Antes de trabajar con matrículas y boletines conviene configurar estos
elementos:

1. Crear el plan formativo.
   Se gestiona desde ``Academy > Training Plans > Training Plans``.
   Ejemplo: ``Plan 2024/2025``.

2. Definir la tipología, si aplica.
   La tipología permite almacenar condiciones de matrícula que después se
   copian automáticamente al crear la matrícula.

3. Crear las actividades.
   Se gestionan desde ``Academy > Training Plans > Activities`` y deben
   pertenecer a un plan formativo.

4. Crear o vincular al profesor.
   El profesor se selecciona en la actividad a partir de ``hr.employee``.
   El empleado debe ser seleccionable en actividades.

5. Configurar evaluaciones.
   Se gestionan desde ``Academy > Configuration > Evaluations`` o desde la
   propia actividad.

6. Configurar conceptos evaluables.
   Se gestionan desde ``Academy > Configuration > Evaluable Concepts`` o desde
   la actividad.

7. Configurar las calificaciones válidas para cada concepto evaluable.
   Se gestionan desde ``Academy > Configuration > Evaluable Concept Marks``.

8. Configurar precios y producto de facturación en la actividad si se desea
   emitir facturas.

Al crear un plan formativo, el módulo genera automáticamente una cuenta
analítica si no se indica una manualmente.

El plan educativo quedaría de la siguiente forma:

.. image:: academy/static/description/training_plan.png

La actividad quedaría de la siguiente forma:

.. image:: academy/static/description/activity.png


Gestión de estudiantes, tutores y profesores
============================================

Los estudiantes y tutores se gestionan desde ``Academy > Students``.

En contactos:

* ``Student`` identifica a los alumnos.
* ``Tutor`` identifica a los tutores o representantes legales.
* Un estudiante puede tener varios tutores.
* Un tutor puede estar relacionado con varios estudiantes.

Los profesores se gestionan desde ``Academy > Teachers`` y se apoyan en
empleados de Odoo. Cuando un empleado es seleccionable en actividades, su
contacto laboral se marca como profesor.


Gestión de matrículas
=====================

Las matrículas se gestionan desde ``Academy > Enrollments``.

Estados disponibles:

* ``Pending Level``
* ``Pending Group``
* ``Attending``
* ``F.S.``
* ``Drop Out``
* ``Cancelled``

Consideraciones funcionales:

* La actividad y el plan formativo son obligatorios.
* La matrícula debe quedar dentro del rango de fechas de la actividad.
* No se permiten matrículas duplicadas para el mismo alumno y actividad.
* La actividad respeta un límite máximo de alumnos.
* Al seleccionar un estudiante, se proponen automáticamente sus tutores y su
  formación académica.
* Si la tipología del plan tiene condiciones de matrícula, se copian al campo
  de comentarios.

La matrícula tiene su propio informe PDF con la información visible en la ficha,
los datos del alumno, sus tutores y la descripción del plan formativo.

.. image:: academy/static/description/enrollment.png


Gestión de boletines de notas
=============================

Los boletines se gestionan desde ``Academy > Students > Marks Bulletins`` y
también pueden generarse desde una actividad.

Flujos disponibles:

* Crear un boletín manualmente para una matrícula activa.
* Generar boletines desde una actividad para una evaluación concreta.
* Añadir líneas de evaluación faltantes a un boletín existente.
* Publicar líneas del boletín para que sean visibles en portal.

Durante la generación desde actividad:

* Se incluyen matrículas en estado ``Attending``, ``F.S.`` o ``Drop Out``.
* La fecha indicada en el asistente debe quedar dentro del rango de la
  matrícula.
* Si ya existe un boletín para la matrícula, no se duplica; sólo se completan
  las líneas necesarias.

Cada línea del boletín combina:

* Evaluación.
* Concepto evaluable.
* Calificación.
* Indicador de publicación en portal.

Los boletines tienen su propio informe PDF con datos del alumno, matrícula,
actividad y notas registradas.

.. image:: academy/static/description/marks_bulletin.png


Facturación de actividades
==========================

El módulo incluye un asistente para facturar actividades de forma mensual.

Condiciones principales:

* La actividad debe tener marcado ``Invoice tutors`` para generar facturas.
* La actividad debe tener producto de venta.
* La fecha de facturación debe estar dentro del periodo de la actividad.
* No se genera una segunda factura para la misma actividad y mes.

Comportamiento de facturación:

* Si la matrícula tiene tutores, se factura al primer tutor.
* Si no tiene tutores, se factura al estudiante.
* Las matrículas gratuitas no se facturan.
* Si la matrícula tiene precio reducido, se usa el precio reducido de la
  actividad.
* La línea de factura reparte el 100 % a la cuenta analítica del plan
  formativo.


Automatismos y cierre
=====================

El módulo incluye automatismos para cerrar planes formativos vencidos.

Al cerrar un plan formativo pueden cerrarse también las actividades y
matrículas relacionadas, ajustando la fecha de fin al día actual cuando sea
necesario.

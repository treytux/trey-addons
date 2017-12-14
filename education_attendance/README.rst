.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================
Education Attendance Sheets
===========================

Este módulo permite gestionar partes de asistencia.


Gestión de partes de asistencia
===============================

Los partes de asistencia pueden ser gestionados por los siguientes roles:

- Administrador
- Usuario
- Profesor

Y sus posibles estados son:
- Borrador
- Listo para comenzar
- Finalizado
- Cancelado

Cuando se establece el estado como "Listo para comenzar", se guarda la fecha y hora de comienzo y cuando se pone como "Finalizado", se guarda la fecha fin. Se debe escribir en el apartado de duración la duración en minutos que ha tenido la clase al terminar de pasar lista.

Si los partes los crea el propio profesor, sólo podrá seleccionar aquellas líneas de plan formativo en las que esté puesto como profesor.
Si los crea un usuario / administrador, podrá seleccionar el profesor y se cargarán en el seleccionable aquellas líneas de plan formativo en las que esté el profesor seleccionado.

.. image:: education_attendance/static/description/parte_asistencia.png

Un parte de asistencia en estado borrador puede ser para:
- Todos los estudiantes
En este caso, al ponerlo como "Listo para comenzar" se cargarán automáticamente todos los alumnos en el parte, y por defecto tendrán en campo "Presente?" como activo, para que sea más cómoda la gestión.
- Selección manual de estudiantes
Al ponerse como "Listo para comenzar", no se rellenará nada, se podrán ir añadiendo manualmente los alumnos de entre los que pertenezcan a la línea de plan formativo seleccionada.

Un parte de asistencia se puede imprimir en cualquier momento desde el menú superior de impresión > Parte asistencia.

Visibilidad para alumnos y tutores
==================================

Los roles de lumnos y tutores podrán ver desde el apartado "Educación > Estudiantes > Administrar ausencias" las faltas de asistencia que tengan.





==================
Website schema.org
==================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo modifica la vista Kanban de las tareas del proyecto para mejorar la visualización de la carga de trabajo.

En concreto, añade el campo **planned_remaining_hours** a la vista Kanban, que representa las horas restantes planificadas de la tarea (limitadas a valores positivos).

Este campo se muestra dentro de la barra de progreso de las columnas Kanban y se utiliza como base para el cálculo del progreso.

Además, se sustituye el indicador estándar por una barra de progreso basada en el estado de actividad de la tarea (activity_state), que cambia de color en función del estado:

- **success**: tareas planificadas
- **warning**: tareas previstas para hoy
- **danger**: tareas atrasadas

Esto permite una visualización más clara del estado y carga de trabajo directamente desde la vista Kanban.


**Tabla de contenidos**

.. contents::
   :local:

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_

============================
Informe de partes de horas
============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Descripción
===========

Este módulo genera un informe semanal con las horas registradas por cada
empleado en sus partes de horas, cubriendo el mes actual y el mes anterior.
El informe se envía automáticamente por correo electrónico a los
destinatarios configurados.

Características principales / lógica de uso
===========================================

El módulo define una acción planificada (cron) que se ejecuta semanalmente.
Esta acción:
1. Calcula dinámicamente los periodos del mes actual y del mes anterior.
2. Agrupa los datos de partes de horas del modelo `account.analytic.line`
   por empleado para esos dos periodos.
3. Calcula métricas de variación mensual y disponibilidad:
    - Porcentaje de incremento o descenso entre el mes actual y el anterior
      (basado en tiempo real).
    - Horas mensuales disponibles según el calendario laboral del empleado.
    - Horas de ausencia procedentes de ausencias validadas (`hr.leave`).
    - Horas netas mensuales disponibles
      (disponibles - ausencias, nunca negativas).
4. Usa una plantilla de correo para generar un email HTML con una tabla
   que muestra:
    - Nombre del empleado.
    - Total de horas trabajadas en el mes anterior (YYYY-MM).
    - Total de horas trabajadas en el mes actual (YYYY-MM).
    - Porcentaje de variación entre periodos.
    - Horas disponibles, de ausencia y netas disponibles al mes.
5. Envía este correo a todos los usuarios que pertenecen al grupo
   "Timesheet Report Recipients".

Regla de variación
==================

- Si el tiempo real del mes anterior es mayor que cero:
  `((current - previous) / previous) * 100`.
- Si el tiempo real del mes anterior es cero:
  el informe muestra `N/A` para evitar una división indefinida.

Regla de horas disponibles
==========================

- La capacidad mensual base proviene del calendario laboral del empleado.
- Solo se descuentan las ausencias validadas (`hr.leave` en estado
  `validate`).
- Las horas netas disponibles se limitan a cero cuando las ausencias superan
  la capacidad.

Configuración
=============

Para configurar los destinatarios del informe:
1. Vaya a Ajustes > Usuarios y compañías > Grupos.
2. Busque el grupo llamado "Timesheet Report Recipients". El identificador
   técnico del grupo es
   `hr_timesheet_employee_report.group_timesheet_report_recipients`.
3. Añada los usuarios deseados en la pestaña "Usuarios" de este grupo.

La acción planificada se crea y activa automáticamente al instalar el
módulo. Su configuración (intervalo, siguiente ejecución) puede ajustarse en
Ajustes > Técnico > Automatización > Acciones planificadas, buscando
"Send Weekly Employee Timesheet Summary".

Dependencias
============

Este módulo depende de:
- `hr_timesheet` y `project_task_real_time` para las horas trabajadas y de
  tiempo real.
- `hr_holidays` para las ausencias validadas usadas en los cálculos de
  disponibilidad.

Uso
===

Una vez instalado y configurado el módulo
(consulte la sección "Configuración"):
1. La acción planificada se ejecutará semanalmente según su programación.
2. El correo con el resumen de partes de horas se enviará a los usuarios del
   grupo destinatario.
3. Para probar la funcionalidad inmediatamente, la acción planificada puede
   ejecutarse manualmente desde su formulario en Ajustes > Técnico >
   Automatización > Acciones planificadas.

Errores conocidos / incidencias
==============================
* No se conocen actualmente.

Contribuciones
==============
* Si desea contribuir, contacte con el autor o cree una incidencia o una
  solicitud de cambios si el proyecto está alojado en una plataforma
  colaborativa.

Créditos
========

Autor
~~~~~

* `Trey <https://www.trey.es>`_

Mantenedores
============
Este módulo es mantenido por:

* Trey (www.trey.es)

Para soporte o para reportar incidencias, contacte a través de la URL del
autor.

# HR Timesheet Employee Report: variación y horas disponibles

## Objetivo
Ampliar el informe semanal por correo para incluir:
- Variación porcentual entre el mes actual y el mes anterior.
- Horas mensuales disponibles por empleado según su calendario laboral.
- Horas mensuales de ausencia a partir de ausencias validadas.
- Horas mensuales netas disponibles.

## Reglas de negocio
- La variación usa los valores de tiempo real.
- Si el tiempo real del mes anterior es cero, la variación es `N/A`.
- Las horas disponibles se calculan con el calendario laboral del empleado
  para el mes actual.
- Las horas de ausencia se calculan con registros validados de `hr.leave`
  que se solapan con el mes actual.
- Horas netas disponibles = max(disponibles - ausencia, 0).

## Reglas de datos y técnicas
- Añadir `hr_holidays` como dependencia en el manifest.
- Mantener las convenciones de orden y formato ya usadas en el módulo.
- El informe mantiene la lógica actual de inclusión de empleados
  (empleados con actividad de partes en cualquiera de los dos meses
  comparados).
- Si un empleado no tiene calendario, disponibles/ausencia/neto se fijan a 0.

## Casos límite
- Mes anterior = 0 y mes actual > 0: mostrar `N/A`.
- Mes anterior = 0 y mes actual = 0: mostrar `N/A`.
- Empleado sin ausencias validadas: ausencia = 0.
- Las ausencias no validadas se ignoran.
- Una ausencia que cruza límites de mes solo cuenta el tramo solapado.

## Plan de pruebas
1. Variación positiva.
2. Variación negativa.
3. Mes anterior a cero => `N/A`.
4. Horas disponibles sin ausencias.
5. Horas disponibles con ausencias validadas.
6. Las ausencias no validadas no descuentan.
7. Empleado sin partes no rompe el cálculo del informe.
8. El render de plantilla incluye nuevas columnas y caso `N/A`.
9. El envío de correo sigue funcionando con el contexto ampliado.

## Comandos de validación
- Actualizar/instalar el módulo con tests habilitados y ejecutar tests del
  módulo.
- Opcionalmente ejecutar el cron manualmente e inspeccionar el correo saliente
  generado.

# HR Holidays Public Warning Fix

## Objetivo

Evitar el warning de `hr_holidays_public` cuando se reciben simultáneamente
`employee_id` y `partner_id`.

## Comportamiento

El override prioriza `partner_id` y llama al método original con un único
identificador, manteniendo la resolución de partner del módulo OCA.

## Validación

- Instalar el módulo en una base de pruebas.
- Abrir la lista de empleados y un empleado individual.
- Confirmar que no aparece el warning de parámetros duplicados.
- Confirmar que la consulta de festivos mantiene el resultado esperado.

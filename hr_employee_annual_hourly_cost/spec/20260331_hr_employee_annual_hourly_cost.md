# Coste hora anual por empleado

## Resumen
- Módulo nuevo `hr_employee_annual_hourly_cost`.
- Permite informar coste hora anual por empleado.
- Añade fallback al `hourly_cost` actual si no existe valor anual.

## Implementación
- Nuevo modelo `hr.employee.annual.hourly.cost`.
- Relación `One2many` en `hr.employee`.
- Vista en ficha de empleado bajo el bloque de `Hourly Cost`.

## Validación
- Test de lectura por año.
- Test de fallback al coste actual.

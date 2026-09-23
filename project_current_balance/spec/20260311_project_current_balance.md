# SPEC: Saldo actual reutilizable en `project_current_balance`

## 1. Contexto
- Fecha de solicitud: 2026-03-11
- Solicitado por: user
- Alcance: documentar la extracción del cálculo base de saldo actual de
  proyecto a un módulo reutilizable.

## 2. Objetivos
- Centralizar el cálculo base de saldo actual en un módulo propio.
- Hacer reutilizable el campo `current_balance` fuera de `trey_customize`.

## 3. No objetivos
- No migrar datos manuales antiguos.
- No rediseñar recordatorios ni emails externos al módulo base.

## 4. Requisitos funcionales
- El módulo debe calcular `current_balance` como saldo extra menos horas
  imputadas desde `extra_balance_date`.
- El módulo debe exponer los campos base necesarios para ese cálculo.

## 5. Diseño técnico
- Módulo:
  - `project_current_balance`
- Dependencias:
  - `project`
  - `hr_timesheet`
- Assets y plantillas:
  - vistas de proyecto y tarea
- Datos y seguridad:
  - definición de `extra_balance`, `extra_balance_date` y `current_balance`

## 6. Plan de validación
- Instalar o actualizar el módulo.
- Ejecutar los tests del módulo.
- Verificar el cálculo sobre proyectos con partes imputados.

## 7. Riesgos y mitigaciones
- Riesgo: dependencias incompletas en campos computados.
  - Mitigación: ampliar dependencias y cubrirlo con tests.

## 8. Entregables
- `project_current_balance/models/...`
- `project_current_balance/views/...`
- `project_current_balance/tests/...`

## 9. Plan de rollback
- Revertir el módulo y restaurar el cálculo previo en el módulo origen.

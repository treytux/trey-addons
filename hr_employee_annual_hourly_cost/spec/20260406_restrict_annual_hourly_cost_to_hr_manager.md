# SPEC: Restringir coste hora anual a gestión de RRHH

## 1. Contexto
- Fecha: 2026-04-06
- Módulo: `hr_employee_annual_hourly_cost`
- Solicitud: evitar acceso de cualquier empleado y limitarlo a usuarios con
  permisos de gestión de recursos humanos usando grupos existentes.

## 2. Problema
- El ACL del modelo `hr.employee.annual.hourly.cost` usa actualmente
  `hr.group_hr_user`.
- En este contexto funcional, ese alcance es más amplio de lo deseado.

## 3. Objetivo
- Permitir acceso al modelo y a su edición solo a perfiles de gestión de RRHH.

## 4. Diseño técnico
- Cambiar `group_id` en `security/ir.model.access.csv` de
  `hr.group_hr_user` a `hr.group_hr_manager`.
- Restringir la visualización/edición del campo `annual_hourly_cost_ids`
  en la vista heredada de `hr.employee` con atributo `groups` apuntando al
  mismo grupo `hr.group_hr_manager`.

## 5. No objetivos
- No crear grupos nuevos.
- No cambiar lógica de cálculo ni constraints del modelo.

## 6. Validación
- Usuario con `hr.group_hr_manager`: puede ver/editar periodos.
- Usuario sin `hr.group_hr_manager`: no ve el bloque y no tiene ACL sobre el
  modelo.

# SPEC: Limpieza de dependencia `contract` en `portal_project`

## 1. Contexto
- Fecha de solicitud: 2026-03-09
- Solicitado por: user
- Alcance: documentar la funcionalidad implementada para desacoplar
  `portal_project` de la dependencia obsoleta `contract`.

## 2. Objetivos
- Eliminar la dependencia no utilizada `contract` del manifiesto.
- Mantener intacto el comportamiento funcional del portal de proyectos.

## 3. No objetivos
- No rediseñar funcionalidades del portal.
- No modificar módulos OCA ni core de Odoo.

## 4. Requisitos funcionales
- `portal_project` no debe depender de `contract`.
- El resto de dependencias debe seguir reflejando solo lo que el módulo usa.

## 5. Diseño técnico
- Módulo:
  - `portal_project`
- Dependencias:
  - eliminar `contract` del manifiesto
- Assets y plantillas:
  - sin cambios
- Datos y seguridad:
  - sin cambios

## 6. Plan de validación
- Revisar el diff del `__manifest__.py`.
- Ejecutar validaciones de formato sobre el manifiesto.
- Confirmar que el módulo sigue instalando y cargando correctamente.

## 7. Riesgos y mitigaciones
- Riesgo: dependencia implícita no detectada.
  - Mitigación: limitar el cambio al manifiesto y validar la carga del módulo.

## 8. Entregables
- `portal_project/__manifest__.py`

## 9. Plan de rollback
- Restaurar la dependencia `contract` en el manifiesto.

## 10. Actualizaciones posteriores
- 2026-03-18:
  - Se añade breadcrumb específico para la ruta de partes de horas
    `/my/unit/timesheets/<project_id>`.
  - En dicha ruta, se muestra el nombre del proyecto en breadcrumb
    con enlace directo a `/my/projects/<project_id>`.
  - Implementado en `views/project_portal_templates.xml` mediante herencia
    de `portal.portal_breadcrumbs`.

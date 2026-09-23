# SPEC: Enlace home en breadcrumbs del portal de empleado

## 1. Contexto
- Fecha de solicitud: 2026-05-07
- Alcance: corregir el enlace del icono de inicio en los breadcrumbs del
  portal de empleado.

## 2. Objetivos
- Hacer que el icono de inicio apunte a `/employee` cuando el usuario navega
  por páginas propias del portal de empleado.
- Mantener el comportamiento estándar `/my/home` para el resto de páginas del
  portal.

## 3. Diseño técnico
- Módulo:
  - `portal_employee`
- Vista:
  - heredar `portal.portal_breadcrumbs`
  - añadir un `t-att-href` condicional al enlace de inicio del breadcrumb

## 4. Plan de validación
- Actualizar `portal_employee`.
- Entrar en una página del portal de empleado con breadcrumb.
- Confirmar que el icono de inicio navega a `/employee`.
- Confirmar que el breadcrumb estándar de portal mantiene `/my/home`.

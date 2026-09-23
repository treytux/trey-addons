# SPEC: Extracción de `is_maintenance` a `product_template_maintenance`

## 1. Contexto
- Fecha de solicitud: 2026-03-12
- Solicitado por: user
- Alcance: documentar la funcionalidad implementada para mover el flag
  reutilizable de mantenimiento a un módulo propio.

## 2. Objetivos
- Hacer que `product_template_maintenance` sea dueño de
  `product.template.is_maintenance`.
- Mantener el consumo del campo desde módulos dependientes.

## 3. No objetivos
- No mover otras políticas de mantenimiento fuera de `trey_customize`.
- No cambiar el significado ni la etiqueta del campo.

## 4. Requisitos funcionales
- Añadir `is_maintenance` sobre `product.template` desde un módulo nuevo.
- Mostrar el campo en productos de tipo servicio.
- Reutilizar el mismo nombre técnico para conservar los datos existentes.

## 5. Diseño técnico
- Módulo:
  - `product_template_maintenance`
- Dependencias:
  - `product`
- Assets y plantillas:
  - vista heredada de producto
- Datos y seguridad:
  - sin ACL nuevas
  - sin migración de datos adicional

## 6. Plan de validación
- Instalar o actualizar el módulo.
- Verificar visibilidad del campo en servicios.
- Verificar que módulos consumidores siguen leyendo `is_maintenance`.
- Ejecutar los tests del módulo.

## 7. Riesgos y mitigaciones
- Riesgo: dependencias ausentes en módulos que leen el campo.
  - Mitigación: declarar dependencias explícitas y validar integraciones.

## 8. Entregables
- `product_template_maintenance/models/...`
- `product_template_maintenance/views/...`
- `product_template_maintenance/tests/...`

## 9. Plan de rollback
- Restaurar la propiedad del campo al módulo anterior y revertir dependencias.

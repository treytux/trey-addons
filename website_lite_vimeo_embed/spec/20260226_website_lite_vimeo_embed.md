# SPEC: Funcionalidades implementadas en `website_lite_vimeo_embed`

## 1. Contexto
- Fecha de solicitud: 2026-02-26
- Solicitado por: user
- Alcance: consolidar la especificación del módulo
  `website_lite_vimeo_embed` según las mejoras aplicadas en formato, vistas
  e internacionalización.

## 2. Objetivos
- Proveer un snippet configurable para incrustaciones ligeras de Vimeo.
- Mantener las vistas y assets del módulo con formato homogéneo.
- Dejar las traducciones y plantillas del módulo alineadas con Trey.

## 3. No objetivos
- No ampliar el módulo a otros proveedores.
- No introducir cambios funcionales fuera del snippet Vimeo.

## 4. Requisitos funcionales
- El módulo debe exponer un snippet Vimeo configurable en Website.
- Las vistas XML no deben incluir espaciado innecesario entre plantillas.
- El módulo debe mantener sus traducciones al español actualizadas.
- La carga de assets y plantillas debe seguir la estructura del módulo.

## 5. Diseño técnico
- Módulo:
  - `website_lite_vimeo_embed`
- Dependencias:
  - `website`
  - `web_editor`
- Assets y plantillas:
  - snippet XML en `views/snippets.xml`
  - plantillas website en `views/website_templates.xml`
  - traducciones en `i18n/es.po`
- Datos y seguridad:
  - sin cambios en modelos ni ACL

## 6. Plan de validación
- Actualizar el módulo en una base Odoo 16.
- Comprobar el snippet en frontend y editor web.
- Revisar visualmente el XML generado y el comportamiento del embed.
- Regenerar y revisar las traducciones del módulo.

## 7. Riesgos y mitigaciones
- Riesgo: ruido de formato en XML sin valor funcional.
  - Mitigación: limitar cambios a espaciado y estructura del módulo.
- Riesgo: desalineación entre textos e i18n.
  - Mitigación: refrescar `.po` y validar el diff resultante.

## 8. Entregables
- `website_lite_vimeo_embed/views/snippets.xml`
- `website_lite_vimeo_embed/views/website_templates.xml`
- `website_lite_vimeo_embed/i18n/es.po`

## 9. Plan de rollback
- Revertir los cambios de vistas, assets e i18n del módulo.

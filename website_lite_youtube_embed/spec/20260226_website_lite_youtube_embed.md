# SPEC: Funcionalidades implementadas en `website_lite_youtube_embed`

## 1. Contexto
- Fecha de solicitud: 2026-02-26
- Solicitado por: user
- Alcance: consolidar la especificación funcional y técnica del módulo
  `website_lite_youtube_embed` a partir de las mejoras ya implementadas.

## 2. Objetivos
- Proveer un snippet web configurable para incrustaciones ligeras de YouTube.
- Garantizar que el renderizado funcione tanto en frontend como en el editor.
- Cargar librerías de terceros desde archivos locales del módulo.
- Mantener formato, assets e i18n alineados con las reglas de Trey.

## 3. No objetivos
- No añadir soporte para proveedores distintos de YouTube.
- No rediseñar el comportamiento del editor fuera del snippet del módulo.

## 4. Requisitos funcionales
- El módulo debe ofrecer un snippet reutilizable para páginas Website.
- El vídeo debe quedar centrado en su contenedor visual.
- El JS de opciones del snippet debe cargarse como módulo Odoo válido.
- La librería lite embed debe ser segura ante cargas duplicadas en assets.
- Las traducciones al español deben cubrir los textos visibles del módulo.

## 5. Diseño técnico
- Módulo:
  - `website_lite_youtube_embed`
- Dependencias:
  - `website`
  - `web_editor`
- Assets y plantillas:
  - snippet XML en `views/snippets.xml`
  - assets frontend y wysiwyg desde `static/src/lib/` y `static/src/snippets/`
- Datos y seguridad:
  - sin cambios de seguridad ni modelos

## 6. Plan de validación
- Actualizar el módulo en una base Odoo 16.
- Comprobar el snippet en una página web y en el editor.
- Verificar que no haya errores JS por imports o redefiniciones.
- Verificar que los assets se sirvan desde rutas locales del módulo.

## 7. Riesgos y mitigaciones
- Riesgo: duplicidad de assets en el editor.
  - Mitigación: encapsular y proteger la definición del componente.
- Riesgo: regresiones visuales al centrar el bloque.
  - Mitigación: usar clases estándar y validación manual responsive.

## 8. Entregables
- `website_lite_youtube_embed/views/snippets.xml`
- `website_lite_youtube_embed/static/src/lib/...`
- `website_lite_youtube_embed/static/src/snippets/...`
- `website_lite_youtube_embed/i18n/es.po`

## 9. Plan de rollback
- Revertir los cambios del módulo y volver a cargar assets anteriores.

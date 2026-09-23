# SPEC: Firma de PDFs adjuntos en portal de empleado

## 1. Contexto
- Fecha de solicitud: 2026-05-07
- Alcance: permitir firmar un PDF ya adjunto a una página de conocimiento desde
  el portal de empleado.

## 2. Objetivos
- Añadir una funcionalidad reutilizable para incrustar una firma capturada en
  portal sobre un PDF existente.
- Configurar la firma desde `document.page` con coordenadas numéricas en
  centímetros.
- Permitir elegir una posición automática predefinida para la firma con opción
  `Personalizada` para usar coordenadas manuales.
- Sustituir el PDF original por el PDF firmado.
- Impedir nuevas firmas cuando una página ya está firmada.
- Mantener toda la vertical funcional dentro de `portal_employee`.

## 3. No objetivos
- No implementar selector visual de posición en esta versión.
- No conservar un histórico de PDFs firmados.
- No permitir más de un adjunto en una página firmable.

## 4. Requisitos funcionales
- Una página firmable debe tener exactamente un adjunto PDF.
- La firma se captura con el componente estándar `portal.signature_form`.
- La firma se inserta en la página PDF configurada.
- Tras firmar, se guardan firmante y fecha, y desaparece la acción del portal.
- Las posiciones automáticas actualizan `x` e `y` como referencia de solo
  lectura; la posición personalizada permite editar esos valores.

## 5. Diseño técnico
- Módulo:
  - `portal_employee`
- Backend:
  - campos de configuración y estado en `document.page`
  - mezcla PDF mediante `PyPDF2`, `reportlab` y `Pillow`
  - validaciones controladas con `UserError`
- Portal:
  - ruta JSON `/employee/knowledge/document/<page_id>/sign`
  - botón y modal de firma en la página de conocimiento de empleado

## 6. Plan de validación
- Probar firma correcta con un PDF de una página.
- Probar rechazo de página no firmable.
- Probar rechazo de página ya firmada.
- Probar rechazo con cero, varios o adjuntos no PDF.
- Probar rechazo de coordenadas fuera del tamaño de página.
- Probar actualización de coordenadas de referencia en posiciones automáticas.

## 7. Riesgos y mitigaciones
- Riesgo: coordenadas difíciles de ajustar manualmente.
  - Mitigación: usar centímetros en la interfaz y convertir internamente a
    puntos PDF; dejar preparado el modelo para añadir selector visual después.
- Riesgo: diferencias entre versiones de `PyPDF2`.
  - Mitigación: usar wrappers compatibles con API antigua y nueva.

## 8. Entregables
- Campos, lógica de firma y validaciones dentro de `portal_employee`.
- Tests backend de firma y validaciones.
- Plantillas portal y vista backend.
- Traducciones base en `i18n`.

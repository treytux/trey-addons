# SPEC: Acciones de adjuntos compactas en móvil

## 1. Contexto
- Fecha de solicitud: 2026-06-02
- Alcance: ajustar las acciones de adjuntos en la página de conocimiento del
  portal de empleado para mejorar su visualización en móviles pequeños.

## 2. Objetivos
- Ocultar las etiquetas de texto de los botones de descarga y firma en el
  tamaño más pequeño de móvil.
- Mantener visibles los iconos de acción para conservar la funcionalidad.
- Reutilizar utilidades estándar de Bootstrap 5 sin añadir CSS nuevo.

## 3. No objetivos
- No modificar la lógica de descarga o firma.
- No cambiar la disposición de la tabla de adjuntos.
- No añadir nuevas traducciones ni textos de interfaz.

## 4. Requisitos funcionales
- En pantallas extra pequeñas, los botones deben mostrar solo el icono.
- Desde pantallas `sm` en adelante, los botones deben mostrar icono y texto.

## 5. Diseño técnico
- Módulo:
  - `portal_employee`
- Vista:
  - aplicar `d-none d-sm-inline` a las etiquetas `span` de los botones
    `Download` y `Sign`.

## 6. Plan de validación
- Actualizar el módulo `portal_employee`.
- Abrir una página de conocimiento con adjunto en el portal.
- Verificar en ancho extra pequeño que solo se muestran los iconos.
- Verificar en ancho `sm` o superior que se muestran icono y texto.

## 7. Riesgos y mitigaciones
- Riesgo: el usuario no identifique el botón sin texto en móvil.
  - Mitigación: mantener iconos ya existentes y reconocibles para cada acción.

## 8. Entregables
- Ajuste responsive en la plantilla de portal de conocimiento.

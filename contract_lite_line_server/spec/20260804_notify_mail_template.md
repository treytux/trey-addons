# Corrección de plantilla en notificación de espacio

## Alcance aprobado

Corregir la acción `action_notify_server_space_usage` para que use la
plantilla de correo
`mail_template_contract_lite_line_server_space_usage` al generar la traza del
contrato y las notificaciones a seguidores.

## Diagnóstico

El módulo ya define y permite abrir la plantilla de correo, pero la acción de
notificación construye el asunto y el cuerpo desde Python. Esto impide que los
cambios realizados en la plantilla tengan efecto al pulsar el botón de
notificación.

## Cambios técnicos

- Subir la versión del módulo de `16.0.1.1.0` a `16.0.1.1.1` por cambio de
  lógica Python que requiere reinicio, sin cambios de esquema.
- Obtener la plantilla con `_get_space_notification_template`.
- Renderizar `subject` y `body_html` con `mail.template.generate_email`.
- Mantener el renderizado por idioma usando `template_preview_lang`.
- Lanzar el mismo error funcional cuando la plantilla no exista.
- Eliminar la generación manual de cuerpo y asunto para evitar duplicidad.
- Actualizar README para reflejar que el botón usa la plantilla editable.

## Plan de validación

- Añadir una prueba de regresión que modifica la plantilla en test y valida que
  el contenido personalizado aparece en la traza y en la notificación.
- Ejecutar:
  `oo exec trey_260612 -u contract_lite_line_server --test-enable`
  `--test-tags /contract_lite_line_server --stop-after-init`.

## Resultado de validación

- Suite del módulo en `trey_260612`: 16 tests, 0 fallos, 0 errores.
- `python3 -m compileall` sobre modelos y tests: correcto.
- `msgfmt --check` sobre `i18n/es.po`: correcto.

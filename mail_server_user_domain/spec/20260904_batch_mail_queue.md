# Envío de la cola de correo por lotes

## Resumen

- Objetivo:
  Permitir que la cola de correo procese varios mensajes en una misma llamada
  sin provocar un error de singleton.
- Módulo afectado:
  `mail_server_user_domain`.

## Implementación

- Se prepara cada correo del lote de forma individual para seleccionar su
  servidor SMTP y adaptar remitente y dirección de respuesta cuando proceda.
- Una vez preparados todos los correos, se delega el recordset completo al
  método estándar de Odoo para conservar su agrupación por configuración SMTP.
- Se añade una prueba de regresión con correos que requieren servidores SMTP
  diferentes dentro de una única llamada a `send()`.

## Resultado esperado

El cron de la cola procesa todos los correos seleccionados, asigna a cada uno
su servidor correspondiente y no lanza `Expected singleton` cuando el lote
contiene más de un mensaje.

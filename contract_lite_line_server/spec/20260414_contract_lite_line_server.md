# SPEC: Servidor administrado en líneas de `contract_lite`

## 1. Contexto
- Fecha de solicitud: 2026-04-14
- Solicitado por: user
- Alcance: crear un módulo aislado para registrar datos de servidor
  administrado en líneas de contrato e importar ocupación de disco de los
  servidores.

## 2. Objetivos
- Marcar productos de tipo servicio como servidor.
- Mostrar un bloque de servidor administrado solo en líneas cuyo producto esté
  marcado como servidor.
- Registrar servidor, contenedor, espacio contratado, espacio consumido y línea
  de ampliación de disco en la línea de contrato.
- Mostrar el espacio ampliado de solo lectura desde la cantidad de la línea de
  ampliación seleccionada.
- Mostrar una ampliación sugerida de solo lectura en base a crecimiento
  histórico proyectado a 6 meses, con buffer de seguridad del 10% y
  redondeada al múltiplo de 10 superior.
- Mostrar el saldo de espacio actual de solo lectura para identificar líneas
  con sobreconsumo.
- Actualizar el espacio consumido pegando la salida de ocupación de clientes en
  un asistente disponible desde el listado de contratos.
- Permitir una acción masiva en líneas de contrato para enviar notificación por
  correo y registrar traza en el muro del contrato.

## 3. No objetivos
- No modificar el módulo base `contract_lite`.
- No crear líneas de contrato desde el asistente.
- No recalcular automáticamente el espacio contratado desde la línea de
  ampliación.
- No publicar mensajes en chatter ni guardar histórico permanente del asistente.

## 4. Requisitos funcionales
- Un producto marcado como servidor debe activar el bloque de servidor en sus
  líneas de contrato.
- El bloque debe estar disponible tanto en el formulario standalone de línea
  como en el pop-up de edición desde contrato.
- La línea de ampliación de disco debe seleccionar líneas del mismo contrato,
  excluyendo la línea actual.
- Si hay línea de ampliación seleccionada, debe mostrarse su cantidad como
  `Espacio ampliado (GB)` de solo lectura.
- La ampliación sugerida debe calcularse como:
  capacidad futura necesaria proyectando 6 meses de crecimiento histórico real
  más un buffer del 10%, menos la capacidad actual contratada y ampliada.
- El crecimiento histórico de la ampliación sugerida debe tomar como base los
  meses transcurridos desde la fecha de inicio del contrato si existe en el
  modelo, o desde la fecha de inicio de la línea si el contrato no dispone de
  ese campo.
- La ampliación sugerida debe normalizarse a 0 si no hay necesidad, redondearse
  al múltiplo de 10 superior y aplicar un mínimo de 10GB si el valor es
  positivo.
- El saldo actual debe calcularse como:
  `(espacio contratado + espacio ampliado) - espacio consumido`.
- Debe existir un filtro en búsqueda de líneas de contrato para localizar, en
  una sola vista, líneas servidor con saldo negativo de cualquier contrato.
- El asistente debe procesar líneas `ERROR` y `OK` con formato similar a:
  `[ ERROR ] contenedor: 97G (~97.00G) de 80G (Sin espacio)` y
  `[ OK ] contenedor: 17G (~17.00G) de 20G`.
- El asistente debe extraer el contenedor y el primer valor de ocupación en GB.
- La búsqueda debe hacerse solo sobre líneas de los contratos seleccionados en
  el listado, siempre que esos contratos estén activos y las líneas tengan
  producto servidor y contenedor coincidente.
- Si existen varias líneas activas para el mismo contenedor, deben actualizarse
  todas dentro de los contratos seleccionados.
- El asistente debe informar actualizadas, no encontradas y líneas no
  procesadas.
- El asistente debe ejecutar en dos pasos:
  `Import` para previsualizar y `Apply` para persistir cambios.
- El log del asistente debe listar también los contenedores actualizados,
  valor aplicado y número de líneas afectadas.
- El campo de texto del asistente debe ocupar todo el ancho disponible del
  modal para facilitar el pegado de salidas largas.
- El bloque de registro de importación debe mostrar el título en una línea
  separada y el contenido del log debajo, también a ancho completo.
- Debe existir una acción sobre líneas seleccionadas que:
  - notifique por correo a seguidores del `commercial_partner` y del contrato
  - use una plantilla de email editable desde backend con consumo, capacidad
    total contratada y ampliación sugerida
  - renderice la plantilla en el idioma del partner del contrato de la línea,
    sin depender del idioma individual de cada seguidor
  - publique una copia del mensaje en el chatter del contrato para trazabilidad.
- Debe existir una acción rápida en listado de líneas para abrir la plantilla
  de notificación y permitir su edición desde backend.

## 5. Diseño técnico
- Módulo:
  - `contract_lite_line_server`
- Dependencias:
  - `contract_lite`
  - `product`
- Modelos:
  - `product.template`: campo `is_server`.
  - `contract_lite.line`: campos de servidor administrado.
  - `contract_lite.line.disk_expansion_space_gb`: related readonly a la
    cantidad de `disk_expansion_line_id`.
  - `contract_lite.line.suggested_expansion_gb`: compute readonly con la
    ampliación sugerida en GB.
  - `contract_lite.line.current_space_balance_gb`: compute readonly almacenado
    para filtrar saldo negativo.
  - `contract.lite.line.server.occupation.import.wizard`: asistente de
    importación.
  - `contract_lite.line.action_notify_server_space_usage`: acción masiva de
    notificación por correo con traza en contrato.
  - La notificación usa `template_preview_lang` al renderizar la plantilla para
    forzar el idioma del partner del contrato también cuando la plantilla no
    define un campo `lang`.
  - La acción de notificación renderiza la plantilla editable de correo con
    `mail.template.generate_email`; el contenido no se construye manualmente
    desde Python.
- Vistas:
  - herencia de ficha de producto.
  - herencia de formulario, listado y búsqueda de línea standalone.
  - herencia de formulario y listado de contrato.
  - formulario modal del asistente.
- Seguridad:
  - acceso al asistente para usuarios de facturación.

## 6. Plan de validación
- Instalar o actualizar el módulo:
  `oo exec <db_name> -u contract_lite_line_server --stop-after-init`.
- Ejecutar tests:
  `oo exec <db_name> --test-enable -u contract_lite_line_server`
  `--stop-after-init`.
- Validar manualmente el pop-up de líneas desde contratos con productos
  servidor y no servidor.
- Validar el asistente pegando una salida con líneas `INFO`, `ERROR` y
  `WARNING`.

## 7. Riesgos y mitigaciones
- Riesgo: formato de salida de información de ocupación cambiante.
  - Mitigación: parser tolerante a espacios y decimales con punto o coma.
- Riesgo: contenedores duplicados en contratos no seleccionados.
  - Mitigación: restringir la actualización a `active_ids` del listado.
- Riesgo: selector de ampliación con líneas de otros contratos.
  - Mitigación: dominio por contrato y exclusión de la propia línea.

## 8. Entregables
- `contract_lite_line_server/models/...`
- `contract_lite_line_server/views/...`
- `contract_lite_line_server/wizards/...`
- `contract_lite_line_server/tests/...`
- `contract_lite_line_server/i18n/es.po`

## 9. Plan de rollback
- Desinstalar el módulo para retirar campos, vistas y asistente.
- Si solo se quiere ocultar la funcionalidad temporalmente, retirar permisos
  del asistente o desinstalar el módulo en la base afectada.

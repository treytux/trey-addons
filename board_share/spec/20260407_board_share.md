# SPEC: Compartir tableros en `board_share`

## 1. Contexto
- Fecha de solicitud: 2026-04-07
- Solicitado por: user
- Alcance: permitir compartir una instantanea de `My Dashboard` con usuarios
  concretos en modo sólo lectura.

## 2. Objetivos
- Crear un módulo `board_share` en `addons/trey-addons`.
- Compartir instantáneas fijas del tablero personal.
- Dar acceso a los destinatarios desde un menú propio.

## 3. No objetivos
- No compartir por grupos ni por compañía.
- No sincronizar cambios futuros del tablero origen.
- No modificar el módulo core `board`.

## 4. Requisitos funcionales
- El propietario comparte desde un botón en `My Dashboard`.
- La compartición se guarda con nombre, propietario, destinatarios y vista.
- Los destinatarios abren el tablero compartido en sólo lectura.
- El propietario puede renombrar y archivar la compartición.

## 5. Diseno tecnico
- Modelo nuevo `board.share.dashboard`.
- Wizard nuevo `board.share.wizard`.
- Extensión de `board.board.get_view` para:
  - marcar `My Dashboard` como compartible,
  - controlar acceso a vistas snapshot,
  - forzar modo sólo lectura en snapshots.
- Patch frontend del board para botón `Share` y modo `readonly`.

## 6. Plan de validacion
- Ejecutar tests Python del módulo.
- Verificar acceso de propietario, destinatario y usuario no autorizado.
- Comprobar que renombrar actualiza el título del snapshot.
- Comprobar que archivar deja inaccesible el tablero compartido.

## 7. Riesgos y mitigaciones
- Riesgo: reutilizar `ir.ui.view.custom` rompiendo la inmutabilidad.
  Mitigacion: ignorar personalizaciones al abrir snapshots.
- Riesgo: acceso directo a `view_id`.
  Mitigacion: validar acceso en `board.board.get_view`.

## 8. Entregables
- `board_share/models/...`
- `board_share/wizards/...`
- `board_share/views/...`
- `board_share/tests/...`
- `board_share/i18n/...`

## 9. Plan de rollback
- Desinstalar `board_share`.
- Eliminar snapshots creados y sus vistas asociadas.

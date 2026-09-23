# SPEC: Extensión contractual en `project_current_balance_contract_lite`

## 1. Contexto
- Fecha de solicitud: 2026-03-11
- Solicitado por: user
- Alcance: documentar la extensión del saldo actual de proyecto cuando existe
  una línea válida de `contract_lite`.

## 2. Objetivos
- Extender el cálculo base de saldo con la bolsa del contrato.
- Tener en cuenta facturas pendientes asociadas a la línea contractual.

## 3. No objetivos
- No soportar otros motores de saldo distintos de `contract_lite`.
- No trasladar lógica base al módulo extensión.

## 4. Requisitos funcionales
- Si hay línea contractual válida, el saldo debe partir de la cantidad del
  contrato y restar las horas imputadas del periodo.
- Si existen facturas pendientes asociadas, la bolsa base disponible debe ser
  `0` antes de restar horas.
- El módulo debe aportar los campos de relación contractual y facturas
  pendientes necesarios.

## 5. Diseño técnico
- Módulo:
  - `project_current_balance_contract_lite`
- Dependencias:
  - `project_current_balance`
  - `contract_lite`
  - `account`
- Assets y plantillas:
  - vistas de proyecto y tarea
- Datos y seguridad:
  - campos de contrato, facturas pendientes y periodo de renovación

## 6. Plan de validación
- Instalar o actualizar el módulo.
- Ejecutar los tests del módulo.
- Verificar saldo con y sin facturas pendientes.

## 7. Riesgos y mitigaciones
- Riesgo: recomputaciones incorrectas al cambiar contrato o facturas.
  - Mitigación: ampliar dependencias del compute y validar con tests.

## 8. Entregables
- `project_current_balance_contract_lite/models/...`
- `project_current_balance_contract_lite/views/...`
- `project_current_balance_contract_lite/tests/...`

## 9. Plan de rollback
- Revertir el módulo extensión y volver al cálculo base del saldo actual.

## 10. Actualización 2026-03-25 (i18n)
- Se completa la traducción al español del módulo en
  `i18n/es.po` (cadenas de modelo, ayudas, selecciones y vistas).
- Se validan placeholders y sintaxis PO.
- Resultado esperado:
  - Fichero `es.po` sin entradas vacías para cadenas activas del módulo.

## 11. Actualización 2026-03-25 (facturas futuras y estado pendiente)
- Se ajusta `_compute_pending_invoices` para que `has_pending_invoices` solo
  sea `True` cuando la factura pendiente más antigua tenga fecha menor o igual
  al día actual.
- Si la factura pendiente más antigua es futura:
  - se mantiene `pending_invoices_since` con dicha fecha
  - `has_pending_invoices` pasa a `False`
  - no se fuerza la base del saldo a `0` por esta condición.
- Se añade cobertura de test en
  `tests/test_project_current_balance_contract_lite.py` para validar el caso
  de factura pendiente futura.

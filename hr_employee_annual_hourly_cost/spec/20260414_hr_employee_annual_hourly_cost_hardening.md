# SPEC: Ajustes de coste hora anual por empleado

## 1. Contexto
- Fecha de solicitud: 2026-04-14
- Solicitado por: usuario
- Alcance: módulo `hr_employee_annual_hourly_cost`, tomando como base los
  cambios locales realizados después del último `git pull` del repositorio
  `addons/trey-addons`.

## 2. Objetivos
- Mantener el cálculo de coste hora por periodo con búsquedas compatibles con
  los estándares de formato del proyecto.
- Endurecer la validación de periodos para que los mensajes de error esperados
  queden cubiertos por tests explícitos.
- Ajustar la vista heredada de empleado a las normas XML de Trey para vistas
  heredadas.
- Subir la versión del módulo para aplicar los cambios mediante actualización.

## 3. No objetivos
- No cambiar el modelo funcional de periodos de coste hora por empleado.
- No añadir nuevos campos, menús, permisos o reglas de seguridad.
- No modificar módulos dependientes ni código de Odoo core/OCA.
- No cambiar las traducciones salvo que se refresquen los `.po` por el flujo de
  preparación de MR.

## 4. Requisitos funcionales
- El empleado debe seguir devolviendo el coste del periodo que cubra la fecha
  solicitada.
- Si no existe un periodo anterior que cubra la fecha, debe usarse el siguiente
  periodo disponible.
- Si no existe ningún periodo aplicable, debe usarse el coste hora actual del
  empleado.
- Los periodos no deben solaparse para el mismo empleado.
- Un periodo sin fecha fin solo es válido si empieza en una fecha menor o igual
  a hoy y si es el periodo más reciente del empleado.
- Los errores de validación deben mantener mensajes claros en inglés y quedar
  verificados por tests.

## 5. Diseño técnico
- Módulo:
  - `hr_employee_annual_hourly_cost`
- Dependencias:
  - `hr_hourly_cost`
- Backend:
  - `models/hr_employee.py`: mantener `get_period_hourly_cost` y
    `get_annual_hourly_cost` como APIs de lectura de coste por fecha/año.
  - `models/hr_employee_annual_hourly_cost.py`: conservar la restricción de
    solape y las validaciones para periodos abiertos.
- Vistas:
  - `views/hr_employee_views.xml`: heredar
    `hr_hourly_cost.view_employee_form` sin definir `field name="name"` en el
    registro heredado, siguiendo la regla XML de Trey.
- Datos y seguridad:
  - No se añaden nuevos ficheros de seguridad ni datos maestros.
  - La vista sigue restringiendo la edición/listado de periodos al grupo
    `hr.group_hr_manager`.
- Versionado:
  - `__manifest__.py` pasa de `16.0.1.0.0` a `16.0.1.1.0` para reflejar que la
    vista debe actualizarse con `-u hr_employee_annual_hourly_cost`.

## 6. Plan de validación
- Actualizar el módulo:
  - `oo exec <db_name> -u hr_employee_annual_hourly_cost --stop-after-init`
- Ejecutar tests del módulo:
  - `oo exec <db_name> -u hr_employee_annual_hourly_cost --test-enable --stop-after-init`
- Comprobaciones manuales:
  - Abrir la ficha de empleado como usuario de RR. HH. manager.
  - Verificar que el listado editable de periodos aparece tras `Hourly Cost`.
  - Crear periodos cerrados no solapados y comprobar que se guardan.
  - Intentar crear un periodo solapado y confirmar el error esperado.
  - Intentar crear un periodo abierto con inicio futuro y confirmar el error
    esperado.
- Tests automatizados:
  - Coste por fecha dentro de un periodo.
  - Fallback al coste hora actual.
  - Uso del siguiente periodo disponible.
  - Periodo abierto válido hasta hoy.
  - Rechazo de solapes.
  - Rechazo de periodo abierto futuro.
  - Rechazo de periodo abierto que no sea el más reciente.

## 7. Riesgos y mitigaciones
- Riesgo: la comparación de periodos abiertos usa la fecha actual, por lo que
  los tests que dependan de `fields.Date.today()` deben evitar fechas fijas que
  puedan quedar obsoletas.
  Mitigación: mantener los tests con fechas relativas cuando validen periodos
  abiertos.
- Riesgo: los tests comparan textos exactos de `ValidationError`.
  Mitigación: si cambia una cadena de usuario, actualizar tests e i18n en el
  mismo cambio.
- Riesgo: la actualización de vista requiere `-u`.
  Mitigación: documentar el comando de actualización del módulo en el MR.

## 8. Entregables
- `__manifest__.py`: incremento de versión.
- `models/hr_employee.py`: formato de llamadas ORM sin cambio funcional.
- `models/hr_employee_annual_hourly_cost.py`: limpieza de validación redundante.
- `views/hr_employee_views.xml`: ajuste de vista heredada.
- `tests/test_hr_employee_annual_hourly_cost.py`: assertions de mensajes de
  validación y formato de tests.
- `spec/20260414_hr_employee_annual_hourly_cost_hardening.md`: especificación
  técnica del cambio.

## 9. Plan de reversión
- Revertir los cambios del módulo `hr_employee_annual_hourly_cost`.
- Restaurar la versión anterior `16.0.1.0.0` si el cambio no se ha desplegado.
- Actualizar de nuevo el módulo en la base afectada para regenerar la vista con
  la versión revertida si ya se aplicó el despliegue.

## 10. Plan de ejecución por fases
- Fase 1: congelar esta spec y confirmar el alcance de los cambios locales.
- Fase 2: validar backend y restricciones del modelo.
- Fase 3: validar vista heredada de empleado.
- Fase 4: ejecutar tests y revisión de calidad.
- Fase 5: refrescar i18n si el MR incluye cambios de cadenas.

## 11. Briefs para subagentes
- Backend: revisar `models/hr_employee.py` y
  `models/hr_employee_annual_hourly_cost.py`; confirmar que el cálculo de coste
  por fecha y las restricciones de solape se mantienen sin regresiones.
- Frontend: revisar `views/hr_employee_views.xml`; confirmar que la herencia de
  vista no define `field name="name"` y que el campo `annual_hourly_cost_ids`
  sigue apareciendo tras `Hourly Cost`.
- QA: ejecutar los tests del módulo y auditar que los casos cubren periodo
  aplicable, fallback, periodo abierto, solapes y mensajes de error.
- i18n: si se regeneran traducciones, comprobar que las cadenas nuevas o
  modificadas de errores se mantienen en inglés en origen y que los `.po`
  respetan el glosario del proyecto.

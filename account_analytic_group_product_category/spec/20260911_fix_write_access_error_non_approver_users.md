# Corrección: AccessError al asignar grupo analítico como usuario no aprobador

## Alcance aprobado

Corregir el `AccessError` ("No puede acceder a partes de horas que no son
propios.") que se produce al validar un albarán con cuenta analítica
asignada, cuando el usuario que valida no pertenece al grupo
`hr_timesheet.group_hr_timesheet_approver` ("Usuario: todos los partes de
horas").

## Diagnóstico técnico

`hr_timesheet` (módulo core) sobrescribe `AccountAnalyticLine.write()`
(`server/addons/hr_timesheet/models/hr_timesheet.py:204-207`) con una
comprobación incondicional que no distingue si la línea es realmente un
parte de horas (`project_id` presente) o no:

```python
def write(self, values):
    if not (self.user_has_groups('hr_timesheet.group_hr_timesheet_approver')
            or self.env.su) \
            and any(self.env.user.id != line.user_id.id for line in self):
        raise AccessError(_("You cannot access timesheets that are not yours."))
```

Esta instancia reutiliza `account.analytic.line` para costes de stock/venta
(vía `stock_picking_analytic_custom` y `stock_picking_analytic_from_sale`),
donde las líneas no tienen `project_id` ni `user_id` igual al operario que
valida el albarán.

El disparador real **no es la creación de la línea en sí**: `create()` de
`hr_timesheet` solo actúa si hay `project_id`, así que no bloquea la
creación de estas líneas. El problema lo generaba
`_assign_group_from_product_category()` (versión anterior de este módulo),
que tras `create()` hacía `line.group_id = group` — una escritura adicional
e innecesaria sobre el registro recién creado. Esa segunda llamada a
`write()` es la que cae en el guard de `hr_timesheet` y aborta toda la
transacción de `button_validate()` (el albarán revierte a su estado
previo).

Reproducido en shell (rollback) con un usuario real sin el grupo aprobador
(`dvaduva@mercadoit.com`) sobre un albarán real (`WH/OUT/29664`): el error
era idéntico, carácter por carácter, al reportado en producción.

Se descartó corregirlo con `sudo()` en esa escritura (enfoque evaluado
inicialmente): aunque habría evitado el error, seguía generando una
escritura innecesaria que se salta deliberadamente una protección de
seguridad del core. La corrección elegida evita generar esa escritura en
absoluto.

No se modifica `hr_timesheet` (módulo core): es mala práctica editar
código de terceros directamente, se perdería en la próxima actualización
del módulo.

## Cambios previstos

- `models/account_analytic_line.py`:
  - `create()` ahora resuelve el grupo a partir de los `vals` (mirando
    `product_id` o, en su defecto, el producto del `stock_move_id`) e
    inyecta `group_id` en el propio diccionario de creación, antes de
    llamar a `super().create(vals_list)`. La línea nace ya con el grupo
    correcto en el mismo `INSERT`; no hay ningún `write()` posterior, por
    lo que el guard de `hr_timesheet` nunca se ejecuta para el camino de
    creación.
  - Nuevos métodos auxiliares `_product_from_vals()` y
    `_group_from_product()`, reutilizados tanto por `create()` como por
    `_get_group_from_product_category()` (usado por el camino de
    `write()`, sin cambios de comportamiento).
  - `write()` y `_assign_group_from_product_category()` quedan **sin
    cambios**: cuando `product_id`/`stock_move_id` cambian en una línea ya
    existente, se sigue usando `line.group_id = group` tal cual. Ese
    camino no interviene en el bug reportado (confirmado: validar un
    albarán solo pasa por `create()`, nunca reescribe `product_id` en una
    línea ya creada) y mantiene la protección de `hr_timesheet` intacta
    para ediciones manuales reales de una línea existente.
- `__manifest__.py`: versión `16.0.1.0.0` -> `16.0.1.0.1` (cambio Python
  puro, sin tocar tablas/campos, solo requiere reinicio).
- `tests/test_account_analytic_group_product_category.py`: nuevo test
  `test_create_group_as_non_approver_does_not_raise_access_error`, que
  crea una línea vía `create()` como un usuario sin ningún grupo de
  `hr_timesheet` (solo `analytic.group_analytic_accounting` +
  `project.group_project_user`, necesario únicamente para sortear un
  chequeo de acceso a `project.task` de `project_timesheet_holidays`
  ajeno a este bug) y confirma que no lanza `AccessError` y que el grupo
  se asigna correctamente. El test se salta (`skipTest`) si `hr_timesheet`
  no está instalado, ya que es una interacción cruzada entre módulos y
  este addon no depende de `hr_timesheet`.

## Áreas impactadas

- Backend:
  - `models/account_analytic_line.py`
  - `__manifest__.py`
- Tests:
  - `tests/test_account_analytic_group_product_category.py`
    (`test_create_group_as_non_approver_does_not_raise_access_error`)
- Seguridad:
  - Sin cambios en ACL/`ir.rule` ni uso de `sudo()`. El fix no se salta
    ninguna comprobación de seguridad: evita generar la escritura que la
    activaba innecesariamente.

## Plan de pruebas

Validación automática (nota: el resto de la suite de este módulo falla
actualmente en `mercadoit090926_copy` por un problema de entorno ajeno a
este cambio — `product_template.sale_line_warn` viola `NOT NULL` al crear
cualquier `product.product` en `setUp()` — a resolver aparte):

```bash
oo exec <db> -u account_analytic_group_product_category \
  --test-enable --stop-after-init
```

Validación manual:

- Con un usuario que NO tenga el grupo "Partes de horas: Usuario, todos
  los partes de horas", validar un albarán con cuenta analítica asignada
  cuyo producto resuelva a un grupo analítico vía categoría.
- Confirmar que el albarán queda en estado `Listo`/`Hecho` sin el
  `AccessError`, y que la línea analítica creada tiene el `group_id`
  correcto.
- Regresión: confirmar que un parte de horas real (`project_id` presente)
  sigue lanzando `AccessError` cuando un usuario no aprobador intenta
  editar un parte de horas ajeno (el camino de `write()` no se ha
  tocado).

Validado en shell (rollback, sin persistir) contra dos albaranes reales
que reprodujeron el fallo en producción (`WH/OUT/29663`, `WH/OUT/29664`,
usuario `dvaduva@mercadoit.com`): ambos validan correctamente tras el
fix, con el `group_id` de la línea analítica bien asignado.

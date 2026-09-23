# Especificación funcional completa

## 1. Objetivo del módulo

El módulo `project_task_sale_order_stock` permite generar pedidos de venta
desde tareas de proyecto a partir de horas imputadas y materiales consumidos,
manteniendo trazabilidad con las líneas de venta creadas y evitando que un
mismo parte de horas o material se facture más de una vez.

Además, amplía el asistente de creación de tareas para que, cuando proceda,
se pueda crear automáticamente el pedido de venta asociado, confirmarlo,
gestionar el albarán derivado y tratar de facturarlo.

## 2. Dependencias funcionales

El módulo se apoya en los siguientes módulos:

- `hr_timesheet`
- `project_task_material`
- `sale_stock`
- `sale_timesheet`

## 3. Alcance funcional

La funcionalidad cubierta por el módulo se divide en dos flujos principales:

1. Creación manual de pedido de venta desde una tarea ya existente.
2. Creación de tarea mediante asistente con automatización posterior de venta,
   logística y facturación.

## 4. Extensiones del modelo de datos

### 4.1. Tarea (`project.task`)

Se añaden o utilizan los siguientes comportamientos:

- Relación con los pedidos de venta creados desde la tarea.
- Cómputos para mostrar el número de pedidos, albaranes y movimientos de stock
  relacionados.
- Campo `destination_location_id` para indicar la ubicación de destino usada
  en la lógica de almacén.
- Validaciones para determinar si la tarea puede generar un nuevo pedido de
  venta.

### 4.2. Partes de horas (`account.analytic.line`)

Cada parte de horas incorpora el campo:

- `sale_order_line_id` (`Many2one` a `sale.order.line`)

Este campo enlaza el parte con la línea de pedido de venta generada desde la
tarea. Su propósito es:

- Trazar qué parte ya se ha pasado a venta.
- Evitar duplicidades en nuevas creaciones de pedido.

### 4.3. Materiales de tarea (`project.task.material`)

Cada línea de material incorpora los campos:

- `sale_order_line_id` (`Many2one` a `sale.order.line`)
- `lot_id` (`Many2one` a `stock.lot`)

El campo `sale_order_line_id` permite la misma trazabilidad y control de
duplicidad que en horas. El campo `lot_id` se usa únicamente en el asistente
de creación de tarea para poder reservar y transferir el lote indicado cuando
se genera albarán.

## 5. Flujo 1: creación manual de pedido desde la tarea

### 5.1. Condiciones para permitir la acción

Desde la tarea existe una acción para crear pedido de venta sólo cuando se
cumplen las validaciones de negocio:

- La tarea tiene cliente asignado, o existe una vía válida para determinarlo.
- La tarea dispone de horas pendientes de vender y/o materiales pendientes de
  vender.
- No todos los partes y materiales ya están enlazados a una línea de venta
  mediante `sale_order_line_id`.

### 5.2. Selección de líneas a vender

Al abrir el asistente `project.task.create.sale.order`, se precargan líneas
pendientes generadas a partir de:

- Partes de horas sin `sale_order_line_id`.
- Materiales con cantidad positiva y sin `sale_order_line_id`.

### 5.3. Creación del pedido

Al confirmar el asistente:

1. Se crea el pedido de venta para el cliente de la tarea.
2. Se asigna el almacén calculado para la tarea a partir de
   `destination_location_id` cuando aplique.
3. Se crean las líneas de pedido correspondientes a horas y materiales.
4. Se rellenan los campos `sale_order_line_id` de los partes de horas y de los
   materiales que hayan pasado al pedido.
5. Se enlaza el pedido con la tarea.

### 5.4. Prevención de duplicidades

Una vez que horas o materiales tienen informado `sale_order_line_id`, dejan de
ser candidatos para nuevas ventas desde la misma tarea. Si se intenta volver a
crear el pedido, el asistente no debe generar nuevas líneas para dichos
registros ya transferidos.

### 5.5. Restricción sobre lotes en este flujo

Cuando el pedido se crea manualmente desde una tarea existente, no se debe
informar lote en la propia tarea para este proceso, ya que en este flujo no se
automatiza la creación ni la transferencia del albarán desde la interfaz de la
tarea.

## 6. Flujo 2: asistente "Crear tarea"

### 6.1. Propósito

El asistente `create.project.task` permite crear una tarea y, si la información
introducida lo requiere, ejecutar automáticamente el flujo posterior de venta,
stock y facturación.

### 6.2. Mensaje informativo al usuario

El asistente muestra un texto explicativo indicando que la tarea:

- Creará un pedido de venta automáticamente.
- Confirmará el pedido automáticamente.
- Creará albarán si aplica.
- Intentará crear la factura.

### 6.3. Ubicación de destino y almacén

El campo `destination_location_id` del asistente se utiliza para localizar el
almacén que cubre dicha ubicación y asignarlo al pedido de venta generado.

La intención funcional es:

- Tomar la ubicación indicada por el usuario.
- Buscar el almacén cuya ubicación vista contenga esa ubicación.
- Asignar ese almacén al pedido de venta para que el flujo logístico use la
  estructura correcta.

### 6.4. Gestión de materiales y lotes

Si la tarea se crea con materiales:

- El pedido de venta generado se confirma automáticamente.
- Si la confirmación crea albarán, se intentan asignar los lotes indicados por
  el usuario en el asistente a las líneas de stock correspondientes.
- La selección de lote se limita mediante dominio para mostrar sólo lotes del
  producto de la línea.

### 6.5. Validación previa de stock

Antes de aceptar el asistente se valida que exista stock suficiente de los
productos y lotes indicados para poder completar el flujo logístico.

La validación debe comprobar:

- Disponibilidad del producto en la ubicación/almacén correspondiente.
- Disponibilidad del lote concreto cuando se haya informado lote.

Si no hay stock suficiente, no se continúa con el proceso y se muestra un
aviso al usuario.

### 6.6. Confirmación y transferencia del albarán

Cuando el pedido confirmado genera albarán:

1. El albarán se confirma.
2. Se reservan las cantidades.
3. Se informan los lotes cuando proceda.
4. Se valida la transferencia para dejar la entrega completada.

## 7. Facturación automática

Tras la creación y confirmación del pedido de venta, el módulo intenta generar
la factura automáticamente.

### 7.1. Resultado esperado

Si la política de facturación del pedido y de sus productos lo permite, el
pedido debe quedar facturado automáticamente.

### 7.2. Comportamiento ante fallo de facturación

Si la factura no puede crearse de forma automática:

- No se debe interrumpir con una excepción funcional.
- Debe mostrarse un aviso al usuario indicando que la facturación no se ha
  podido completar.
- El resto del flujo ya ejecutado debe conservarse: tarea creada, pedido
  creado, confirmación realizada y albarán procesado si correspondía.

## 8. Interfaz de usuario

### 8.1. Tarea

En la tarea se muestran:

- Acción para crear pedido de venta.
- Botones inteligentes para pedidos, albaranes y movimientos.
- `destination_location_id`.
- Campo `sale_order_line_id` en horas, en sólo lectura.
- Campo `sale_order_line_id` en materiales, en sólo lectura.

### 8.2. Asistente de pedido desde tarea

El asistente muestra las líneas a trasladar a venta, pero no necesita mostrar
en edición los campos de trazabilidad ya existentes en la tarea.

### 8.3. Asistente de creación de tarea

El asistente permite introducir:

- Datos generales de la tarea.
- Partes de horas.
- Materiales.
- Lotes en líneas de materiales, con dominio por producto.
- Ubicación de destino.

## 9. Trazabilidad funcional

La trazabilidad principal del módulo se basa en:

- La relación entre tarea y pedidos de venta creados desde ella.
- El campo `sale_order_line_id` en horas.
- El campo `sale_order_line_id` en materiales.

Gracias a ello se puede identificar:

- Qué información de la tarea ya ha sido vendida.
- Qué líneas de venta proceden de horas o materiales concretos.
- Qué registros siguen pendientes de pasar a venta.

## 10. Reglas de negocio relevantes

- No se deben usar consultas SQL para esta funcionalidad.
- La lógica debe apoyarse en ORM de Odoo.
- Las líneas ya enlazadas mediante `sale_order_line_id` no deben volver a
  venderse.
- Los lotes sólo deben ofrecerse para el producto correspondiente.
- Si no hay stock suficiente, el asistente de creación de tarea debe avisar y
  no continuar.
- Si falla la facturación automática, debe emitirse aviso sin deshacer el resto
  del proceso.

## 11. Cobertura de pruebas esperada

El módulo debe contar con pruebas que validen, al menos:

- Creación de pedido desde tarea con horas.
- Creación de pedido desde tarea con materiales.
- Relleno de `sale_order_line_id` al crear el pedido.
- Prevención de duplicidades en nuevas ejecuciones.
- Creación de tarea con generación automática de pedido.
- Confirmación del pedido y tratamiento del albarán.
- Asignación de lotes cuando existan materiales.
- Facturación automática cuando el escenario lo permita.
- Aviso cuando no haya stock suficiente.
- Aviso cuando no sea posible facturar automáticamente.

## 12. Resultado funcional esperado

El comportamiento global esperado del módulo es que una tarea pueda actuar como
origen comercial y logístico controlado, permitiendo vender horas y materiales
de forma trazable, evitando duplicidades y automatizando al máximo el flujo de
pedido, entrega y facturación cuando la creación se hace desde el asistente de
tareas.

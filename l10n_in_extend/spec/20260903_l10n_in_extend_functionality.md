# SPEC: Funcionalidad de l10n_in_extend

## 1. Contexto

- Fecha de solicitud: 2026-09-03
- Módulo objetivo: `l10n_in_extend`
- Ubicación: `addons/trey-addons/l10n_in_extend`
- Tipo: documentación funcional y técnica de la implementación existente.

El módulo amplía la localización india estándar de Odoo 16 (`l10n_in`) con
datos de transporte para documentos comerciales y con una asignación de
impuestos GST basada en el código HS del producto y en el estado fiscal de las
partes.

## 2. Objetivos funcionales

1. Registrar datos de transporte en pedidos de venta, pedidos de compra y
   facturas.
2. Copiar esos datos desde el pedido origen a la factura generada.
3. Añadir una tasa GST al código HS para que el producto aporte la base del
   cálculo fiscal.
4. Determinar automáticamente CGST/SGST o IGST en operaciones indias según
   los TIN de los estados de la compañía y del cliente o proveedor.
5. Mantener el cálculo estándar de Odoo para operaciones fuera de India.

## 3. Alcance y dependencias


### Modelos afectados

| Modelo | Responsabilidad |
| --- | --- |
| `hs.code` | Almacena la tasa GST en `rate`. |
| `sale.order` | Registra los datos de transporte y los prepara para factura. |
| `purchase.order` | Registra los datos de transporte y los prepara para factura. |
| `account.move` | Conserva los datos de transporte en facturas. |
| `sale.order.line` | Recalcula impuestos de venta en pedidos indios. |
| `purchase.order.line` | Recalcula impuestos de compra en pedidos indios. |
| `account.move.line` | Calcula impuestos en facturas y rectificativas indias. |
| `res.country.state` | Expone el TIN de India para facilitar su mantenimiento. |

## 4. Datos de transporte

### Campos

Los modelos `sale.order`, `purchase.order` y `account.move` incorporan los
siguientes campos de texto:

| Campo técnico | Etiqueta | Finalidad |
| --- | --- | --- |
| `transport_mode` | Transport Mode | Medio utilizado para el transporte. |
| `vehicle_number` | Vehicle Number | Identificador del vehículo. |
| `supply_date` | Date Supply | Fecha de suministro. |
| `supply_place` | Place to Supply | Lugar de suministro. |

### Interfaz y flujo

Las vistas de formulario de pedidos de venta, pedidos de compra y facturas
añaden la pestaña `Indian Transport`, que muestra los cuatro campos.

Al crear una factura desde un pedido, los métodos `_prepare_invoice()` de
`sale.order` y `purchase.order` incluyen los cuatro valores en el diccionario
de creación de factura. La factura conserva así la información indicada en el
documento de origen.

## 5. Configuración de impuestos GST

1. En *Inventario > Configuración > Códigos HS*, informar `Rate` para cada
   código HS que se use en operaciones indias.
2. Asignar un código HS a cada producto aplicable.
3. Configurar el país India y un estado con TIN en la compañía india.
4. Configurar el país India y un estado con TIN en cada cliente o proveedor
   indio.
5. Instalar o actualizar la plantilla contable india para generar los
   impuestos adicionales definidos por el módulo.

La vista de producto oculta los campos HSN estándar de `l10n_in` para evitar
duplicar la información frente al código HS utilizado por este módulo. Las
vistas de estados muestran `l10n_in_tin` para facilitar la configuración.

## 6. Regla de cálculo GST

La regla se aplica al recalcular impuestos en líneas de pedido y al obtener los
impuestos calculados de una línea de factura. Afecta a facturas de cliente,
abonos de cliente, facturas de proveedor y abonos de proveedor; no modifica
otros tipos de asiento.

| Condición | Resultado |
| --- | --- |
| Compañía con país distinto de India | Se conserva el cálculo estándar de Odoo. |
| Partner con país distinto de India | Se conserva el cálculo estándar de Odoo. |
| Compañía y partner indios con el mismo `l10n_in_tin` | Se buscan CGST y SGST del tipo de uso y del 50% de `rate`. |
| Compañía y partner indios con distinto `l10n_in_tin` | Se busca IGST del tipo de uso y del 100% de `rate`. |
| Código HS con `rate = Nil` | Se mantiene el resultado estándar sin sustituir impuestos. |

Para ventas y documentos de cliente se buscan impuestos con
`type_tax_use = sale`; para compras y documentos de proveedor, con
`type_tax_use = purchase`. Las búsquedas se basan en el importe, el tipo de
uso y el nombre del impuesto (`CGST`, `SGST` o `IGST`). En facturas también se
filtra por la compañía del documento.

Las búsquedas por nombre usan el operador ORM `=ilike` con los patrones
`%CGST%`, `%SGST%` y `%IGST%`. Por tanto, localizan las cadenas indicadas sin
distinguir mayúsculas, minúsculas ni combinaciones de ambas.

## 7. Validaciones y mensajes

En una operación aplicable a India se bloquea el cálculo con `UserError` si:

- la compañía o el cliente no tiene estado, en venta y factura de cliente;
- la compañía o el proveedor no tiene estado, en compra y factura de
  proveedor;
- el producto no tiene código HS.

Los mensajes actuales son `Please, set state in customer and state in
company.`, `Please, set state in vendor and state in company.` y `Please, set
HS Code in product.`. Están incluidos en las traducciones españolas del
módulo.

## 8. Datos fiscales

`data/account_tax_data.xml` define el grupo `india_tax_group` y plantillas de
impuestos GST adicionales para la plantilla contable india. Estas plantillas
complementan los tipos que aporta `l10n_in` y deben generar impuestos de venta
y de compra con nombres que permitan su localización por la regla anterior.

## 9. Pruebas existentes y criterios de aceptación

### Transporte

- Los cuatro campos existen en facturas, pedidos de venta y pedidos de compra.
- Los valores introducidos en un pedido de venta se incluyen en
  `sale.order._prepare_invoice()`.
- Los valores introducidos en un pedido de compra se incluyen en
  `purchase.order._prepare_invoice()`.

### GST

- Las operaciones con compañía o partner no indio mantienen sus impuestos
  estándar.
- En venta y compra, el mismo TIN aplica CGST y SGST; un TIN distinto aplica
  IGST.
- En factura se validan los mismos escenarios para documentos de cliente y de
  proveedor.
- Las búsquedas de CGST, SGST e IGST funcionan con cualquier combinación de
  mayúsculas y minúsculas en el nombre del impuesto.
- La falta de estado o de código HS genera el error correspondiente.
- La tasa `Nil` conserva los impuestos estándar.

Los casos anteriores están cubiertos por:

- `tests/test_l10n_in_extend.py`
- `tests/test_l10n_in_extend_taxes.py`

La validación debe ejecutarse contra una base de datos de pruebas que tenga
instaladas las dependencias y los datos demo de `l10n_in`:

## 10. Riesgos y aspectos a revisar

- `rate` es un campo de texto. Los valores distintos de `Nil` deben ser
  numéricos y usar un formato convertible a `float` para evitar errores de
  cálculo.
- La localización de impuestos por nombre depende de las cadenas `CGST`,
  `SGST` e `IGST`; un cambio de nomenclatura puede impedir encontrarlos.
- Las líneas de pedido buscan impuestos sin filtrar explícitamente por
  compañía, mientras que las líneas de factura sí lo hacen. En entornos
  multiempresa conviene validar que no se seleccionen impuestos de otra
  compañía.
- `supply_date` es actualmente texto, no un campo `Date`; no existe validación
  de formato ni de obligatoriedad.
- Los impuestos con tasa `Nil` no se limpian: se conserva el resultado que
  hubiera asignado el cálculo estándar de Odoo.

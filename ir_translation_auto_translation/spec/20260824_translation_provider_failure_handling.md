# Evitar guardar errores del proveedor como traducciones

## Alcance aprobado

Corregir el comportamiento del modulo `ir_translation_auto_translation`
cuando el proveedor externo de traduccion falla durante una traduccion
individual o masiva.

El caso analizado afecta especialmente a campos traducibles de
`product.template`, como `name` y `warranty`, donde una traduccion fallida
puede terminar almacenando el mismo texto en varios idiomas.

## Diagnostico tecnico

El proveedor `GoogletransProvider` devolvia el texto origen despues de agotar
los reintentos ante errores de red, timeout, limites del servicio u otras
excepciones de `deep-translator`.

El helper interpretaba cualquier cadena devuelta como una traduccion valida y
la guardaba mediante `update_field_translations()`. Por tanto, un fallo del
servicio quedaba indistinguible de una traduccion correcta:

```text
origen:  Garantia de por vida.
es_ES:   Garantia de por vida.
de_DE:   Garantia de por vida.
```

La auditoria realizada en la base `mercadoit_copia` sobre
`product.template.warranty` confirmo el efecto:

- 4.450 productos contienen texto real en `warranty`.
- Solo 86 productos tienen terminos registrados en `ir_translation`.
- Los 131 terminos registrados por idioma eran identicos al origen en
  `es_ES` y `de_DE`.

## Cambios realizados

- Modificar `models/googletrans_provider.py` para que:
  - lance una excepcion despues de agotar los reintentos;
  - no devuelva el texto origen cuando falla la traduccion;
  - rechace resultados no textuales o vacios;
  - fuerce al menos un intento aunque la configuracion indique cero reintentos;
  - aplique la misma politica de errores a `translate_batch()`.
- Mantener el uso del `savepoint` existente en
  `models/ir_translation_helper.py`: la excepcion se registra como error y no
  se persiste ninguna traduccion destino.
- Anadir pruebas de regresion para los fallos del proveedor y de la traduccion
  en bloque en `tests/test_ir_translation_auto_translation.py`.

No se modifican traducciones ya almacenadas ni se realiza una reparacion
automatica de los productos afectados por esta especificacion.

## Areas impactadas

- Backend:
  - `models/googletrans_provider.py`
  - `models/ir_translation_helper.py` (comportamiento existente de
    `savepoint` y captura de errores)
- Tests:
  - `tests/test_ir_translation_auto_translation.py`
- Frontend:
  - Sin cambios.
- Seguridad:
  - Sin cambios en ACL ni reglas.
- Datos:
  - No se ejecutan escrituras sobre productos ni traducciones existentes.
- i18n:
  - No se anaden cadenas visibles nuevas.

## Plan de pruebas

Validacion estatica:

```bash
git diff --check
python3 -m py_compile \
  models/googletrans_provider.py \
  tests/test_ir_translation_auto_translation.py
```

Pruebas funcionales del proveedor:

```bash
odoo-bin -c /var/lib/odoo/mercadoit16/odoo-server.conf \
  -d mercadoit_copia --test-enable \
  --test-tags ir_translation_auto_translation:TestGoogletransProvider \
  --stop-after-init
```

La validacion estatica se completo correctamente. La ejecucion de Odoo no se
pudo completar en el entorno de desarrollo porque falta la dependencia Python
`PyPDF2`.

## Riesgos y notas

- Una respuesta del proveedor que sea exactamente igual al origen puede ser
  valida para nombres propios, referencias o marcas. Por ese motivo la
  correccion no trata cualquier igualdad como error; solo evita guardar
  respuestas que el proveedor haya obtenido mediante su ruta de fallo.
- Los productos afectados por ejecuciones anteriores deben localizarse y
  reprocesarse separadamente, despues de revisar las traducciones existentes.
- Para traducciones masivas grandes sigue siendo recomendable procesar por
  lotes reanudables y controlar los limites del proveedor externo.

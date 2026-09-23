# SPEC: Añadir códigos de cliente al `supercode`

## 1. Contexto
- Fecha de solicitud: 2026-07-16
- Solicitado por: user
- Alcance: alinear `product_supercode_search` con el módulo de referencia
  de la 12.0, que agrega también códigos de cliente
  (`product.customerinfo` vía `customer_ids`).

## 2. Objetivos
- Que `supercode` agregue también, además de proveedores, los datos de
  cliente: nombre del contacto, `ref` del contacto y `product_code` de
  cada `product.customerinfo` asociado.
- Mantener el mismo criterio ya usado con proveedores: en
  `product.template` se agregan todos los `customer_ids`; en
  `product.product` solo los específicos de esa variante
  (`product_id == product`), heredando además los genéricos vía
  `product_tmpl_id.supercode`.

## 3. No objetivos
- No se reimplementa `product.customerinfo` desde cero; se reutiliza el
  modelo que ya provee el módulo OCA `product_supplierinfo_for_customer`
  (repo `product-attribute`, ya vendorizado en el entorno), que hereda de
  `product.supplierinfo` y añade `customer_ids` /
  `variant_customer_ids` sobre `product.template`.
- No se modifica el comportamiento de precios/`name_search` que aporta
  ese módulo OCA; solo se consume el modelo y el campo `customer_ids`.

## 4. Requisitos funcionales
- `product.template`: `_compute_supercode` agrega, por cada registro en
  `customer_ids.filtered('partner_id')`, el nombre del contacto, su
  `ref` y su `product_code`; el recálculo se dispara con
  `@api.depends` sobre `customer_ids.product_code`,
  `customer_ids.partner_id.name` y `customer_ids.partner_id.ref`.
- `product.product`: mismo agregado pero filtrado a
  `customer.product_id == product`, con el mismo patrón de `@api.depends`
  ya usado para `seller_ids`.

## 5. Diseño técnico
- Módulo:
  - `product_supercode_search`
- Nueva dependencia:
  - `product_supplierinfo_for_customer` (OCA, repo `product-attribute`),
    que aporta el modelo `product.customerinfo` y el campo
    `customer_ids` en `product.template` (delegado también a
    `product.product` por herencia `_inherits`).
- Cambios de código:
  - `models/product_template.py`: ampliar `@api.depends` y el bucle de
    agregación con `customer_ids`.
  - `models/product_product.py`: ampliar `@api.depends` y el bucle de
    agregación con `customer_ids` filtrados por variante.
- Manifest:
  - Añadir `product_supplierinfo_for_customer` a `depends`.
  - Bump de versión `16.0.1.0.0` -> `16.0.1.1.0` (cambio de
    `@api.depends`/contenido de un campo `store=True` existente,
    requiere `-u` del módulo).
- Vistas: sin cambios (la búsqueda ya filtra por `supercode`).
- Datos y seguridad: sin ACL nuevas propias; se reutilizan las del
  módulo `product_supplierinfo_for_customer` para
  `product.customerinfo`.

## 6. Plan de validación
- Actualizar el módulo (`-u product_supercode_search`) para que se
  recalculen los `supercode` existentes con la nueva dependencia.
- Crear un `product.customerinfo` en una plantilla y comprobar que
  `template.supercode` incluye nombre, `ref` y `product_code` del
  cliente.
- Crear un `product.customerinfo` específico de una variante
  (`product_id` informado) y comprobar que aparece en el `supercode` de
  esa variante.
- Ejecutar los tests del módulo, incluidos los dos nuevos:
  `test_template_supercode_includes_customer` y
  `test_product_supercode_customer_specific`.

## 7. Riesgos y mitigaciones
- Riesgo: nueva dependencia dura a un módulo OCA no instalado
  previamente en todas las bases de datos.
  - Mitigación: `product_supplierinfo_for_customer` ya está disponible
    en el path de addons (`product-attribute`); se instalará junto con
    `product_supercode_search` al declarar la dependencia en el
    manifest.
  - Confirmado con el usuario antes de aplicar el cambio.
- Riesgo: tras el `-u`, los `supercode` ya calculados no reflejan los
  clientes existentes hasta que Odoo recalcule el campo.
  - Mitigación: `-u` fuerza el recálculo de campos `store=True` cuyas
    dependencias han cambiado; no se requiere script de migración
    adicional.

## 8. Entregables
- `product_supercode_search/__manifest__.py` (nueva dependencia y
  versión).
- `product_supercode_search/models/product_template.py`
- `product_supercode_search/models/product_product.py`
- `product_supercode_search/tests/test_product_supercode_search.py`
- `product_supercode_search/README.rst`

## 9. Plan de rollback
- Revertir los cambios de `@api.depends`/compute en ambos modelos y
  quitar `product_supplierinfo_for_customer` de `depends`.
- Bajar la versión o publicar una nueva que restaure el comportamiento
  anterior (solo proveedores) y actualizar el módulo de nuevo.

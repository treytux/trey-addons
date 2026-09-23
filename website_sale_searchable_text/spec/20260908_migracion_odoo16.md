# Migración a Odoo 16

## 1. Contexto
- Módulo: `website_sale_searchable_text`
- Fecha: 2026-09-08
- Origen: versión 12.0 en `odoo_12/addons/trey-addons`.

## 2. Objetivo
- Portar a Odoo 16 la funcionalidad de búsqueda de productos de la tienda web
  sobre un texto consolidado.
- Adaptar el módulo al nuevo mecanismo de búsqueda ("fuzzy") de la tienda web
  de Odoo 16 sin reescribir controladores completos.

## 3. Alcance
### Incluido
- Campo calculado y almacenado `product.template.searchable_text` con el
  nombre, la descripción web sin HTML, `hidden_mapping` y los `default_code`
  de las variantes.
- Campo `product.template.hidden_mapping` para términos de búsqueda extra.
- Registro de `searchable_text` como campo de búsqueda mediante
  `product.template._search_get_detail()`.
- Ajuste del filtro de precio mediante
  `WebsiteSale._add_search_subdomains_hook()`.
- Vista de formulario de producto con `hidden_mapping` y `searchable_text`
  (este último solo en modo desarrollador).
- Tests de cómputo y de integración con la búsqueda de la tienda.

### Excluido
- Semántica OR entre palabras y frase exacta entre comillas que tenía la
  versión 12.0. En 16.0 se adopta la semántica estándar (AND entre palabras).
- Traducción de `searchable_text` (`translate=True`), incompatible con un
  campo `compute` + `store` en el nuevo sistema de traducción jsonb.

## 4. Diseño técnico
- `searchable_text`: `fields.Text(compute='_compute_searchable_text',
  store=True)`. Depende de `name`, `default_code`,
  `product_variant_ids.default_code`, `website_description` y
  `hidden_mapping`. La descripción web se limpia con `tools.html2plaintext`.
- `hidden_mapping`: `fields.Text(translate=True)`.
- `_search_get_detail()`: se hace `super()` y se añade `searchable_text` a
  `detail['search_fields']` (no a `mapping`/`fetch_fields`, para no volcar el
  blob en el autocompletado).
- `_add_search_subdomains_hook(search)`: devuelve
  `[('searchable_text', 'ilike', search)]`, combinado con OR sobre el
  resultado de `super()`. Solo afecta al cálculo de los topes del filtro de
  precio (`_get_search_domain`).
- Vista: herencia de `product.product_template_form_view`, campos añadidos
  tras `website_id`.

## 5. Validación esperada
- Al crear/editar un producto, `searchable_text` refleja nombre, descripción
  web sin etiquetas, `hidden_mapping` y referencias de variantes.
- En `/shop`, buscar un término presente solo en `hidden_mapping` o en la
  referencia de una variante devuelve el producto.
- El filtro de precio de la tienda es coherente con los resultados de la
  búsqueda.
- `-u website_sale_searchable_text --test-enable` en verde.

## 6. Riesgos
- Cambio de comportamiento respecto a 12.0: la búsqueda pasa de "cualquier
  palabra" a "todas las palabras". Si algún cliente depende del comportamiento
  antiguo, hay que sobrescribir `_search_build_domain` en `product.template`.
- Requiere actualización de módulo por los campos nuevos.
- Tras instalar, forzar un recálculo de `searchable_text` si ya existen
  productos (se recalcula solo al cambiar alguna dependencia).

# Especificación incremental del módulo
# `ede` — Segmentación de solicitudes EDE en lotes (batches)

## Resumen
- Objetivo:
  Introducir la segmentación (batching) de las solicitudes que se envían a
  la API EDE para evitar peticiones masivas y controlar la concurrencia y
  tamaño de cada lote.
- Alcance:
  - Modificaciones en `models/product_template.py` para agrupar items en
    lotes antes de llamar a la API.
  - Ajustes en `models/res_company.py` para exponer parámetros de batching
    (tamaño máximo de lote, ventana temporal, etc.).
  - Actualización del `__manifest__` y traducciones (`i18n`).
  - Vistas necesarias para editar parámetros por compañía.
- Fuera de alcance:
  - No se cambian los flujos de pedido ni la lógica de conciliación de precios
    más allá de la agregación en lotes.

## Áreas impactadas
- Backend:
  - `models/product_template.py`:
    - Nuevo método para segmentar `items` en batches: `segment_items_for_ede(self, batch_size)`.
    - Ajustes en el job que construye payloads para `EdeApi` para soportar
      múltiples llamadas por batch.
  - `models/res_company.py`:
    - Nuevos campos de configuración: `ede_batch_size` (int), `ede_batch_delay` (secs).
- Configuración/ops:
  - Recomendar ajustar `config.yml` del runner para reflejar canales y
    concurrencia; usar canal específico por batches si procede.
- Tests:
  - Tests unitarios para `segment_items_for_ede()` que verifiquen tamaños y
    contenido de batches.
  - Test que valida que el job llama repetidamente a `EdeApi.simulate_order`
    por cada batch en lugar de hacerlo en una única petición.

## Diseño funcional
- Flujo general:
  1. El cron o el job que procesa plantillas construye la lista de `items` a
     simular (barcode/cantidad/compañía).
  2. Antes de llamar a `EdeApi.simulate_order`, se segmenta la lista en
     sublistas de tamaño `ede_batch_size`.
  3. Para cada batch, se realiza una llamada separada a `EdeApi.simulate_order`.
  4. Los resultados se aplican a las `seller_ids` correspondientes; si un
     batch falla parcialmente, el job decide si reintentar el batch o seguir.

## Diseño técnico
- Ubicaciones relevantes:
  - [addons/trey-addons/ede/models/product_template.py](addons/trey-addons/ede/models/product_template.py#L1-L400)
  - [addons/trey-addons/ede/models/res_company.py](addons/trey-addons/ede/models/res_company.py#L1-L200)
  - [addons/trey-addons/ede/__manifest__.py](addons/trey-addons/ede/__manifest__.py#L1-L120)
  - [addons/trey-addons/ede/views/res_company_views.xml](addons/trey-addons/ede/views/res_company_views.xml#L1-L160)

- API y cambios de código:
  - Añadir en `product_template.py`:
    - `def segment_items_for_ede(self, items, batch_size):` retorna lista de batches.
    - Modificar el job `job_ede_update_price` para iterar sobre batches:
      ```py
      for batch in self.segment_items_for_ede(items, batch_size):
          resp = EdeApi.simulate_order(batch)
          process_response(resp)
      ```
  - En `res_company.py` añadir campos y getters para `ede_batch_size`.

## Manejo de errores y logs
- Si una llamada por batch falla con error recuperable, el job lanza
  `queue_job.exception.FailedJobError` para reintento; en errores no recuperables
  se registran y se continúa con los siguientes batches (según política).
- Agregar logs por batch con `batch_id`, `size` y `elapsed_ms` para trazabilidad.

## Validación prevista
- Manual:
  1. Configurar `res.company` con `ede_batch_size` pequeño (ej. 10).
  2. Encolar job para una plantilla con >10 items.
  3. Verificar que se realizan múltiples llamadas a `EdeApi.simulate_order` y
     que cada llamada procesa como máximo `ede_batch_size` items.
- Tests:
  - Test que verifica la fragmentación en batches y que cada batch es enviado.

## Notas de implementación
- Mantener retrocompatibilidad: si `ede_batch_size` es `None` o `0`, caer
  al comportamiento previo (una sola llamada con todos los items).
- Revisar límites de la API EDE (máximo items por petición) y mapearlos como
  valor por defecto de `ede_batch_size` en `res.company`.

---

Fecha: 2026-05-25
Autor: Miguel

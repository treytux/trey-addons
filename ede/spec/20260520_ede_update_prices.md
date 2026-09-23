# Especificación incremental del módulo
# `ede` — Actualización automática de precios de compra desde EDE

## Resumen
- Objetivo:
  Añadir un `ir.cron` que encole la actualización de la tarifa de compra
  (`product.supplierinfo.price`) para los productos cuyo proveedor sea EDE,
  ejecutando la simulación contra la API de EDE y persistiendo los precios
  resultantes.
- Alcance:
  - Cron que crea un `queue.job` por plantilla de producto.
  - Job por plantilla que llama a `EdeApi.simulate_order` y actualiza los
    `seller_ids` correspondientes.
  - Uso de `with_delay(channel='root.ede_prices')` para ejecutar cada plantilla
    en procesos independientes.
- Fuera de alcance:
  - No se modifican flujos de venta ni otros conectores externos.

## Áreas impactadas
- Backend:
  - Nuevo cron en `data/ede_data.xml` que llama a
    `product.template.cron_ede_update_product_prices()`.
  - Nuevo método de job en `models/product_template.py`:
    - `cron_ede_update_product_prices(self, domain=None)`
    - `job_ede_update_price(self)`
- Dependencias/ops:
  - Requiere `queue_job` activo y el canal `root.ede_prices` configurado en
    `config.yml` del runner.
- Tests:
  - Test que verifica que el cron encola un job por producto (`tests/test_ede.py`).

## Diseño funcional
- Flujo general:
  1. El cron busca `product.template` que tengan líneas de proveedor
     (`seller_ids`) configuradas para el proveedor EDE y opcionalmente otras
     restricciones (barcode, compañía).
  2. Por cada plantilla encontrada, se encola un `queue.job` específico para
     esa plantilla usando `with_delay(channel='root.ede_prices')`.
  3. El worker consume los jobs y cada job:
     - Construye el payload de `items` (barcode y cantidad mínima) a partir de
       `product.seller_ids` relevantes.
     - Llama a `EdeApi.simulate_order(...)` y procesa la respuesta XML
       (`SalesOrderSimulateConfirmation/Items/Item`).
     - Actualiza `product.supplierinfo.price` solo si el precio devuelto difiere.
     - En caso de error recuperable, lanza `queue_job.exception.FailedJobError`
       para permitir reintento según configuración de la cola; errores no
       recuperables se registran y fallan el job.

## Diseño técnico
- Ubicación del cron:
  - [addons/trey-addons/ede/data/ede_data.xml](addons/trey-addons/ede/data/ede_data.xml#L1-L120)
- Ubicación de la lógica:
  - [addons/trey-addons/ede/models/product_template.py](addons/trey-addons/ede/models/product_template.py#L1-L320)
- API usada:
  - `addons/trey-addons/ede/models/ede_api.py` — wrapper SOAP que expone
    `simulate_order(...)` y devuelve estructura XML compatible con los
    wizards existentes.
- Canal de ejecución:
  - Se usa `root.ede_prices` como canal específico para aislar los jobs de
    EDE y limitar su concurrencia desde `config.yml`.
- Comportamiento de seguridad y datos:
  - Solo se actualizan `seller_ids` que apunten al proveedor configurado para
    EDE (no se alteran otras líneas de proveedor).
  - Se requiere `barcode` para incluir un producto en la simulación; sin
    barcode, la plantilla se omite y se registra advertencia en logs.

## Manejo de errores y logs
- Errores de conexión o respuesta inválida: lanzar `FailedJobError` para que el
  job quede en estado reintentable.
- Si la respuesta no contiene precios para un `barcode`, se registra un aviso
  y el job continúa con las demás líneas.
- Evitar checks de truthiness con `Element` XML — usar `is None` o comprobar
  `len(elem)` para evitar `FutureWarning`.

## Validación prevista
- Manual:
  1. Asegurar que `queue_job` está instalado y el runner tiene el canal
     `root.ede_prices` configurado.
  2. Crear varios `product.template` con `seller_ids` apuntando a EDE y con
     `barcode`.
  3. Ejecutar manualmente `env['product.template'].cron_ede_update_product_prices()`
     desde `odoo-bin shell -d <db>`.
  4. Verificar que se crean `queue.job` por plantilla con `method_name`
     `job_ede_update_price` y `channel` `root.ede_prices`.
  5. Comprobar que el worker procesa los jobs y que `product.supplierinfo.price`
     se actualiza con los valores devueltos por EDE.
- Automática (tests):
  - Test unitario que comprueba que el cron encola un job por producto
    (`tests/test_ede.py`). Para pruebas end-to-end se recomienda mockear
    `EdeApi.simulate_order`.

## Recomendaciones futuras
- Exponer `ShipmentTypeCode` y otros parámetros como campo en `res.company`
  para permitir multi-compañía con diferentes configuraciones EDE.
- Añadir logs más detallados por línea de proveedor (audit trail) y una
  sección de auditoría en el modelo `product.supplierinfo` si se requiere
  histórico de cambios.

---

Fecha: 2026-05-20
Autor: equipo de desarrollo

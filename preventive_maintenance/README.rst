========================
Mantenimiento preventivo
========================

Este módulo añade métodos para generar informes de mantenimiento para bases de datos.

Los informes se añaden como adjuntos .json a ir.model.log de res.company.

Para consultar los informes generados ir a:
	**'Ajustes -> Registros de modelos -> Registros'**

Cada compañía genera su propio registro de log. Además, se genera un registro
independiente para los datos compartidos entre empresas (company_id vacío).

Pasar un recordset de IDs vacío genera solo el registro compartido.

Estos logs se marcan con ``is_preventive_maintenance = True`` para poder
filtrarlos o eliminarlos con ``remove_preventive_maintenance_logs``.

**NOTA**: Hay que revisar el espacio que ocupan los registros, muy probablemente
haya que reducir el texto impreso en el .json o asegurarse de sobrescribir registros
anteriores.

Tipos de log
------------

Los registros de mantenimiento incluyen un campo ``type`` para filtrar los
informes de historial de cron, historial de consultas lentas, integridad y
almacenamiento.

Historial de consultas lentas
-----------------------------

Mide las consultas ejecutadas por Odoo y registra únicamente las que superan el
umbral configurado con un ``query_id``.

Para hacerlo funcionar añadir hay que ``preventive_maintenance`` a opciones y
reiniciar Odoo. Configurar el umbral en milisegundos; el valor ``-1`` lo
desactiva (valor predeterminado):

Se debe añadir a la sección ``[options]`` de ``odoo-server.conf``:

.. code-block:: ini

    [options]
    server_wide_modules = base,web,preventive_maintenance
    preventive_slow_query_min_duration_ms = 5000

Límites opcionales para proteger la instancia:

.. code-block:: ini

    preventive_slow_query_max_buckets = 500
    preventive_slow_query_max_events_per_minute = 100
    preventive_slow_query_flush_interval_seconds = 60

Los eventos se agrupan por ``query_id``, servidor y hora. El límite de eventos
crea un contador de eventos descartados en vez de generar escrituras sin límite
durante una incidencia.

Ejemplo de acción planificada para el informe:

.. code-block:: python

    model.run_slow_query_history(days=7, max_records=100)

Limpieza configurada manualmente mediante otra acción planificada:

.. code-block:: python

    model.cleanup_slow_query_history(retention_days=90, batch_size=500)

Integridad de registros
-----------------------

**run_records_integrity** comprueba contactos, productos, relaciones y fechas de
proveedores.

Los resultados de duplicados se separan en secciones de contactos
y productos.

Argumentos obligatorios:

* companies: recordset de res.company.
* max_groups: máximo de grupos duplicados devueltos por comprobación.
* max_ids_per_group: máximo de IDs incluidos en cada resultado.
* fuzzy_name_threshold: umbral de similitud en contactos, entre 0 y 1.

Ejemplo:

.. code-block:: python

    env['res.company'].run_records_integrity(
        companies=env['res.company'].browse([1]),
        max_groups=500,
        max_ids_per_group=200,
        fuzzy_name_threshold=0.88,
    )

Uso de almacenamiento
---------------------

**run_storage_usage** comprueba:

* modelos inactivos y su cantidad de registros;
* las tablas más grandes;
* las tablas con más registros creados durante el periodo configurado;
* adjuntos grandes;
* referencias de adjuntos desconectadas o rotas;
* adjuntos cuyo fichero físico no existe;
* adjuntos URL en una sección independiente;
* información sobre adjuntos duplicados.

Argumentos obligatorios:

* companies: recordset de res.company.
* inactive_limit: cantidad mínima de registros inactivos para informar de un
  modelo.
* large_attachment_limit: tamaño mínimo de un adjunto, en bytes.
* max_size_tables: número de tablas más grandes que se devolverán.
* max_growth_tables: número de tablas con más registros creados recientemente.
* growth_period: periodo de crecimiento, en meses, medido mediante
  create_date.

El tamaño de las tablas por compañía se estima sumando el tamaño de sus filas.
Las tablas sin company_id se consideran compartidas. Los tamaños se formatean
como cadenas, por ejemplo 42.18 MB.

Ejemplo:

.. code-block:: python

    env['res.company'].run_storage_usage(
        companies=env['res.company'].browse([1]),
        inactive_limit=100,
        large_attachment_limit=5 * 1024 * 1024,
        max_size_tables=10,
        max_growth_tables=10,
        growth_period=3,
    )

Los IDs solo se incluyen cuando son útiles para acciones masivas posteriores.
En los modelos inactivos se informa del modelo y la cantidad, de modo que los
registros pueden inspeccionarse mediante los filtros normales de Odoo.

**NOTA**: Devolver solo los dominios como con inactivos podría reducir mucho la
carga de los .json generados.

Informes aislados
-----------------

* run_tables_by_growth(companies, max_growth_tables, growth_period):
	tablas con más entradas creadas durante el periodo indicado.
* run_inactive_models(companies, inactive_limit):
	modelos que superan el límite de registros inactivos.
* run_large_attachments(companies, large_attachment_limit):
	adjuntos que superan el tamaño indicado, en bytes.
* run_disconnected_attachments(companies):
	adjuntos desconectados, sin referencias o cuyo fichero no existe.

Todos los argumentos indicados son obligatorios. Por ejemplo:

.. code-block:: python

    env['res.company'].run_tables_by_growth(
        companies=env['res.company'].browse([1]),
        max_growth_tables=10,
        growth_period=3,
    )


Ejemplo de ir.cron
------------------

Para generar el informe de almacenamiento de la compañía (1) e incluir las
(10) tablas más grandes, se puede configurar el código del cron así:

.. code-block:: python

    model.run_tables_by_size(
        companies=env['res.company'].browse([1]),
        max_size_tables=10,
    )

**AVISO**: Algunas operaciones consumen bastantes recursos, si hace un
cron no debería programarse mientras haya actividad en la compañía.

Ejemplo desde Odoo shell
------------------------

Inicie un shell para la base de datos correspondiente:

.. code-block:: console

    ./odoo-bin shell -d mi_base_de_datos

Después ejecute el método deseado:

.. code-block:: python

    company = env['res.company'].browse([1])
    resultados = env['res.company'].run_storage_usage(
        companies=company,
        inactive_limit=100,
        large_attachment_limit=5 * 1024 * 1024,
        max_size_tables=10,
        max_growth_tables=10,
        growth_period=3,
    )

Historial de ejecuciones de cron
--------------------------------

El módulo registra las ejecuciones de ``ir.cron`` en el modelo
``preventive.maintenance.cron.history``, incluyendo fechas, duración, estado,
servidor y traceback completo en caso de error. El registro se escribe en una
transacción independiente para conservarlo aunque el cron monitorizado haga
rollback.

El registro de ejecuciones es automático para las acciones programadas y para
las ejecuciones manuales de un ``ir.cron``. No es necesario modificar el
código de los cron existentes. Cada ejecución genera un registro con estos
campos:

* ``cron_id``: acción programada ejecutada;
* ``date_start`` y ``date_end``: fechas de inicio y finalización;
* ``duration_sec``: duración calculada en segundos;
* ``state``: ``running``, ``success`` o ``failed``;
* ``server_name``: nombre del servidor que ejecutó la acción;
* ``error_traceback``: traceback completo cuando la ejecución falla.

Análisis del historial
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    model.run_cron_history(days=30, max_records=100)

Los parámetros son:

* ``days``: número de días hacia atrás que se analizarán. Debe ser un entero
  positivo;
* ``max_records``: máximo de ejecuciones incluidas en el informe. Se devuelven
  primero las más recientes y debe ser un entero positivo.

Limpieza del historial
~~~~~~~~~~~~~~~~~~~~~~~

La limpieza también se configura manualmente mediante otro ``ir.cron``. Se
puede utilizar, por ejemplo, una acción programada sobre el modelo
``preventive.maintenance.cron.history`` con este código:

.. code-block:: python

    model.cleanup(retention_days, batch_size)

Los parámetros son:

* ``retention_days``: elimina ejecuciones anteriores a este número de días;
* ``batch_size``: máximo de registros eliminados en una ejecución.

Un valor de ``retention_days`` igual o inferior a cero desactiva la limpieza.
La limpieza es la única operación de esta funcionalidad que elimina datos.

Notas
-----
El valor devuelto por ``run_cron_history`` y ``run_cron_analysis`` es un único
diccionario de informe. Los logs y sus adjuntos JSON están disponibles en
Administración -> Logs de modelos. Se pueden filtrar usando el campo
``Is maintenance`` y eliminar conjuntamente con:

.. code-block:: python

    env['ir.model.log'].remove_preventive_maintenance_logs()

Los informes son de solo lectura. No modifican los cron ni los datos
inspeccionados. El modelo de historial es técnico y no tiene vistas propias;
el análisis se consulta mediante el adjunto JSON del log. El acceso directo al
modelo está limitado a administradores del sistema.

El módulo no crea registros ir.cron automáticamente. Los cron pueden crearse
manualmente en cada base de datos, pasando toda la configuración de forma
explícita.

Autor
~~~~~

* `Trey <https://www.trey.es>`__:

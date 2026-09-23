# SPEC: Corrección de paginación de tareas en portal de proyecto

## 1. Contexto
- Fecha de solicitud: 2026-05-20
- Módulo afectado: `portal_project`
- Ruta afectada: `/my/projects/<project_id>`

## 2. Objetivos
- Evitar que la segunda página del listado de tareas fuerce la agrupación por
  proyecto cuando el usuario no ha seleccionado agrupación.
- Mostrar tareas distintas en cada página del listado.
- Conservar el valor de "Filtrar por" al navegar entre páginas.
- Hacer que el listado inferior respete los filtros anuales usando la misma
  fecha que muestra la tabla (`project.task.create_date`).
- Excluir del filtro "Tareas abiertas" las tareas en etapas con nombre fuente
  `Done` y `Cancelled`, aunque se muestren traducidas al usuario y aunque la
  etapa no esté plegada.
- Aumentar el tamaño de página del detalle de proyecto a 50 tareas.
- Mantener intactos la gráfica, totales y filtros de partes de horas.

## 3. No objetivos
- No modificar Odoo core ni módulos OCA.
- No cambiar el listado global de tareas `/my/tasks`.
- No filtrar el listado por partes de horas; los partes siguen alimentando
  únicamente estadísticas, gráfica y contador.

## 4. Diseño técnico
- En el controlador de portal de proyecto, usar `groupby='none'` cuando la
  ruta no reciba una agrupación explícita.
- Añadir `filterby` a los argumentos del pager cuando exista en la petición.
- Mantener `task_id.is_closed = False` como regla estándar de Odoo para
  tareas abiertas y añadir la exclusión local por nombre fuente de etapa para
  `Done` y `Cancelled`.
- Para filtros anuales, aplicar el rango del año sobre `task.create_date`,
  que es la fecha visible en la columna "Fecha" del listado.
- Aplicar un límite de 50 tareas por página solo al detalle de proyecto.
- Mantener `grouped_tasks` como estructura exclusiva del listado de tareas.
- Calcular un contador dedicado para el botón de partes de horas con el mismo
  dominio usado por la gráfica y los totales.
- Corregir la URL base de filtros del detalle de proyecto para que apunte a
  `/my/projects/<project_id>`.

## 5. Plan de validación
- Añadir una prueba HTTP con más de 50 tareas para verificar que la página 2
  muestra tareas diferentes y no muestra cabecera de agrupación por proyecto.
- Verificar que el enlace del paginador conserva el año seleccionado en
  "Filtrar por".
- Verificar que al seleccionar un año no se muestran tareas cuya fecha visible
  (`create_date`) pertenece a otro año, aunque tengan partes en el año filtrado.
- Verificar que "Tareas abiertas" no cuenta partes de horas de tareas en etapa
  `Done`/`Cancelled` bajo contexto `es_ES` aunque la etapa no esté plegada.
- Verificar que la gráfica y los totales de horas siguen usando los partes de
  horas filtrados.
- Verificar que el contador del botón de partes de horas respeta el filtro.
- Ejecutar las pruebas de `portal_project` y `pre-commit` sobre los archivos
  modificados.

## 6. Riesgos y mitigaciones
- Riesgo: afectar otros listados de portal.
  - Mitigación: limitar el tamaño de página de 50 al detalle de proyecto.
- Riesgo: romper estadísticas de horas al separar `grouped_tasks`.
  - Mitigación: conservar el cálculo de `graph_data` desde `timesheets`.

## 7. Entregables
- `controllers/main.py`
- `views/project_portal_templates.xml`
- `tests/test_portal_project_http.py`
- `__manifest__.py`

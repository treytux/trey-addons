# SPEC: Tipologías de partner por categoría

## 1. Contexto
- Fecha de solicitud: 2026-05-29
- Solicitado por: usuario
- Alcance: crear el módulo `partner_category_type_tipology` en
  `addons/trey-addons/` para identificar categorías de partner que actúen
  como tipologías de cliente y asociarles porcentajes mínimo y máximo de
  cumplimiento sobre horas planificadas.
- Límites de repositorio: los cambios deben limitarse a
  `addons/trey-addons/partner_category_type_tipology/`. El código core de
  Odoo y repositorios OCA se tratan como solo lectura.
- El nombre del módulo debe conservar `tipology` por requerimiento funcional,
  pero los campos técnicos deben usar siempre `typology`.

## 2. Objetivos
- Extender `res.partner.category` con campos que permitan marcar una categoría
  como tipología de partner.
- Definir porcentajes mínimo y máximo de cumplimiento esperado sobre horas
  planificadas para cada tipología.
- Extender `res.partner` con una tipología única seleccionable desde categorías
  marcadas como tipología.
- Mostrar en la ficha de partner la tipología y sus porcentajes relacionados.
- Cargar las tipologías iniciales A/B/C/D.
- Cubrir la lógica con tests automáticos.

## 3. No objetivos
- No calcular todavía objetivos de horas ni cumplimiento mensual.
- No modificar la lógica estándar de `category_id` en partners.
- No crear modelos nuevos ni reglas de seguridad específicas.
- No depender obligatoriamente de `partner_category_type`, salvo que se apruebe
  explícitamente una reutilización posterior.

## 4. Requisitos funcionales
- En `res.partner.category` deben existir:
  - `is_partner_typology`: booleano para habilitar la categoría como tipología.
  - `min_planned_rate`: porcentaje mínimo esperado.
  - `max_planned_rate`: porcentaje máximo esperado.
- Si una categoría es tipología:
  - `min_planned_rate` debe ser mayor o igual que `0.0`.
  - `max_planned_rate` debe ser mayor o igual que `0.0`.
  - `min_planned_rate` debe ser menor o igual que `max_planned_rate`.
- Debe permitirse `max_planned_rate > 1.0`.
- Si una categoría no es tipología, los porcentajes no deben bloquear la
  edición aunque existan valores cargados.
- En `res.partner` debe existir:
  - `partner_typology_id`: Many2one a `res.partner.category`, limitado por
    dominio a categorías con `is_partner_typology = True`.
  - `partner_typology_min_planned_rate`: relacionado de solo lectura.
  - `partner_typology_max_planned_rate`: relacionado de solo lectura.
- La vista de partner debe mostrar los campos en la pestaña Sales & Purchase,
  bloque Sales, justo después de `property_product_pricelist`.
- La vista de categorías debe permitir editar la marca de tipología y los dos
  porcentajes, ocultando o haciendo no molestos los porcentajes cuando la
  categoría no sea tipología.
- Deben cargarse cuatro categorías iniciales:
  - A - Strategic: mínimo `0.85`, máximo `1.00`.
  - B - Relevant: mínimo `0.70`, máximo `0.85`.
  - C - Standard: mínimo `0.50`, máximo `0.70`.
  - D - Reactive: mínimo `0.00`, máximo `0.50`.

## 5. Diseño técnico
- Módulo:
  - `partner_category_type_tipology`
- Dependencias:
  - `base`
  - `contacts`
  - `product`
- Nota sobre `product`:
  - La vista estándar que añade `property_product_pricelist` al bloque Sales
    pertenece al módulo `product`. Se incluye como dependencia técnica para
    que el XPath después de la lista de precios sea instalable de forma
    determinista.
- Dependencias descartadas por ahora:
  - No se ha encontrado uso local de `partner_category_type` en los manifests
    revisados, por lo que no se incluirá como dependencia inicial.
- Archivos de inicialización:
  - `__init__.py`
  - `models/__init__.py`
- Manifest:
  - Debe usar la cabecera AGPL completa de Trey.
  - Versión inicial `16.0.1.0.0`.
  - Debe incluir datos, vistas, tests y archivos de presentación si se crean.
- Presentación del módulo:
  - Al ser módulo nuevo, debe incluir `README.rst`.
  - Debe incluir `static/description/index.html` y recursos necesarios por la
    plantilla usada, como `icon.png` si se reutiliza desde otro módulo.
  - `README.rst` e `index.html` deben describir el módulo en español.
- Modelos:
  - `models/res_partner_category.py` hereda `res.partner.category`.
  - `models/res_partner.py` hereda `res.partner`.
  - Todos los `.py` deben usar la cabecera corta Trey.
- Validaciones:
  - Constraint Python con `@api.constrains` sobre
    `is_partner_typology`, `min_planned_rate` y `max_planned_rate`.
  - Mensaje para negativos: `Planned rates cannot be negative.`
  - Mensaje para mínimo superior al máximo:
    `The minimum planned rate must be lower than or equal to the maximum
    planned rate.`
- Datos:
  - `data/res_partner_category_data.xml` con los XML IDs:
    - `res_partner_category_typology_a`
    - `res_partner_category_typology_b`
    - `res_partner_category_typology_c`
    - `res_partner_category_typology_d`
- Vistas:
  - `views/res_partner_category_views.xml`.
  - `views/res_partner_views.xml`.
  - XML con cabecera estándar y raíz `<odoo>`.
  - En vistas heredadas no incluir `<field name="name">`.
  - Los IDs heredados deben coincidir con la referencia heredada cuando aplique
    según la regla Trey.
- Seguridad:
  - No crear `security/ir.model.access.csv` ni declararlo en manifest, porque
    no se crean modelos nuevos.
- Tests:
  - `tests/__init__.py`.
  - `tests/test_partner_category_type_tipology.py`.
  - Usar `odoo.tests.common.TransactionCase`.

## 6. Plan de validación
- Tests automáticos mínimos:
  - Crear una categoría tipología válida.
  - Rechazar porcentajes negativos cuando `is_partner_typology` es verdadero.
  - Rechazar `min_planned_rate > max_planned_rate` cuando es tipología.
  - Permitir una categoría no tipología sin porcentajes específicos.
  - Asignar una tipología a un partner.
  - Verificar los campos relacionados en partner.
  - Verificar que existen las cuatro categorías iniciales y que son tipologías.
- Comandos de validación propuestos:
  - `oo exec <db_name> -u partner_category_type_tipology --stop-after-init`
  - `oo exec <db_name> -u partner_category_type_tipology --test-enable --stop-after-init`
  - `pre-commit run --files <archivos_modificados>`
- Checks manuales:
  - Abrir Contacts / Partner form y revisar Sales & Purchase / Sales.
  - Confirmar que la tipología aparece después de Pricelist.
  - Abrir una categoría de partner y comprobar edición/visibilidad de los
    porcentajes.

## 7. Riesgos y mitigaciones
- Riesgo: los XML IDs de vistas estándar pueden variar según dependencias.
  Mitigación: localizar las vistas reales en el entorno antes de escribir los
  XPath definitivos.
- Riesgo: el campo `property_product_pricelist` puede estar condicionado por
  grupos o por módulos instalados.
  Mitigación: heredar la vista estándar de contacts/base y usar XPath directo
  después del campo existente.
- Riesgo: los campos relacionados no almacenados no son óptimos para búsquedas.
  Mitigación: mantenerlos no almacenados según alcance inicial; otro módulo
  podrá pedir `store=True` si necesita dominios o reporting.
- Riesgo: datos iniciales modificables por usuarios.
  Mitigación: cargarlos como datos normales para que puedan gestionarse desde
  Odoo si el negocio cambia los umbrales.

## 8. Entregables
- `addons/trey-addons/partner_category_type_tipology/README.rst`
- `addons/trey-addons/partner_category_type_tipology/__init__.py`
- `addons/trey-addons/partner_category_type_tipology/__manifest__.py`
- `addons/trey-addons/partner_category_type_tipology/data/res_partner_category_data.xml`
- `addons/trey-addons/partner_category_type_tipology/i18n/es.po`
- `addons/trey-addons/partner_category_type_tipology/i18n/partner_category_type_tipology.pot`
- `addons/trey-addons/partner_category_type_tipology/models/__init__.py`
- `addons/trey-addons/partner_category_type_tipology/models/res_partner.py`
- `addons/trey-addons/partner_category_type_tipology/models/res_partner_category.py`
- `addons/trey-addons/partner_category_type_tipology/static/description/index.html`
- `addons/trey-addons/partner_category_type_tipology/static/description/icon.png`
- `addons/trey-addons/partner_category_type_tipology/tests/__init__.py`
- `addons/trey-addons/partner_category_type_tipology/tests/test_partner_category_type_tipology.py`
- `addons/trey-addons/partner_category_type_tipology/views/res_partner_category_views.xml`
- `addons/trey-addons/partner_category_type_tipology/views/res_partner_views.xml`

## 9. Plan de rollback
- Desinstalar el módulo si ya fue instalado.
- Eliminar la asignación `partner_typology_id` de partners si se requiere
  limpiar datos funcionales.
- Revertir el directorio `addons/trey-addons/partner_category_type_tipology/`.
- Si los datos iniciales se cargaron, eliminar o archivar las cuatro categorías
  A/B/C/D según política funcional.

## 10. Plan de implementación por fases
- Fase 1: congelar esta especificación técnica.
- Fase 2: backend.
  - Crear estructura del módulo, manifest, modelos, constraints y datos.
- Fase 3: frontend.
  - Crear vistas heredadas de partner y categoría.
- Fase 4: QA.
  - Crear tests y ejecutar instalación/actualización con tests.
- Fase 5: i18n.
  - Generar o actualizar `i18n/*.po` si los textos de usuario se extraen en
    este repositorio para módulos nuevos.

## 11. Briefs de delegación
- Backend (`odoo-dev-backend`):
  - Crear el módulo nuevo en `addons/trey-addons/`.
  - Añadir modelos heredados, fields, constraint y datos iniciales.
  - No crear ACLs porque no hay modelos nuevos.
  - Devolver archivos tocados, resumen, comandos de validación y riesgos.
- Frontend (`odoo-view-tweaks`):
  - Crear las vistas heredadas para `res.partner` y `res.partner.category`.
  - Ubicar `partner_typology_id` después de `property_product_pricelist`.
  - Mostrar porcentajes relacionados en modo readonly.
  - Añadir los campos de categoría en formulario y tree/list si la vista
    heredable existe.
- QA (`odoo-testing`):
  - Crear tests de constraint, asignación de partner y datos iniciales.
  - Revisar estilo Trey, longitud de líneas, XML, manifest y actualización.
  - Ejecutar los comandos de validación disponibles.
- Localización (`odoo-translator`):
  - Revisar strings nuevos en campos, helps, errores y vistas.
  - Mantener traducciones/glosario si se generan `i18n/*.po`.

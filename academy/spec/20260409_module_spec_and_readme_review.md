# Especificación del módulo Academy

Fecha: 2024-09-11
Módulo: `academy`
Ruta: `addons/trey-addons/academy`

## 1. Alcance

Este módulo implementa la gestión de academia sobre Odoo 16 para cubrir:

- Planes formativos y actividades.
- Estudiantes, tutores y profesores.
- Matrículas y su ciclo de vida.
- Evaluaciones, conceptos evaluables y calificaciones.
- Boletines de notas y publicación de líneas.
- Facturación mensual de actividades.
- Acceso por roles para responsable, usuario, profesor, tutor y estudiante.

Esta especificación también alinea la documentación funcional con el código
actual, con especial foco en `README.rst`.

## 2. Inventario funcional

### Modelos backend

- `academy.training.plan`
  - Define fechas del plan formativo, tipología, responsable y cuenta analítica.
  - Crea automáticamente una cuenta analítica al crear el registro si no se
    informa una manualmente, una vez que el propio plan ya se ha creado con
    éxito.
  - Puede cerrar planes y propagar el cierre a actividades y matrículas
    relacionadas.

- `academy.activity`
  - Pertenece a un plan formativo.
  - Almacena profesor, precios, configuración de facturación, evaluaciones y
    conceptos evaluables.
  - Calcula contadores de matrículas por estado.
  - Relaciona facturas y boletines.

- `academy.enrollment`
  - Vincula estudiante, actividad y plan formativo.
  - Gestiona la máquina de estados de matrícula:
    `pending_level`, `pending_group`, `active`, `ended`, `dropout`,
    `cancelled`.
  - Copia tutores y formación académica desde el estudiante durante el flujo de
    onchange/creación.
  - Aplica límite de plazas y validación de fechas contra la actividad.
  - Evita matrículas duplicadas para el mismo estudiante y actividad.

- `academy.marks.bulletin`
  - Mantiene un boletín por matrícula.
  - Restringe en formulario la selección a matrículas en estado `active`.
  - Calcula curso/sesión y tutores.
  - Genera líneas de boletín por evaluación y concepto evaluable.

- `academy.marks.bulletin.line`
  - Guarda evaluación, concepto evaluable, calificación y visibilidad en portal.
  - Publica un mensaje en el chatter cuando cambia la calificación.

- `academy.evaluation`
- `academy.evaluable.concept`
- `academy.evaluable.concept.mark`
- `academy.typology`
- `academy.academic.training`

- Extensiones:
  - `res.partner`
    - Añade `is_student`, `is_teacher`, `is_tutor`.
    - Relaciona tutores/estudiantes, matrículas, formación académica y
      boletines.
    - Puede crear usuarios a partir de plantillas para tutores y estudiantes.
  - `hr.employee`
    - Añade comportamiento de profesor mediante `is_activity_selectable`.
    - Sincroniza el contacto laboral como profesor.
    - Precarga grupos de profesor en `action_create_user`.
  - `account.move`
    - Relaciona facturas con actividad y matrícula.

### Asistentes

- `academy.invoice.activities.wizard`
  - Genera facturas de cliente mensuales a partir de actividades seleccionadas.
  - Omite estados no facturables: `pending_level`, `pending_group`,
    `cancelled`.
  - Factura primero al tutor si existe; en caso contrario, al estudiante.
  - Soporta precio reducido y matrículas gratuitas.

- `academy.wizard.generate.bulletin`
  - Genera boletines desde actividades para una evaluación concreta.
  - Incluye matrículas en estados `active`, `ended`, `dropout` si la fecha
    elegida está dentro del rango de la matrícula.

- `academy.wizard.fill.bulletin.line`
  - Añade líneas de boletín pendientes para una evaluación seleccionada.

- `academy.publish.bulletin.lines`
  - Publica líneas de boletín en portal por actividad y evaluación.

### Seguridad y acceso

- Grupos definidos:
  - Responsable
  - Usuario
  - Profesor
  - Tutor
  - Estudiante
- Regla adicional:
  - Los estudiantes sólo ven sus propias matrículas.
- Tutores, estudiantes y profesores tienen acceso de lectura a contactos
  relacionados mediante regla sobre `res.partner`.

### Informes

- Informe PDF de matrícula.
- Informe PDF de boletín de notas.

### Automatismos

- Un cron cierra planes formativos vencidos.
- Los cierres de plan/actividad/matrícula actualizan también fechas y estados
  mediante métodos del modelo.

## 3. Resumen de la revisión del README

### Puntos confirmados que debían mantenerse

- El módulo gestiona planes, actividades, estudiantes, tutores y profesores.
- Las matrículas tienen un informe PDF específico.
- Los boletines pueden generarse desde una actividad.
- Los boletines disponen de informe PDF.

### Puntos ausentes o imprecisos en el README anterior

- Se describían los roles, pero no su efecto real en seguridad y visibilidad de
  profesor/estudiante/tutor.
- No se documentaba la facturación, pese a ser uno de los flujos principales
  implementados.
- La generación de boletines estaba explicada con estados parcialmente
  incorrectos: el código trabaja con `active` en dominio y con
  `active`/`ended`/`dropout` en generación desde actividad.
- No se mencionaba la publicación de líneas de boletín en portal.
- No se mencionaba la creación automática de cuenta analítica en planes
  formativos.
- No se documentaban restricciones importantes de matrícula:
  límite de plazas, duplicados y validación de fechas.
- Había nombres de menú en español que no coincidían con las etiquetas XML
  actuales, definidas en inglés (`Academy`, `Students`, `Training Plans`,
  `Enrollments`, `Configuration`).

## 4. Áreas impactadas

### Backend

- No se requiere cambio backend para esta tarea documental.
- Áreas documentadas:
  `models/`, `wizard/`, `security/`, `data/`.

### Frontend / vistas

- No se requiere cambio en vistas.
- El README queda alineado con la navegación y flujos reales del módulo.

### QA

- Los tests actuales cubren matrículas, asistentes de boletines, facturación y
  creación de profesor/usuario.
- No hacen falta tests automáticos nuevos para este cambio exclusivamente
  documental.

### i18n

- El README se mantiene en español.
- No se requiere actualización de traducciones del módulo para esta tarea.

## 5. Fases de implementación

### Fase 1: congelación de especificación técnica

- Inventariar modelos, asistentes, seguridad, informes y tests.
- Alinear el alcance documentado con el comportamiento implementado.
- Registrar huecos, supuestos y riesgos.

### Fase 2: implementación backend

- No aplica para esta tarea.

### Fase 3: implementación frontend / documentación

- Reescribir `README.rst` incluyendo:
  - alcance del módulo,
  - roles,
  - datos maestros,
  - ciclo de vida de matrículas,
  - flujo de boletines,
  - flujo de facturación,
  - informes y automatismos.

### Fase 4: QA y pruebas automáticas

- Validar que las afirmaciones del README coinciden con código y tests.
- Revisar menús, estados y comportamiento de asistentes.

### Fase 5: i18n y comprobaciones finales

- Verificar consistencia idiomática del README.
- Confirmar que las referencias a imágenes siguen siendo válidas.

## 6. Lista de tareas

### Backend

- Ninguna.

### Frontend / Documentación

- Crear especificación técnica local del módulo bajo `spec/`.
- Reescribir README para reflejar el comportamiento real del módulo.

### QA

- Contrastar las afirmaciones del README contra:
  - modelos,
  - seguridad,
  - asistentes,
  - tests.

### i18n

- Ninguna a nivel de código.

## 7. Plan de pruebas

### Validación de revisión

- Revisar:
  - `__manifest__.py`
  - `README.rst`
  - `models/*.py`
  - `wizard/*.py`
  - `security/academy_security.xml`
  - `views/menu.xml`
  - `tests/*.py`

### Comandos de prueba automatizada

Ejecutar la batería del módulo en un entorno Odoo:

```bash
oo exec -d <database> -- test -i academy --test-tags /academy
```

O, si se prefiere usar el runner de Odoo del proyecto:

```bash
oo exec -d <database> -- odoo-bin -i academy --test-enable --stop-after-init
```

### Checklist de validación manual

- Crear un plan formativo y verificar que se genera cuenta analítica.
- Crear una actividad con profesor, precios, evaluaciones y conceptos.
- Crear un estudiante con tutores y formación académica.
- Crear una matrícula y verificar:
  - propuesta automática de tutores y formación académica,
  - fechas dentro del rango de la actividad,
  - bloqueo de duplicados,
  - aplicación del límite de plazas.
- Generar boletines desde una actividad para una evaluación.
- Publicar líneas de boletín y verificar `portal_published`.
- Generar facturas de un mes y verificar destinatario y precio unitario.

## 8. Briefs de delegación

### Backend

Revisar reglas de integridad de matrículas, boletines y facturación.
Foco en `models/academy_enrollment.py`, `models/academy_marks_bulletin.py` y
`wizard/academy_invoice_activities_wizard.py`. Confirmar si la redacción del
README coincide con restricciones y casos límite reales.

### Frontend / documentación

Responsabilidad sobre `README.rst`. Reescribirlo en español, conservar
referencias a imágenes y alinearlo con la estructura de menús y flujos
implementados.

### QA

Auditar los tests existentes en `tests/` y confirmar que las afirmaciones del
README están cubiertas por código o por pruebas automatizadas. Señalar
comportamientos relevantes no documentados.

### Localización

No aplica en esta tarea salvo que más adelante se requiera replicar la
documentación en otros idiomas.

## 9. Riesgos, supuestos y bloqueos

### Riesgos

- Los nombres de menú del README pueden volver a desalinearse si cambian los
  XML y no se actualiza la documentación a la vez.
- Algunos flujos dependen también de criterio de negocio, especialmente la
  titularidad de la facturación entre tutor y estudiante.

### Supuestos

- Para esta tarea documental, el comportamiento actual del código es la fuente
  de verdad.
- El README se usa como documentación funcional para usuario, no sólo como
  ficha técnica del addon.

### Bloqueos

- Ninguno para la generación de spec y revisión documental.

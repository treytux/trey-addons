# SPEC: Corregir el fichero de traducción de códigos de barras

## 1. Contexto

- Fecha: 2026-09-03
- Módulo: `product_barcode_generator_by_id`
- Incidencia: el backend devuelve HTTP 500 al cargar `/web` porque Odoo no
  puede analizar el fichero `i18n/es.po`.

## 2. Objetivo

Permitir que Odoo cargue las traducciones web del módulo sin excepciones.

## 3. Causa

La traducción de la etiqueta HTML del botón tenía dos declaraciones `msgid`.
La segunda declaración debía ser `msgstr`, por lo que el lector de ficheros
PO fallaba al procesar la entrada.

## 4. Alcance técnico

- Corregir la entrada afectada en
  `product_barcode_generator_by_id/i18n/es.po`.
- No modificar modelos, vistas, datos, seguridad ni dependencias.
- No se requiere migración de base de datos ni cambio de versión del
  módulo: es una corrección de datos de traducción.

## 5. Criterios de aceptación

- El fichero `es.po` se puede analizar con `polib`.
- El lector de traducciones de Odoo procesa el fichero sin excepciones.
- La página `/web` responde sin HTTP 500 causado por traducciones.
- La etiqueta traducida conserva las etiquetas HTML y muestra:
  `Generar` y `Código de barras`.

## 6. Validación

Desde `/var/lib/odoo/adarra16`:

```bash
PYTHONPATH=server .venv/bin/python -c "from odoo.tools.translate import TranslationFileReader; list(TranslationFileReader(open('addons/trey-addons/product_barcode_generator_by_id/i18n/es.po','rb'), fileformat='po'))"
```

Validación funcional:

```bash
oo exec adarra
```

Abrir `/web?debug=assets` y comprobar que no aparece HTTP 500.

## 7. Riesgos y rollback

- Riesgo bajo: solo se modifica la sintaxis de una entrada PO.
- Rollback: restaurar la entrada anterior, aunque volvería a producir el
  fallo del lector de traducciones.

## 8. Entregables

- `product_barcode_generator_by_id/i18n/es.po` corregido.
- Esta especificación.

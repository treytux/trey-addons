# Generación de traducciones del módulo

## Alcance aprobado

Preparar el módulo `ir_translation_auto_translation` para MR añadiendo los
archivos de traducción generados desde la base de datos `mit16_260223` con el
idioma `es_ES`.

## Contexto técnico

El módulo no tenía directorio `i18n/` versionado. Se ejecuta el flujo estándar
de traducción de Odoo Control desde la carpeta del propio módulo para exportar
las cadenas detectadas por Odoo y mantener las traducciones españolas en un
archivo `es.po`.

## Cambios previstos

- Crear `i18n/ir_translation_auto_translation.pot` con las cadenas fuente.
- Crear `i18n/es.po` con las traducciones españolas.
- Normalizar las cabeceras de traducción con los datos de Trey.
- Mantener los identificadores técnicos y ejemplos de dominio sin alterar.
- Mantener el incremento de versión del manifiesto a `16.0.1.1.0`.

## Áreas impactadas

- Backend: sin cambios de lógica Python.
- Frontend: sin cambios en vistas ni plantillas.
- Seguridad: sin cambios en ACL ni reglas.
- Datos: nuevos archivos de traducción cargables por actualización del módulo.
- i18n: nuevas traducciones `es_ES`.

## Plan de ejecución

1. Ejecutar `oo db translate mit16_260223 es_ES` desde el directorio del módulo.
2. Revisar y completar las traducciones generadas en `i18n/es.po`.
3. Normalizar las cabeceras Trey de `es.po` y del archivo `.pot`.
4. Validar el formato del `.po` con `msgfmt --check`.
5. Revisar el estado de git y preparar el resumen de MR.

## Plan de pruebas

- Ejecutar:

  ```bash
  msgfmt --check i18n/es.po -o /tmp/ir_translation_auto_translation_es.mo
  ```

- Validación funcional manual tras actualizar el módulo:

  ```bash
  oo exec mit16_260223 -u ir_translation_auto_translation --stop-after-init
  ```

- Comprobar en interfaz con idioma español que los asistentes y ajustes de
  traducción automática muestran las etiquetas traducidas.

## Riesgos y notas

- La generación depende de que el módulo esté disponible en la base de datos
  usada para exportar las traducciones.
- Si cambian cadenas fuente antes de fusionar, se debe repetir
  `oo db translate mit16_260223 es_ES`.

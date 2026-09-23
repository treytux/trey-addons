# Traducciones al castellano

## Contexto

El modulo `website_b2b_signup_request` muestra un formulario de solicitud de
registro B2B en el sitio web. El archivo `i18n/es.po` debe contener las
traducciones al castellano de las cadenas visibles para el usuario.

## Alcance

- Refrescar las traducciones del modulo desde la base `mit16_260615`.
- Completar las entradas vacias de `i18n/es.po`.
- Normalizar las cabeceras de traduccion segun el criterio Trey.
- Mantener los identificadores originales en ingles sin modificar las vistas.

## Fuera de alcance

- Cambios funcionales en la plantilla del formulario.
- Correcciones de textos originales en ingles.
- Actualizaciones de otros idiomas o modulos.

## Riesgos

- La exportacion puede incorporar metadatos nuevos si la base contiene cambios
  pendientes del modulo.
- Algunas cadenas tecnicas o nombres de vistas deben traducirse de forma
  natural sin alterar su `msgid`.

## Validacion

- Regenerar el catalogo con `oo db translate mit16_260615 es_ES`.
- Revisar que no queden `msgstr` vacios.
- Comprobar que las cabeceras incluyan `Language: es_ES`,
  `Last-Translator: Trey <info@trey.es>` y
  `Language-Team: Trey <info@trey.es>`.

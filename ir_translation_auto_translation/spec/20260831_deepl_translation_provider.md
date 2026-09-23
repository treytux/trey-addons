# Proveedor de traducción DeepL

## Alcance aprobado

Sustituir la integración con MyMemory por DeepL, manteniendo Google Translate
como proveedor disponible.

## Cambios realizados

- Añadir `DeepLProvider` mediante la API REST oficial de DeepL.
- Incorporar la selección `DeepL` en los ajustes del módulo.
- Añadir configuración segura de la clave API de DeepL.
- Usar automáticamente `api-free.deepl.com` para claves terminadas en `:fx` y
  `api.deepl.com` para el resto.
- Traducir los campos HTML enviando el contenido completo con
  `tag_handling=html` y `tag_handling_version=v2`.
- Retirar MyMemory del selector, código cargado, pruebas y documentación.

## Validación

```bash
python3 -m py_compile \
  models/deepl_provider.py \
  models/res_config_settings.py \
  tests/test_ir_translation_auto_translation.py
git diff --check
```

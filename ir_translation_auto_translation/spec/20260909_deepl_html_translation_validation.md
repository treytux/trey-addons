# Validación de traducciones con DeepL

## Alcance

Validar el funcionamiento del proveedor DeepL configurado en el módulo,
incluyendo la traducción de campos de texto y campos de tipo HTML del modelo
`product.template`.

## Configuración

- Seleccionar `DeepL` como proveedor en los ajustes de traducción automática.
- Configurar la clave API de la cuenta DeepL Developer.
- Usar `es_ES` como idioma origen y `en_US` como idioma destino.
- Para cuentas API Free se utiliza el endpoint `api-free.deepl.com` cuando la
  clave termina en `:fx`.

## Validaciones realizadas

- Probar un campo de texto simple, como `public_name`, con un único producto.
- Probar un campo HTML, como `warranty`, con un único producto que contenga
  etiquetas HTML.
- Comprobar que el proveedor utilizado en el log es `deepl`.
- Comprobar que el texto se traduce y que las etiquetas HTML se conservan.
- Verificar el consumo y el límite de caracteres mediante el endpoint de uso
  de DeepL antes de realizar traducciones masivas.

## Implementación técnica

Los campos de tipo `html` se envían a DeepL con:

```json
{
  "tag_handling": "html",
  "tag_handling_version": "v2"
}
```

De esta forma DeepL procesa el texto visible sin eliminar la estructura HTML
del campo traducido.

## Recomendación operativa

Realizar primero pruebas unitarias sobre pocos registros y ampliar el volumen
progresivamente después de verificar el resultado de `public_name` y
`warranty`. No ejecutar una traducción masiva hasta confirmar que la clave,
el endpoint y la cuota disponibles son correctos.

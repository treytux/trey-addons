# Pruebas HTTP Nexmart en entornos multiwebsite

## Problema y objetivo

La fixture de pruebas debe publicar el producto y configurar la clave API
sobre el sitio que atenderá las peticiones HTTP del test. Usar siempre el
sitio predeterminado puede provocar respuestas 404 en una base multiwebsite.

## Alcance e implementación

- Resolver el sitio mediante el host y puerto de `HttpCase.base_url()`.
- Crear el producto publicado y configurar la clave Nexmart en ese sitio.
- Exigir HTTP 200 en los casos positivos y negativos; un 404 no demuestra
  que el iframe se oculte correctamente.
- Mantener las condiciones funcionales de clave API, EAN y activación.

## Criterios de aceptación

- Ejecutar las seis pruebas de Nexmart sin fallos ni errores.
- Verificar presencia del iframe con todos los requisitos satisfechos.
- Verificar su ausencia sin clave, sin EAN o con la integración desactivada.
- Validar el gancho compartido según `20260911_shared_iframe_resizer.md`.

## Validación

`oo exec adarra16_260903 --instance adarra16 -u website_sale_nexmart
--test-enable --test-tags /website_sale_nexmart --stop-after-init`

## Riesgos

Las pruebas HTTP verifican el HTML servido; el contenido del proveedor
externo y su redimensionado visual requieren comprobación en navegador.

# Ajuste automático de altura del documento Nexmart

## Problema y objetivo

La inicialización inline puede ejecutarse antes de la carga diferida de los
assets de Odoo 16. El iframe conserva entonces una altura insuficiente y
muestra desplazamiento vertical interno.

## Alcance final

- Mostrar el documento completo y ajustar su altura cuando cambie.
- Mantener URL, clave API, EAN y condiciones de visibilidad existentes.
- Marcar el iframe mediante `js_wir_iframe` y delegar la inicialización al
  módulo compartido `website_iframe_resizer` después de DOM listo.
- Eliminar la plantilla de inicialización inline y las bibliotecas duplicadas.
- Conservar `checkOrigin: false` por compatibilidad con Nexmart y desactivar
  el desplazamiento interno mediante `scrolling: false`.

El diseño definitivo, las versiones para MR y las validaciones se documentan
en `20260911_shared_iframe_resizer.md`.

## Criterios de aceptación

- Actualización del módulo sin errores y seis pruebas Odoo correctas.
- Iframe presente con clave API, EAN y Nexmart activado; ausente si falta
  cualquiera de las condiciones.
- Un único propietario de la biblioteca y de la inicialización.
- Documento externo visible completo en escritorio y móvil.

## Riesgos

El ajuste depende del protocolo del proveedor. La prueba HTTP confirma el
marcado, pero la última condición requiere verificación visual externa.

# Servicio compartido de redimensionado de iframes

## Problema y objetivo
El bundle real carga dos copias de iframeResizer; ambas escuchan mensajes,
pero solo una inicializa sus callbacks. Se produce messageCallback is not a
function. Centralizar la biblioteca y todas las llamadas a iFrameResize en
website_iframe_resizer, dependencia de Nexmart y Raíz Ferretera.

## Diseño y alcance aprobado
- Nuevo módulo website_iframe_resizer con biblioteca vendorizada única y
  servicio frontend Odoo que espera DOM listo.
- Contrato genérico: iframes con clase js_wir_iframe o contenidos dentro de
  un contenedor js_wir_container. Los consumidores solo marcan su HTML.
- Descubrir también iframes añadidos de forma asíncrona mediante
  MutationObserver; inicializar cada elemento una vez.
- Opciones comunes: checkOrigin false (compatibilidad Nexmart), scrolling
  false, enablePublicMethods true (Raíz), callbacks válidos por defecto.
- Conservar la versión de la librería y su protocolo; sin nuevas dependencias
  externas. Las dos integraciones eliminan librerías duplicadas y llamadas.
- El loader externo de Raíz también llama a iFrameResize (verificado en su
  código servido). Sustituirlo por iframe QWeb equivalente con misma URL
  /ean/apikey/barcode, identificador rfc_apikey_barcode y estilos. Conservar
  XML ID portal.frontend_layout como herencia sin scripts para actualizar
  bases existentes y eliminar el loader y la llamada inline anteriores.
- README e index.html del módulo nuevo en español, icono y cabeceras Trey.
- Preservar reglas funcionales. No nuevas cadenas UI. Las versiones se
  incrementan en la preparación del MR del 15/09/2026.

## Fases y propiedad
1. Spec previa en los tres módulos.
2. Agente frontend: nuevo módulo compartido y pruebas JS de regresión.
3. Agente integraciones: manifiestos, plantillas y eliminación de duplicados
   en los dos consumidores.
4. Revisor QA: auditoría independiente y ejecución de pruebas.

## Validación
- Reproducir TypeError con dos copias antiguas y mensaje de iframe.
- Probar biblioteca única, mensajes, resize, dos iframes, inserción tardía,
  reinicialización y exclusión de iframes ajenos usando Node sin dependencias.
- Validar sintaxis JS, XML y manifiestos, assets y dependencias.
- Actualizar en la instancia adarra16 usando la base confirmada y revisar
  bundle regenerado: una sola biblioteca y punto de llamada compartido.
- Comprobación visual externa sujeta a disponibilidad de los proveedores.

## Implementación del módulo compartido
- Biblioteca fuente original copiada sin cambios desde Nexmart.
- Servicio Odoo con selección genérica y selección temporal por lote; WeakSet
  evita añadir más de un listener load a cada elemento iframe.
- MutationObserver observa inserciones en el documento; las modificaciones
  de estilo durante el redimensionado no disparan nuevas inicializaciones.
- Los callbacks comunes se configuran también con el DOM inicialmente vacío.
- Pruebas ejecutadas: `node tests/iframe_resizer.test.cjs`, 4 casos correctos,
  incluyendo la reproducción del TypeError al cargar dos copias originales.
- Sintaxis del servicio validada con `node --check`.

## Validación previa del 11/09/2026 en adarra16_260903

- Instalación del módulo compartido y actualización de ambos consumidores
  completadas en la instancia adarra16.
- Node: 4 pruebas correctas, incluida reproducción del fallo original.
- Odoo: 12 pruebas ejecutadas, 0 fallos y 0 errores tras ajustar el HttpCase
  de Raíz para seleccionar la web efectiva por host.
- Consulta de solo lectura: los tres módulos están instalados. Bundle
  /web/assets/2697759-ec9db54/2/web.assets_frontend_lazy.min.js contiene
  una biblioteca compartida, una llamada común y cero copias antiguas.
- Auditoría QA independiente sin bloqueantes. Sin nuevas cadenas UI.
- Pendiente comprobación visual del contenido real de los proveedores.

## Preparación del MR del 15/09/2026

- website_iframe_resizer: versión inicial 16.0.1.0.0.
- Nexmart y Raíz Ferretera: 16.0.1.0.0 → 16.0.1.1.0, con actualización
  necesaria para aplicar las vistas y la dependencia compartida.
- Auditoría independiente: sin bloqueantes; sintaxis Python/XML/JS correcta
  y cuatro pruebas Node ejecutadas correctamente.
- La validación visual del contenido real de ambos proveedores queda pendiente.
- Ejecución Odoo del 15/09/2026: 12 pruebas, 8 fallos y 0 errores;
  cuatro pruebas de modelo correctas. Los ocho casos HTTP reciben 403
  porque `website_sale.product` lee `product.attachment_template_ids`
  sin permisos de lectura en `ir.attachment` para el usuario público.
  La validación integrada queda bloqueada por esa sección de adjuntos.
- Flake8 de manifiestos y pruebas modificadas: correcto.
- Traducciones regeneradas con Odoo Control en los tres módulos.
  Catálogos españoles completos y validados con TranslationFileReader;
  euskera preservado. El módulo compartido no aporta términos traducibles.

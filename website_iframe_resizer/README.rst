Website Iframe Resizer
======================

Centraliza la biblioteca iframeResizer y su inicialización para las
integraciones web de Nexmart y Raíz Ferretera, evitando listeners duplicados.

Uso
---

Los módulos consumidores deben depender de ``website_iframe_resizer`` y
marcar cada iframe con ``js_wir_iframe`` o su contenedor con
``js_wir_container``. No deben incluir otra copia de la biblioteca ni
llamar a ``iFrameResize``. Se detectan también las inserciones posteriores
al DOM inicial y cada iframe se inicializa una sola vez.

Se conserva la biblioteca existente sin modificar su protocolo. Sus opciones
son compartidas: sin comprobación de origen, sin scroll y con métodos
públicos habilitados, para mantener las integraciones actuales.

Validación
----------

Desde el directorio del módulo::

    node tests/iframe_resizer.test.cjs

Después de instalar el módulo y actualizar los consumidores, comprobar los
productos de ambos proveedores y el contenido insertado de forma asíncrona.

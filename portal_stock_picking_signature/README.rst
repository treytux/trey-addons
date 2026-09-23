==============================
Portal stock picking signature
==============================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

- Añade un botón en el albarán y en el asistente de la sesión de venta para
  solicitar la firma del cliente desde el portal.
- El botón del albarán solo se muestra cuando el albarán está en estado
  Hecho y tiene una venta asociada, evitando iniciar una firma que el
  portal nunca podría completar.
- Muestra la ficha del albarán pendiente de firma en el portal, con los
  datos del cliente, la fecha prevista, el estado, la política de entrega
  y el detalle de productos.
- Permite firmar el albarán con el dedo o el ratón desde el portal, o
  cancelar la solicitud de firma.
- Como alternativa a la firma, permite adjuntar desde el portal una foto del
  albarán en papel sellado, que se sube a resolución completa.
- Publica la foto del albarán sellado en una URL sin token
  (``/picking/<id>/delivery_proof``): al abrirla sin sesión, Odoo redirige al
  inicio de sesión y solo un usuario interno con permiso de lectura sobre el
  albarán puede verla.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:

==================================
Sale order partner default carrier
==================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

    * Se añade el campo default_carrier_id en el modelo res.partner.
    * El campo default_carrier_id se añade en la vista en la pestaña de Ventas/Compras.
    * También se añade en la vista para crear/editar las direcciones de entrega.
    * El campo partner_shipping_id se establece el valor del campo default_carrier_id del partner_shipping_id.
    * Si no tiene ningún valor, se busca en parent_id.shipping_partner_id.

**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:

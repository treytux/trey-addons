.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================
Website Sale Product Icon
=========================

Muestra los iconos de producto (``product.template.icon`` / ``icon_ids``) en la
ficha de producto de la tienda online, justo debajo de la descripción de venta.

Módulo puente entre ``product_icon`` y ``website_sale``: no añade modelos ni
campos, solo hereda la plantilla ``website_sale.product`` para pintar los
iconos.

Configuración
~~~~~~~~~~~~~

 - Crear los iconos en Ventas > Configuración > Iconos de producto
   (``product.icon``), con nombre e imagen.
 - Asignar los iconos al producto en la pestaña de iconos de la ficha de
   producto.
 - Publicar el producto en la web.

Uso
~~~

Al abrir ``/shop/<producto>`` los iconos aparecen bajo la descripción de venta,
con el nombre del icono como ``title`` y ``alt``.

Las clases CSS ``o_wspi_icons``, ``o_wspi_icon`` y ``o_wspi_icon_image`` se
dejan sin estilo para que cada tema las personalice.

Créditos
~~~~~~~~

Desarrollado por Trey.

Licencia
~~~~~~~~

AGPL-3.0

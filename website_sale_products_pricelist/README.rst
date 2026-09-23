.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Website Sale Products Pricelist
===============================

Este módulo permite mostrar la tarifa de precios por cantidad en la ficha de 
producto dentro del sitio web de Odoo. Los usuarios pueden consultar una tabla 
con los precios aplicables según la cantidad seleccionada, facilitando la 
comparación y selección de variantes.

Funcionalidad
-------------

- Muestra una tabla de precios por cantidad en la página de producto y en la 
lista de productos del sitio web.
- Permite visualizar los precios de cada variante del producto según la tarifa 
configurada.
- Los descuentos y reglas de precios se aplican automáticamente según la 
cantidad seleccionada y la variante elegida.
- Compatible con múltiples tarifas y reglas de descuento.

Configuración
-------------

1. Accede a **Ventas > Tarifas** en el backend de Odoo.
2. Selecciona o crea una tarifa nueva.
3. Añade reglas de precio para variantes, especificando:
   - Variante específica.
   - Cantidad mínima para aplicar el precio.
   - Descuento o precio fijo.
4. Guarda la tarifa y asígnala a los clientes o al sitio web según corresponda.

Al configurar las reglas de precio sobre las variantes, el módulo mostrará 
automáticamente la tabla de precios en el sitio web, permitiendo a los usuarios 
ver los descuentos aplicados por cantidad y variante.

Requisitos
----------

- Odoo versión compatible.
- Módulo `website_sale` instalado.


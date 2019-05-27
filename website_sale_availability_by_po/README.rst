.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================
Availability by Purchase Orders
===============================

Muestra la disponibilidad de un artículo en la tienda online teniendo en
cuenta los pedidos de compra.

-----
Campos utilizados para el cálculo de los estados de stock
-----

- inventory_availability: Política a seguir para la venta online
- available_threshold: Cantidad mínima de stock (si inventory_availability = 'treshold')
- qty_available: Cantidad real disponible
- incoming_qty: Cantidad pendiente de entrada
- outgoing_qty: Cantidad pendiente de salida
- virtual_available: Cantidad virtual disponible (qty_available + incoming_qty - outgoing_qty)

-----
Estados en ficha de producto (para variantes de producto)
-----

- 'available' / 'Disponible': qty_available – available_threshold – outgoing_qty > 0
- 'available_threshold' / 'Pocas unidades': qty_available – outgoing_qty > 0
- 'coming_soon' / 'Próxima reposición': virtual_available > 0
- 'not_available' / 'No disponible': qty_available = 0 y virtual_available = 0

-----
Estados en listado de productos (para plantillas de producto)
-----

- 'available' / 'Disponible': Todas las variantes en estado 'available'
- 'available_threshold' / 'Pocas unidades': Alguna variante en estado 'threshold_available'
- 'coming_soon' / 'Próxima reposición': Alguna variante en estado 'coming_soon'
- 'not_available' / 'No disponible': Todas las variantes en estado 'not_available'


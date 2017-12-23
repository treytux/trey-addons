# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Product Public Name',
    'version': '8.0.0.1',
    'category': 'Website',
    'summary': 'Add Public Name to Product Template to show in Ecommerce.',
    'description': """
Se reemplazan los valores del campo product.name por product.public_name
en listados de producto, ficha de producto.

TODO: Modificar líneas del carrito.

Se ha optado por la solución menos problemática para la herencia de plantillas.

Se ofrece otra como alternativa en 'views/website_sale.xml' para utilizar en
módulos de personalización ya que permite mostrar el nombre original si no se
rellena el campo 'public_name' sin necesidad de la utilización de campos
calculados.

Aquellas vistas cuya visualización sea personalizable (como
'recommended_products' del módulo 'website_sale') tendrán que reemplazarse
manualmente desde un módulo de personalización.
    """,
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'depends': [
        'website_sale',
    ],
    'data': [
        'views/product_view.xml',
        'views/website_sale.xml'
    ],
    'demo': [
    ],
    'test': [
    ],
    'images': [
    ],
    'installable': True,
    'application': False,
}

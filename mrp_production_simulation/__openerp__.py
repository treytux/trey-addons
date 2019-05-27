# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
##############################################################################
{
    'name': 'Mrp production simulation',
    'summary': 'Mrp production simulation',
    'description': '''
Wizard to simulate a manufacturing order, showing in a window the products
available in the warehouse and knowing how much can be manufactured at present.

For this it will show:

- The quantity that it wants to manufacture.

- The real available quantity (real stock) of the components.

- The virtual available quantity (virtual stock) of the components.

- The pending quantity of components to be buyed.

- The pending quantity of components to be manufactured.

And it will be calculated:

- The number of units considering the real stock that can be currently
manufactured.

- The number of units considering the virtual stock that can be currently
manufactured.

The lines are marked with different colors according to what they indicate:

     - Black: lines with available quantity.

     - Blue: lines with pending amount to buy.

     - Violet: lines with pending amount to produce.

In addition, if a product that is manufactured has stock available, the lower
level lines that compose it are not shown. If on the contrary, the product
that is manufactured does not have available stock, the lower-level lines that
make it up are shown, since it is important to know whether or not they have
stock for manufacturing.

Also it show the buys summary needed to produce the main product.
''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Manufacturing',
    'version': '8.0.0.1.0',
    'depends': [
        'base',
        'mrp',
        'mrp_production_escandallo',
        'purchase',
    ],
    'data': [
        'wizards/mrp_simulation_view.xml',
        'views/mrp_bom_view.xml',
    ],
    'installable': True,
}

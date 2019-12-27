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
    'name': 'Sale order last prices sale and pos',
    'summary': 'Sale order last prices sale and pos',
    'description': '''
Hide separatly buttons to unify in a single button the functionality of
displaying the latest prices, to show sales order lines and point of sale lines
in the same view.''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Sales',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
        'sale',
        'sale_order_last_prices',
        'point_of_sale',
    ],
    'data': [
        'wizards/last_prices_from_sale_order_line_view.xml',
        'views/sale_order_line_view.xml',
        'views/pos_order_line_view.xml',
    ],
    'installable': True,
}

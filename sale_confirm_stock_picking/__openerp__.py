# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2020-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Sale Confirm Stock Picking',
    'category': 'Sales',
    'summary': 'Allow to confirm stock picking from sale.',
    'version': '8.0.1.0.0',
    'description': '''
        This module allows user to confirm stock pickikng created from sale
        order.
    ''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'stock',
    ],
    'data': [
        'data/res_groups.xml',
        'wizards/sale_confirm_picking_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
}

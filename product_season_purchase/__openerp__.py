# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey (www.trey.es)
#    Copyright (C) 2016-Today Trey (www.trey.es) <www.trey.es>
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
    'name': 'Product Season Purchase Report group',
    'category': 'Product',
    'summary': '',
    'version': '8.0.0.1',
    'description': 'Apply a filter to view products season in purchase report',
    'author': 'Trey (www.trey.es)',
    'depends': ['product_season', 'purchase'],
    'data': [
        'views/purchase_report_view.xml',
        'views/purchase_order_view.xml'
    ],
    'installable': True,
}

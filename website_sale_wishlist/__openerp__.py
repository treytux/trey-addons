# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2015-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Products Wishlist',
    'category': 'website',
    'summary': 'Allow ecommerce users to save their favorite products '
               'in a wish list',
    'version': '8.0.0.1',
    'description': """
    Allow ecommerce users to save their favorite products in a wish list
    """,
    'author': 'Trey (www.trey.es)',
    'depends': [
        'website',
        'website_sale',
    ],
    'data': [
        'views/views.xml',
        # 'security/ir.model.access.csv',
        # 'security/security.xml',
        # 'data/group.xml',

        # 'views/categories.xml',
        # 'views/snippets.xml',

        # 'views/pos_index.xml',
        # 'reports/report_paperformat.xml',
        # 'reports/report_layout.xml',
        # 'reports/report_invoice.xml',
        # 'reports/report_saleorder.xml',
        # 'reports/report_purchaseorder.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'qweb': [
    ],
    'js': [
    ],
    'css': [
    ],
    'installable': True,
}

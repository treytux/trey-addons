# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Product Hs Code',
    'summary': 'International HS Code enhancement for delivery',
    'description': """Add hs_code field to Product Template for enhancement""",
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'version': '8.0.1.0.0',
    'category': 'Stock',
    'depends': ['delivery'],
    'data': [
        'data/product_template_hscode_data.xml',
        'security/ir.model.access.csv',
        'views/product_template_hscode_view.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
}

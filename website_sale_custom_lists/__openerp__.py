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
    'name': 'Website sale custom lists',
    'category': 'Website',
    'summary': 'Website sale custom lists',
    'version': '8.0.0.1',
    'description':
        'Allows create custom lists and associate them with template '
        'products.',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_list.xml',
        'views/product.xml',
        'views/menu.xml',
        'wizards/assign_product_tmpl_to_list.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
}

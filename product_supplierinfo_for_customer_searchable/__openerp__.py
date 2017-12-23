# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2017-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Product supplierinfo for customer searchable',
    'category': 'customize',
    'summary': 'Allow search products by supplierinfo for customer',
    'version': '8.0.1.0.0',
    'description': '''
    This module depends on OCA product-attribute branch
    (https://github.com/OCA/product-attribute.git#8.0)
    ''',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'product_supplierinfo_for_customer',
    ],
    'data': [
        'views/product_product.xml',
        'views/product_template.xml',
        'views/product_supplierinfo.xml'
    ],
    'installable': True,
}

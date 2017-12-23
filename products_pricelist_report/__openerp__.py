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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
###############################################################################
{
    'name': 'Products Pricelist report',
    'summary': 'Allows to show products pricelist per quantity in product list'
               ' and product template on a table',
    'version': ' 8.0.0.1.0',
    'category': 'Product',
    'description': '''Allows to show products pricelist per quantity in
     product list and product template on a table ''',
    'author': 'Trey (www.trey.es)',
    'depends': ['product_season', 'print_formats_base', 'products_pricelist'],
    'data': [
        'report/report_saleorder.xml',
        'wizard/products_pricselist.xml',
        'views/sale_view.xml'
    ],
    'installable': True,
}

# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
{
    'name': 'Ecommerce Season by User',
    'summary': """
        Show active season products depending on user""",
    'description': """
        Show active season products depending on user""",
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Product',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
        'sale',
        'product_season',
        'website_sale',
    ],
    'data': [
        'security/security.xml',
        'templates/website_sale.xml',
        'views/product_public_category_view.xml',
        'views/product_season_view.xml'
    ],
    'installable': True,
}

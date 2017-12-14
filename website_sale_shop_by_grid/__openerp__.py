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
    'name': 'Shop by grid',
    'category': 'customize',
    'summary': 'Add to cart several products at once from a grid',
    'version': '8.0.0.1',
    'description': '''Add to cart several products at once from a grid''',
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'depends': [
        'product',
        'website_sale',
        'website_sale_attribute_public_name',
    ],
    'data': [
        'templates/website.xml',
        'templates/website_sale.xml',
        'views/res_config_view.xml',
        'templates/website_sale_shop_by_grid.xml',
    ],
    'installable': True,
}

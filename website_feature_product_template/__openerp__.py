# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones (www.trey.es).
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
    'name': 'website_feature_product_template',
    'category': 'website',
    'summary': 'Este modulo anade caracteristicas a la plantilla de productos '
               'y permite busquedas y agrupaciones desde el sitio web.',
    'version': '8.0.0.1',
    'description': """
Este modulo anade caracteristicas a la plantilla de productos y permite
busquedas y agrupaciones desde el sitio web.
    """,
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'depends': [
        'product',
        'website_sale'
    ],
    'data': [
        # @ TODO add security
        'views/feature.xml',
        'views/product.xml',
        'views/menu.xml'
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

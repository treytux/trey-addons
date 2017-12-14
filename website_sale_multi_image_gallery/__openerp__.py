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
    'name': 'Image gallery for eCommerce',
    'category': 'customize',
    'summary': 'Show the touch-enabled, responsive and customizable Bootstrap '
               'Image Gallery (based on blueimp Gallery) on product page',
    'version': '8.0.0.1',
    'description': """
    """,
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'depends': [
        'website_sale_multi_image',
    ],
    'data': [
        'templates/website.xml',
    ],
    'qweb': [
        'static/src/xml/website_sale_multi_image_gallery.xml',
    ],
    'installable': True,
}

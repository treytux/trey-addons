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
    'name': 'Smart Search',
    'summary': 'Smart Search on Website',
    'version': '8.0.1.0.0',
    'description': 'Smart Search on Website',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'website',
    'depends': [
        'product',
        'website',
        'website_sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'templates/website.xml',
        'views/menu.xml',
        'views/cache_search.xml',
        'views/product_template.xml',
        'views/suggestion_banner.xml',
        'views/website_config_settings.xml',
    ],
    'qweb': [
        'static/src/xml/website_sale_smart_search.xml',
    ],
    'installable': True,
}

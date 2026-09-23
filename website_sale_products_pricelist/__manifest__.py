###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2025-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Website Products Pricelist',
    'summary': 'Allows to show products pricelist per quantity in product list'
               ' and product template on a table',
    'category': 'Website',
    'version': '16.0.1.0.5',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'website_sale',
    ],
    'data': [
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sale_products_pricelist/static/src/js/'
            'website_sale_products_pricelist.js',
            'website_sale_products_pricelist/static/src/xml/'
            'website_sale_products_pricelist.xml',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
}

###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2023-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Vertical Ecommerce B2B',
    'category': 'Vertical',
    'summary': 'Addons dependencies for ecommerce B2B',
    'version': '16.0.1.2.0',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'vertical_website',
        'website_require_login',
        'website_sale',
        'website_sale_category_breadcrumb',
        'website_sale_hide_price',
    ],
    'data': [
        'views/website_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'application': True,
}

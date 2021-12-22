###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'version': '12.0.1.2.2',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'portal_base',
        'portal_hide_promotional_link',
        'vertical_website',
        'website_sale',
        'website_sale_description_backend',
        'website_sale_observations',
        'website_sale_option_fixed_text',
        'website_sale_products_per_page',
        'website_sale_reset_styles',
    ],
    'data': [
        'views/website_sale.xml',
    ],
    'application': True,
}

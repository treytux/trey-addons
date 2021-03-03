###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2020-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Google Shopping',
    'category': 'e-commerce',
    'summary': 'Generate products feed for Google Merchant Center',
    'version': '12.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'product_brand',
        'stock',
        'website_sale',
    ],
    'post_init_hook': 'post_init_hook',
    'data': [
        'security/ir.model.access.csv',
        'templates/website_sale_template.xml',
        'views/product_views.xml',
        'views/product_pricelist_views.xml',
        'views/res_company_views.xml',
        'views/website_views.xml',
        'views/google_product_category_views.xml',
    ],
}

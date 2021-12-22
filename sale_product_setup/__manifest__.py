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
    'name': 'Product setup',
    'summary': 'Product setup',
    'category': 'Sale',
    'version': '12.0.1.10.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'sale',
        'sale_management',
        'sales_team',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_setup_category_views.xml',
        'views/product_setup_group_views.xml',
        'views/product_setup_property_views.xml',
        'views/product_template_views.xml',
        'wizards/sale_product_setup.xml',
    ],
    'demo': [
        'demo/setup_demo.xml',
    ],

}

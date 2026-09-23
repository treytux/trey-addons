###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2026-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Account Analytic Group Product Category',
    'summary': 'Auto-assign analytic group from product category',
    'description': '''
Links product categories to analytic groups. When an analytic line
is created the group is automatically set from the product's category.
If the direct category has no group, parent categories are checked
recursively. The product is obtained from the analytic line itself,
or from the stock.move if the line has no product.
    ''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Accounting',
    'version': '16.0.1.0.1',
    'license': 'AGPL-3',
    'depends': [
        'account_analytic_group',
        'product',
        'stock',
    ],
    'data': [
        'views/product_category_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}

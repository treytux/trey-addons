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
    'name': 'Product purchase last price',
    'summary': 'Add last purchase price in product',
    'category': 'Purchases',
    'version': '12.0.1.5.2',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'purchase_discount',
        'sale_stock',
        'sale_report_from_stock_margin',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'reports/sale_report_from_stock_move.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/templates.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}

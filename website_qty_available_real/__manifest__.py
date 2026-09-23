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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http: //www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Website QTY Available Real',
    'summary': 'Allows filter products without stock in website sale',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Website',
    'version': '12.0.1.4.0',
    'depends': [
        'product_qty_available_real_filter',
        'sale_order_line_qty_available',
        'website_sale',
        'website_sale_custom_filters',
        'website_sale_stock_available_display',
    ],
    'data': [
        'views/sale_product_template.xml',
        'views/website_template.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}

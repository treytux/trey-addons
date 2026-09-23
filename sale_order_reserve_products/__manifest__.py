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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Sale order reserve products',
    'summary': 'Reserve products from sales order',
    'category': 'Stock',
    'version': '16.0.1.0.1',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'sale_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_views.xml',
        'wizards/sale_product_reserve.xml',
    ],
    'images': [
        'static/description/banner.png',
    ]
}

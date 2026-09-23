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
    'name': 'Industrial Stock OrderPoint',
    'summary': 'Stock OrderPoint Customization for Industry',
    'category': 'Vertical',
    'version': '12.0.1.4.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'purchase_stock',
        'stock',
        'stock_deposit',
        'stock_warehouse_orderpoint_stock_info',
        'stock_warehouse_orderpoint_stock_info_unreserved',
    ],
    'data': [
        'data/ir_cron_data.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_warehouse_orderpoint_views.xml',
        'wizards/stock_warehouse_orderpoint_operation.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}

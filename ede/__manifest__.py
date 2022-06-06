##############################################################################
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
##############################################################################
{
    'name': 'EDE',
    'version': '12.0.2.16.1',
    'summary': 'Ede Supplier Webservice Connector',
    'license': 'AGPL-3',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'customize',
    'depends': [
        'barcodes',
        'product_list_price_from_margin',
        'product_standard_price_from_supplierinfo',
        'purchase',
        'purchase_discount',
        'purchase_stock',
        'sale',
        'sale_management',
        'sale_stock',
        'stock_picking_send_by_mail',
    ],
    'data': [
        'data/ede_data.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_ede_log_views.xml',
        'views/account_invoice_ede_log_line_views.xml',
        'views/purchase_order_views.xml',
        'views/res_company_views.xml',
        'views/sale_order_line_views.xml',
        'views/sale_order_views.xml',
        'views/stock_location_route_views.xml',
        'wizards/purchase_order_check.xml',
        'wizards/simulator_purchase.xml',
        'wizards/simulator_sale.xml',
    ],
    'demo': [
        'data/ede_demo.xml',
    ],
    'external_dependencies': {
        'python': [
            'ftputil',
            'xmltodict',
            'zeep',
        ],
    },
}

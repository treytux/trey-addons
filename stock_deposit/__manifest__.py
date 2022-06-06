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
    'name': 'Stock deposit',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Stock',
    'version': '12.0.2.1.0',
    'depends': [
        'product',
        'purchase_stock',
        'sale',
        'stock',
        'stock_picking_invoice_link',
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/stock_warehouse_views.xml',
        'views/sale_order_views.xml',
        'wizards/create_deposit.xml',
        'wizards/stock_deposit.xml',
    ],
}

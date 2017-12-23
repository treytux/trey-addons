# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2016-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Sale wizard process',
    'summary': 'Sale wizard process',
    'category': 'Sales',
    'version': '8.0.0.1',
    'description': '''
Wizard to create a sales order with fields concerning the picking and
automatically process it to generate the picking and transfer it (if products
are stockable or consumable) and generate the invoice.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'depends': [
        'account',
        'account_payment_sale',
        'base',
        'delivery',
        'product_dimension',
        'product_uos_price_sale_order_line',
        'sale',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'views/account_invoice_view.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
}

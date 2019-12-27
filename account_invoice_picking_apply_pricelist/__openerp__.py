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
    'name': 'Apply pricelist when invoice a picking',
    'category': 'Picking',
    'summary': 'Apply the appropriate pricelist when invoice a picking.',
    'version': '8.0.1.0.0',
    'description': '''
Apply the appropriate pricelist when invoice a picking.
The order of priority for applying the pricelist is as follows:
    - The associated in sale/purchase order (if you have one and have a \
    pricelist assigned).
    - The associated partner (if have a pricelist assigned).
    - Otherwise, the pricelist assigned in the new field 'Pricelist'.
''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'sale_stock',
        'stock_account',
        'stock_picking_invoice_link',
    ],
    'data': [
        'views/stock_view.xml',
    ],
    'installable': True,
}

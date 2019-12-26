# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Purchase order repair',
    'summary': 'Purchase order repair',
    'description': '''
This module creates two new types of operation: shipment repairs and reception
repairs. The reception repair type is marked by default the option 'Create
automatic return picking' to automatically create the return picking.

When a purchase order is created to ship products to be repaired to a supplier,
in the field 'Deliver to' you must select the new type of operation 'Reception
of repairs'. When the purchase order is confirmed, two stock pickings will be
generated:

    - One output (shipment) in 'Ready to transfer' state to send the products
    to repair to the supplier. The invoice control is fixed to 'Not
    Applicable' because the supplier is not going to invoice anything.

    - One entry (reception) in 'Waiting another operation' state so that, once
    the shipping stock picking has been transferred to the supplier, it
    automatically goes to the 'Ready to transfer' state and is received when
    the supplier has repaired it.
''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Purchases',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
        'purchase',
        'stock',
    ],
    'data': [
        'data/stock_picking_operation_repair.xml',
        'views/stock_picking_operation.xml',
    ],
    'installable': True,
}

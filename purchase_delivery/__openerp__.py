# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2015-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Purchase delivery',
    'summary': 'Purchase delivery.',
    'category': 'Purchase',
    'version': '8.0.0.1',
    'description': """
Add the information 'Shipping Method' field the purchase order and the field
'Carrier' the shipping in.
When generating the shipping in from this purchase order, the value of field
'Shipping Method' copies to 'Carrier'.
    """,
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'depends': [
        'base',
        'delivery',
        'purchase',
        'stock',
    ],
    'data': [
        'views/purchase.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
}

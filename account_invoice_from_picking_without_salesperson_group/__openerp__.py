# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Account invoice from picking without salesperson group',
    'summary': 'Account invoice from picking without salesperson group',
    'description': '''
When invoicing several stock pickings of the same partner with different
salesperson in the order marking the option "Group by partner" the system by
default creates a different invoice for each salesperson.

This module modifies this operation and does not have in consideration the
order's salesperson, so a single invoice is created that is assigned to
the salesperson of the first found order.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Invoicing & Payments',
    'version': '8.0.0.1.0',
    'depends': ['sale', 'sale_stock', 'stock_account'],
    'installable': True,
}

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
    'name': 'Account analytic assign quantity max',
    'category': 'Account',
    'summary': 'Add new group in account.move tree',
    'version': '8.0.0.1',
    'description': '''
Add the 'Contract hours' field to the product template and 'Contract' to the
invoice. When a invoice that has a contract partner is validated, it is
add the numbers of hours products lines recurring invoice that contract is
added the value of the field 'Total Worked Time' and result is assigned to the
field 'Units pre-paid service' of the contract.''',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'account',
        'account_analytic_analysis',
        'product',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/product_view.xml',
    ],
    'installable': True,
}

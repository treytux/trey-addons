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
    'name': 'Sale credit limit',
    'summary': 'Sale credit limit',
    'category': 'Sales',
    'version': '8.0.0.1',
    'description': '''
When a sale order is confirmed, it is checked whether the customer has credit
limit. If so, the sum of the amounts of unpaid invoices with confirmed sales
orders is calculated. If this sum is greater than the credit limit and the user
does not belong to the group 'Allow sell credit limit' is not allowed to
confirm the order.''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'depends': [
        'account',
        'base',
        'hr_timesheet_invoice',
        'project_account_analytic_line_partner',
        'sale',
        'stock_account_extend',
    ],
    'data': [
        'security/security.xml',
        'views/res_partner_view.xml',
        'views/account_analytic_line_view.xml',
        'wizards/compute_credit_limit.xml'
    ],
    'installable': True,
}

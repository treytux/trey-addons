# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2017-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Account subvention',
    'summary': 'Account subvention',
    'description': '''
        Add a new model to manage subventions.
        If a subvencion and a percentage is added to the customer, when an
        invoice is generated, these fields will be filled automatically in the
        lines. Once an invoice with a subvention is validated, the account move
        line will be divided so that one of them will have the percentage that
        the subvencion must pay and it will be subtracted from the total amount
        to be paid by the customer.
        From the account move lines of the subventions view you can reconcile
        the account move lines automatically from a button.
        In addition, there is a cron to perform the reconciliation of all the
        account move lines associated with any subvencion automatically.

        NOTE:
        In order for the account move lines to be reconciled, the associated
        journals must have the 'Default Debit Account' and 'Default Credit
        Account' fields filled out.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Accounting & Finance',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
        'account',
        'account_payment',
        'print_formats_base',
        'report',
    ],
    'data': [
        'data/data.xml',
        'report/report_subvention.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_line_view.xml',
        'views/account_invoice_view.xml',
        'views/account_move_line_view.xml',
        'views/account_move_view.xml',
        'views/account_subvention_view.xml',
        'views/menu_view.xml',
        'views/product_template_view.xml',
        'views/res_partner_view.xml',
        'wizard/print_options_account_subvention.xml',
        'wizard/wizard_change_subvention.xml',
    ],
    'installable': True,
}

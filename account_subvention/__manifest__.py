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
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Accounting & Finance',
    'version': '12.0.1.2.0',
    'depends': [
        'account_payment',
        'account_analytic_parent',
    ],
    'data': [
        'data/data.xml',
        'reports/report_subvention.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_line_view.xml',
        'views/account_invoice_view.xml',
        'views/account_move_line_view.xml',
        'views/account_move_view.xml',
        'views/account_subvention_view.xml',
        'views/menu_view.xml',
        'views/product_template_view.xml',
        'views/res_partner_view.xml',
        'wizards/print_options_account_subvention.xml',
        'wizards/wizard_change_subvention.xml',
    ],
    'installable': True,
}

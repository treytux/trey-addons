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
    'name': 'Account partner ledger report',
    'summary': 'Account partner ledger report',
    'description': '''
        Changes the report that is printed from the partner 'Partner Ledger'
        wizard to print the report that is printed from Accounting/
        Generic Reports/Partners/General Ledger menuitem.
    ''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Account',
    'version': '8.0.1.0.0',
    'depends': [
        'account',
        'account_financial_report_webkit_xls'
    ],
    'data': [
        'views/account_partner_ledger_view.xml',
    ],
    'installable': True,
}
